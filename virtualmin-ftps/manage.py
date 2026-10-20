#!/usr/bin/python3
"""Install in inert mode; explicit activation/freeze/rollback/removal."""
import argparse
import base64
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

BASE = Path(__file__).resolve().parent
MODULE_SOURCE = BASE / 'virtualmin-ftps' if (BASE / 'virtualmin-ftps/module.info').is_file() else BASE
spec = importlib.util.spec_from_file_location('ftps_engine', MODULE_SOURCE / 'engine.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
BEGIN = '# BEGIN virtualmin-ftps managed include\n'
END = '# END virtualmin-ftps managed include\n'
CONFIG = Path(engine.CONFIG)
STATE = Path('/var/lib/virtualmin-ftps')
UNIT_DIR = Path('/etc/systemd/system')


def webmin_root(value):
    if value:
        root = Path(value)
    else:
        data = Path('/etc/webmin/miniserv.conf').read_text()
        found = re.findall(r'^root=(.+)$', data, re.M)
        if len(found) != 1:
            raise ValueError('Cannot discover Webmin root; pass --webmin-root')
        root = Path(found[0])
    if not re.fullmatch(r'/[A-Za-z0-9_./-]+', str(root)):
        raise ValueError('Unsupported Webmin root path')
    engine.trusted(root, directory=True)
    return root


def verify_source(root):
    v = root / 'virtual-server'
    info = (v / 'module.info').read_text()
    if not re.search(r'^version=8\.3\.0\.gpl$', info, re.M):
        raise ValueError('Only the audited Virtualmin GPL 8.3.0 is supported')
    required = {
        'virtual_feature_api.pl': ['sub feature_setup', 'sub feature_modify',
                                   'sub feature_delete', 'sub feature_links'],
        'virtual-server-lib-funcs.pl': ['sub plugin_call', 'sub load_plugin_libraries',
                                      '"feature_setup", $dom', '"feature_delete", $dom',
                                      '"feature_modify", $d, $oldd',
                                      'sub get_all_domain_links', 'sub clear_links_cache',
                                      '"/$l->{\'mod\'}/$l->{\'page\'}"',
                                      '$d->{\'disabled\'} = join(",", @disabled)'],
        'save_newips.cgi': ['"feature_modify", $d, $oldd'],
        'feature-ssl.pl': ['sub renew_letsencrypt_cert', 'sub install_letsencrypt_cert'],
        'edit_domain.cgi': ['"feature_label", 1', '&ui_checkbox($f, 1'],
    }
    for file, needles in required.items():
        text = (v / file).read_text()
        for needle in needles:
            if needle not in text:
                raise ValueError(f'Hook compatibility check failed: {file}: {needle}')
    if not (root / 'proftpd/proftpd-lib.pl').is_file():
        raise ValueError('Webmin ProFTPD module missing')


def require_host(root):
    if root.resolve() != webmin_root(None).resolve():
        raise ValueError('Requested Webmin root is not the active miniserv root')
    data = Path('/etc/os-release').read_text()
    if not re.search(r'^ID=\"?debian\"?$', data, re.M) or not re.search(
            r'^VERSION_ID=\"?12\"?$', data, re.M):
        raise ValueError('This package targets Debian 12 only')
    verify_source(root)
    out = engine.run(['/usr/sbin/proftpd', '-v']).decode()
    if not re.search(r'Version 1\.3\.8(?:\D|$)', out):
        raise ValueError('ProFTPD 1.3.8 required')
    for binary in ('/usr/bin/openssl', '/usr/bin/perl', '/usr/bin/python3', '/usr/bin/systemctl'):
        if not os.access(binary, os.X_OK):
            raise ValueError(f'Missing dependency: {binary}')


def units(root):
    return {
        'virtualmin-ftps.service':
            '[Unit]\nDescription=Synchronize Virtualmin FTPS certificates\n'
            'After=proftpd.service\nConditionPathExists=/etc/webmin/virtualmin-ftps/engine.json\n'
            '[Service]\nType=oneshot\nUMask=0077\n'
            f'ExecStart=/usr/bin/perl {root}/virtualmin-ftps/collect.pl --apply\n'
            'TimeoutStartSec=300\n',
        'virtualmin-ftps.timer':
            '[Unit]\nDescription=Check Virtualmin FTPS renewal every minute\n'
            '[Timer]\nOnBootSec=90s\nOnUnitInactiveSec=60s\nAccuracySec=5s\n'
            'Unit=virtualmin-ftps.service\n[Install]\nWantedBy=timers.target\n',
    }


def get_config():
    return engine.configuration(str(CONFIG))


def install(root):
    require_host(root)
    target = root / 'virtualmin-ftps'
    if target.exists() or CONFIG.exists():
        raise ValueError('Already installed; refusing to overwrite module/configuration')
    state = STATE
    if state.exists() and any(state.iterdir()):
        raise ValueError('Existing FTPS state/backups found; refusing to overwrite')
    for name in units(root):
        if (UNIT_DIR / name).exists():
            raise ValueError(f'Service unit already exists: {name}')
    # Only new files/dirs; never modifies Virtualmin core or ProFTPD config.
    shutil.copytree(MODULE_SOURCE, target)
    shutil.copyfile(BASE / 'manage.py', target / 'manage.py')
    if (BASE / 'docs').is_dir():
        shutil.copytree(BASE / 'docs', target / 'docs')
    for name in ('README.md', 'LICENSE'):
        if (BASE / name).is_file():
            shutil.copyfile(BASE / name, target / name)
    target.chmod(0o755)
    for p in target.rglob('*'):
        if p.is_dir():
            p.chmod(0o755)
        elif p.is_file():
            p.chmod(0o755 if p.suffix in ('.cgi', '.pl', '.py') else 0o644)
    initialize(root, target)


def initialize(root, target):
    """Initialize an uploaded native module. Never edits daemon/core configuration."""
    engine.trusted(target, directory=True)
    if CONFIG.exists():
        existing = get_config()
        print(f'Already configured (mode={existing["mode"]}); configuration and state preserved.')
        return
    if STATE.exists() and any(STATE.iterdir()):
        raise ValueError('Existing FTPS state/backups found; refusing to overwrite')
    for name in units(root):
        if (UNIT_DIR / name).exists():
            raise ValueError(f'Service unit already exists: {name}')
    c = json.loads((target / 'engine.json.example').read_text())
    c['state_dir'] = str(STATE)
    c['mode'] = 'dry-run'
    state = STATE
    state.mkdir(mode=0o700, exist_ok=True)
    engine.trusted(state, directory=True)
    (state / 'certs').mkdir(mode=0o700, exist_ok=True)
    engine.atomic(state / 'state.json', engine.json_bytes({'domains': {}}))
    engine.atomic(state / 'installation.json', engine.json_bytes({'webmin_root': str(root)}))
    CONFIG.parent.mkdir(mode=0o700, exist_ok=True)
    engine.atomic(CONFIG, engine.json_bytes(c))
    print('Installed in dry-run mode. No ProFTPD changes, no reload, no timer. '
          'Register in Virtualmin > System Settings > Features and Plugins; default OFF.')


def setup(root):
    require_host(root)
    target = root / 'virtualmin-ftps'
    if MODULE_SOURCE.resolve() != target.resolve():
        raise ValueError('Run setup using manage.py inside the uploaded virtualmin-ftps module')
    if not (target / 'module.info').is_file():
        raise ValueError('Native module.info missing')
    initialize(root, target)


def marked(c):
    return BEGIN + 'Include ' + c['managed_file'] + '\n' + END


def set_default_host(name):
    name = engine.validate_default_domain(name)
    c = get_config()
    e = engine.Engine(c)
    with e.lock():
        state = e.read_state()
        if (c['mode'] != 'dry-run' or e.managed.exists() or
                state['domains'] or state.get('pending') or
                (e.root / 'journal.json').exists()):
            raise ValueError('Standardhost nur vor der ersten Aktivierung bei leerem Zustand setzen')
        c['default_domain'] = name
        engine.atomic(CONFIG, engine.json_bytes(c))
    print('FTPS-Standardhost: '+(name or 'keiner')+'. Noch keine aktive Änderung oder Reload.')


def activate(root):
    require_host(root)
    c = get_config()
    e = engine.Engine(c)
    with e.lock():
        if c['mode'] != 'dry-run' or e.read_state()['domains']:
            raise ValueError('Activation requires inert installation and empty managed state')
        main = Path(c['proftpd_conf'])
        engine.trusted(main)
        data = main.read_bytes()
        expanded, hosts, tls, ipv6, count = engine.scan(str(main), c['managed_file'])
        policy = engine.main_policy(expanded)
        if policy['issues']:
            raise ValueError(' '.join(policy['issues']))
        if BEGIN.encode() in data or count or e.managed.exists():
            raise ValueError('Existing managed Include/file found; refusing automatic adoption')
        # Check the shadow configuration before touching active configuration.
        with tempfile.TemporaryDirectory(prefix='ftps-activate-') as tmp:
            shadow = Path(tmp) / 'proftpd.conf'
            shadow.write_text(expanded + '\n' + engine.HEADER)
            engine.run([c['proftpd_bin'], '-t', '-c', str(shadow)])
        for name in units(root):
            if (UNIT_DIR / name).exists():
                raise ValueError('Existing service unit; refusing overwrite')
        engine.atomic(e.root / 'activation-main.backup', data, stat_mode(main))
        engine.atomic(e.managed, engine.HEADER.encode())
        oldmode = stat_mode(main)
        try:
            engine.atomic(main, data + b'\n' + marked(c).encode(), oldmode)
            engine.run([c['proftpd_bin'], '-t', '-c', str(main)])
            e.reload()
            for name, text in units(root).items():
                engine.atomic(UNIT_DIR / name, text.encode(), 0o644)
            engine.run(['/usr/bin/systemctl', 'daemon-reload'])
            c['mode'] = 'live'
            engine.atomic(CONFIG, engine.json_bytes(c))
            engine.run(['/usr/bin/systemctl', 'enable', '--now', 'virtualmin-ftps.timer'])
        except BaseException:
            c['mode'] = 'dry-run'
            engine.atomic(CONFIG, engine.json_bytes(c))
            # Freeze first, then restore only the configuration changed above.
            subprocess.run(['/usr/bin/systemctl', 'disable', '--now', 'virtualmin-ftps.timer'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=45)
            engine.atomic(main, data, oldmode)
            e.reload()
            e.managed.unlink(missing_ok=True)
            raise
    print('Live mode enabled, empty managed Include installed; existing vhosts unchanged. '
          'Renewal timer runs every minute. Enable individual domains via Virtualmin.')


def stat_mode(path):
    return Path(path).stat().st_mode & 0o777


def freeze():
    c = get_config()
    c['mode'] = 'dry-run'
    # Engine rechecks mode while holding its lock, so in-flight work is drained.
    e = engine.Engine(c)
    with e.lock():
        engine.atomic(CONFIG, engine.json_bytes(c))
    for unit in ('virtualmin-ftps.timer', 'virtualmin-ftps.service'):
        p = subprocess.run(['/usr/bin/systemctl', 'stop', unit], capture_output=True, timeout=310)
        if p.returncode and (UNIT_DIR / unit).exists():
            raise ValueError(f'Failed to stop {unit}')
    subprocess.run(['/usr/bin/systemctl', 'disable', 'virtualmin-ftps.timer'],
                   capture_output=True, timeout=45)
    return c


def deactivate():
    c = freeze()
    e = engine.Engine(c)
    with e.lock():
        e.recover()
        main = Path(c['proftpd_conf'])
        before = main.read_bytes()
        block = marked(c).encode()
        if before.count(block) != 1:
            raise ValueError('Exact managed Include marker missing/changed; refusing removal')
        after = before.replace(block, b'', 1)
        # The managed file stays intact until the config without its Include is live.
        try:
            engine.atomic(main, after, stat_mode(main))
            engine.run([c['proftpd_bin'], '-t', '-c', str(main)])
            e.reload()
        except BaseException:
            engine.atomic(main, before, stat_mode(main))
            e.reload()
            raise
    print('Managed Include removed, timer stopped, plugin frozen. '
          'Existing vhosts untouched; managed state/certificate backups retained. '
          'Domain feature flags remain in Virtualmin; do not re-enable the timer.')



LOGROTATE_FILE = Path('/etc/logrotate.d/virtualmin-ftps')
LOGROTATE_MARKER = '# Managed by virtualmin-ftps logrotate\n'


def logrotate_policy(c, ident=None):
    policy = c.get('logrotate', {})
    if not isinstance(policy, dict) or set(policy) - {'interval', 'rotate', 'maxsize', 'domains'}:
        raise ValueError('Unknown logrotate settings')
    overrides = policy.get('domains', {})
    if not isinstance(overrides, dict):
        raise ValueError('Logrotate domains must be an object keyed by domain ID')
    base = {k: v for k, v in policy.items() if k != 'domains'}
    for key, value in overrides.items():
        if (not isinstance(key, str) or not re.fullmatch(r'[0-9]{1,40}', key) or
                not isinstance(value, dict) or set(value) - {'interval', 'rotate', 'maxsize'}):
            raise ValueError('Invalid domain logrotate override')
        logrotate_policy({'logrotate': dict(base, **value)})
    policy = dict(base, **overrides.get(ident, {}))
    interval = policy.get('interval', 'weekly')
    count = policy.get('rotate', 52)
    size = policy.get('maxsize')
    if interval not in ('daily', 'weekly', 'monthly'):
        raise ValueError('Logrotate interval must be daily, weekly or monthly')
    if type(count) is not int or not 1 <= count <= 3660:
        raise ValueError('Logrotate rotate must be an integer between 1 and 3660')
    if size is not None and (not isinstance(size, str) or
                            not re.fullmatch(r'[1-9][0-9]{0,8}[kMG]', size)):
        raise ValueError('Logrotate maxsize must be null or a size such as 100M')
    return interval, count, size


def logrotate_config(c):
    interval, count, size = logrotate_policy(c)
    root = engine.effective_log_root(c)
    engine.validate_home(root)
    engine.trusted(Path(root).parent, directory=True, log_path=True)
    engine.trusted(root, directory=True, log_path=True)
    for child in Path(root).iterdir():
        if child.name[:1].isdigit():
            engine.trusted(child, directory=True, log_path=True)
    root = engine.resolve_log_source(root)
    def block(directory, values, duplicate_guard=False):
        interval, count, size = values
        return (f'"{directory}/ftp.log" "{directory}/xferlog" {{\n' +
                ('    ignoreduplicates\n' if duplicate_guard else '') +
                f'    {interval}\n    rotate {count}\n' +
                (f'    maxsize {size}\n' if size else '') +
                '    missingok\n    notifempty\n    compress\n    delaycompress\n'
                '    copytruncate\n    su root root\n}\n')
    data = LOGROTATE_MARKER
    # Specific hosts first. Their ignoreduplicates flag suppresses later wildcard
    # matches, while the wildcard automatically covers newly created domains.
    overrides = c.get('logrotate', {}).get('domains', {})
    for ident in sorted(overrides):
        data += block(f'{root}/{ident}', logrotate_policy(c, ident), True)
    data += block(f'{root}/[0-9]*', (interval, count, size))
    return data.encode()


def configure_logrotate(apply=False):
    c = get_config()
    e = engine.Engine(c)
    with e.lock():
        engine.trusted('/usr/sbin/logrotate')
        engine.trusted(LOGROTATE_FILE.parent, directory=True)
        data = logrotate_config(c)
        if LOGROTATE_FILE.exists() or LOGROTATE_FILE.is_symlink():
            engine.trusted(LOGROTATE_FILE)
            if not LOGROTATE_FILE.read_bytes().startswith(LOGROTATE_MARKER.encode()):
                raise ValueError('Foreign logrotate configuration; refusing overwrite')
        with tempfile.TemporaryDirectory(prefix='ftps-logrotate-') as tmp:
            candidate = Path(tmp) / 'virtualmin-ftps'
            candidate.write_bytes(data)
            candidate.chmod(0o600)
            engine.run(['/usr/sbin/logrotate', '--debug', str(candidate)])
        if apply:
            engine.atomic(LOGROTATE_FILE, data, 0o644)
        print(data.decode(), end='')
        print('Logrotate installed.' if apply else 'Logrotate preview checked; no rotation or installation.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['check', 'install', 'setup', 'activate', 'freeze', 'rollback', 'deactivate', 'set-default-host', 'check-logrotate', 'install-logrotate'])
    p.add_argument('--webmin-root')
    p.add_argument('--domain', default='')
    a = p.parse_args()
    if os.geteuid() != 0:
        p.error('Run as root')
    if a.action in ('check-logrotate', 'install-logrotate'):
        return configure_logrotate(apply=a.action == 'install-logrotate')
    if a.action == 'set-default-host':
        return set_default_host(a.domain)
    if a.action in ('check', 'install', 'setup', 'activate'):
        root = webmin_root(a.webmin_root)
        if a.action == 'install':
            return install(root)
        if a.action == 'setup':
            return setup(root)
        if a.action == 'activate':
            return activate(root)
        require_host(root)
        c = (get_config() if CONFIG.exists() else
             json.loads((MODULE_SOURCE / 'engine.json.example').read_text()))
        expanded, hosts, tls, ipv6, count = engine.scan(c['proftpd_conf'], c['managed_file'])
        print(json.dumps({'supported_sources': True, 'foreign_vhosts': hosts,
                          'main_tls_values': tls, 'main_ipv6_values': ipv6,
                          'main_policy': engine.main_policy(expanded),
                          'default_domain': c.get('default_domain', ''),
                          'managed_include_count': count, 'mode': c['mode'],
                          'active_configuration_changed': False}, indent=2, ensure_ascii=False))
    elif a.action == 'freeze':
        freeze()
        print('Frozen: no further domain/certificate changes will be applied.')
    elif a.action == 'rollback':
        c = freeze()
        print(json.dumps(engine.Engine(c).execute({'operation': 'rollback'}, apply=True)))
        print('Previous managed transaction restored. Timer remains stopped; mode dry-run.')
    elif a.action == 'deactivate':
        deactivate()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)
