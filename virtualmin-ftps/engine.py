#!/usr/bin/python3
"""Root-only ProFTPD transaction engine. No third party Python modules required."""
import argparse
import base64
import contextlib
import fcntl
import glob
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
import tempfile
import time
from log_views import prepare_views, unmount_view

HEADER = '# Managed by virtualmin-ftps 0.1.0; edit via Virtualmin only.\n'
MODULE = 'virtualmin-ftps'
CONFIG = '/etc/webmin/virtualmin-ftps/engine.json'


def now():
    return time.time()


def run(argv, data=None):
    p = subprocess.run(argv, input=data, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, timeout=45, env={
                           'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LANG': 'C'})
    if p.returncode:
        # Never echo OpenSSL input, private keys or arbitrary daemon output.
        raise ValueError(f'{Path(argv[0]).name}: command failed (exit {p.returncode}); '
                         'inspect daemon logs locally')
    return p.stdout


def atomic(path, data, mode=0o600):
    path = Path(path)
    if path.is_symlink():
        raise ValueError(f'Refusing symlink: {path}')
    fd, name = tempfile.mkstemp(prefix='.ftps-', dir=path.parent)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
        dfd = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def json_bytes(obj):
    if isinstance(obj, dict):
        obj = {k: v for k, v in obj.items() if not k.startswith('_')}
    return (json.dumps(obj, sort_keys=True, indent=2) + '\n').encode()


def load_json(path, default=None):
    return json.loads(Path(path).read_text()) if Path(path).exists() else default


def trusted(path, directory=False, log_path=False):
    p = Path(path)
    # Every ancestor must be controlled by root; prevents replaced symlink parents.
    for q in [p, *p.parents]:
        s = q.lstat()
        if (log_path and q == Path('/var/log') and stat.S_ISDIR(s.st_mode)
                and s.st_uid == 0 and not s.st_mode & 0o002):
            # Only standard system logging groups may control /var/log.
            # Customer accounts (including supplementary membership) fail closed.
            import grp, pwd
            group = grp.getgrgid(s.st_gid)
            if s.st_mode & 0o020:
                import errno
                try:
                    os.getxattr(q, 'system.posix_acl_access', follow_symlinks=False)
                except OSError as err:
                    if err.errno not in (errno.ENODATA, errno.ENOTSUP):
                        raise
                else:
                    raise ValueError('Review extended ACL on writable /var/log')
                members = [u for u in pwd.getpwall()
                           if u.pw_gid == s.st_gid or u.pw_name in group.gr_mem]
                if group.gr_name not in ('root', 'syslog', 'adm') or any(
                        u.pw_uid >= 1000 for u in members):
                    raise ValueError('Untrusted writable /var/log group')
            continue
        if stat.S_ISLNK(s.st_mode) or s.st_uid != 0 or s.st_mode & 0o022:
            raise ValueError(f'Not a root-controlled path: {q}')
    if directory and not p.is_dir():
        raise ValueError(f'Not a directory: {p}')


def configuration(path=CONFIG):
    trusted(path)
    c = load_json(path)
    for k in ('state_dir', 'managed_file', 'proftpd_conf', 'proftpd_bin'):
        if not re.fullmatch(r'/[A-Za-z0-9_./-]+', c[k]) or '..' in Path(c[k]).parts:
            raise ValueError(f'Unsafe configuration path: {k}')
    if c['mode'] not in ('dry-run', 'live'):
        raise ValueError('Unknown mode')
    ports = c['passive_ports']
    if (len(ports) != 2 or any(type(x) is not int for x in ports)
            or not 1024 <= ports[0] <= ports[1] <= 65535):
        raise ValueError('Invalid passive port range')
    validate_default_domain(c.get('default_domain', ''))
    # Fixed executable and arguments: never execute shell text from domains/config.
    c['_config_path'] = str(path)
    return c


def scan(conf, managed):
    """Conservatively expand Includes, even inside inactive conditionals.

    Unknown/malformed syntax fails closed. Returns expanded main text, foreign
    virtual hosts, global TLS observations and number of managed includes.
    """
    vhosts, main_tls, main_ipv6, includes = [], [], [], []
    stack, active_files = [], set()

    def walk(path):
        path = Path(path)
        if path == Path(managed):
            if stack:
                raise ValueError('Managed Include must be at top level')
            includes.append(str(path))
            return '@@VIRTUALMIN_FTPS@@\n'
        trusted(path)
        if path in active_files:
            raise ValueError('Recursive Include')
        active_files.add(path)
        out = []
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            if line.rstrip().endswith('\\'):
                raise ValueError(f'Continued lines unsupported: {path}:{lineno}')
            words = shlex.split(line, comments=True)
            if not words:
                out.append(line + '\n')
                continue
            if words[0].lower() == 'include':
                if len(words) != 2 or not words[1].startswith('/'):
                    raise ValueError('Only absolute single-path Includes supported')
                matches = sorted(glob.glob(words[1]))
                if words[1] == managed and not matches:
                    matches = [managed]
                for match in matches:
                    if Path(match).is_dir():
                        raise ValueError('Directory Includes unsupported; use a file glob')
                    out.append(walk(match))
                continue
            if words[0].lower() == '<virtualhost':
                if not words[-1].endswith('>') or any(x[0] == 'virtualhost' for x in stack):
                    raise ValueError('Malformed/nested VirtualHost')
                addresses = ' '.join(words[1:]).removesuffix('>').split()
                host = {'addresses': addresses, 'aliases': [], 'file': str(path),
                        'line': lineno, 'port': 21, 'named': False}
                vhosts.append(host)
                stack.append(('virtualhost', host))
            elif words[0].startswith('</'):
                tag = words[0][2:].rstrip('>').lower()
                if not stack or stack[-1][0] != tag:
                    raise ValueError(f'Unbalanced section: {path}:{lineno}')
                stack.pop()
            elif words[0].startswith('<'):
                stack.append((words[0][1:].rstrip('>').lower(), None))
            else:
                host = next((h for tag, h in reversed(stack) if tag == 'virtualhost'), None)
                key = words[0].lower()
                if host and key in ('serveralias', 'servername'):
                    host['aliases'].extend(x.lower() for x in words[1:])
                    if key == 'serveralias':
                        host['named'] = True
                if host and key == 'port' and len(words) == 2:
                    host['port'] = int(words[1])
                if not host and key == 'tlsengine':
                    main_tls.append(words[1].lower())
                if not host and key == 'useipv6':
                    main_ipv6.append(words[1].lower())
                if not host and key == 'tlsoptions' and any(
                        x.lower() in ('ignoresni', 'useimplicitssl') for x in words[1:]):
                    raise ValueError('Global IgnoreSNI/UseImplicitSSL conflicts with explicit named FTPS')
                if not host and key == 'servertype' and words[1].lower() != 'standalone':
                    raise ValueError('Only standalone ProFTPD is supported')
            out.append(line + '\n')
        active_files.remove(path)
        return ''.join(out)

    expanded = walk(conf)
    if stack:
        raise ValueError('Unclosed configuration section')
    if len(includes) > 1:
        raise ValueError('Managed Include occurs more than once')
    return expanded, vhosts, main_tls, main_ipv6, len(includes)


def normalize(d):
    allowed = {'id', 'dom', 'ip', 'ip6', 'group', 'cert', 'key', 'ca', 'suspended', 'home', 'user'}
    if set(d) - allowed:
        raise ValueError('Unknown domain descriptor fields')
    d = dict(d)
    if not re.fullmatch(r'[0-9]{1,40}', str(d['id'])):
        raise ValueError('Invalid Virtualmin domain ID')
    d['id'] = str(d['id'])
    dom = d['dom'].lower()
    if (len(dom) > 253 or '.' not in dom or
            any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', x)
                for x in dom.split('.'))):
        raise ValueError('Domain must be an ASCII/punycode FQDN')
    d['dom'] = dom
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.-]{0,63}', d['group']):
        raise ValueError('Unsupported Unix group name')
    addresses = []
    for key in ('ip', 'ip6'):
        if d.get(key):
            a = ipaddress.ip_address(d[key])
            if a.is_unspecified or a.is_multicast or (a.version == 4) != (key == 'ip'):
                raise ValueError('Invalid IP address')
            d[key] = str(a)
            addresses.append(str(a))
    if not addresses:
        raise ValueError('Domain has no IP address')
    for k in ('cert', 'key', 'ca'):
        if d.get(k) and (not re.fullmatch(r'/[A-Za-z0-9_./-]+', str(d[k]))):
            raise ValueError('Certificate paths must be absolute')
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.-]{0,63}', d.get('user', '')):
        raise ValueError('Missing or invalid Virtualmin domain user; run a full domain collection')
    d['home'] = validate_home(d.get('home'))
    d['suspended'] = bool(d.get('suspended'))
    return d


def validate_default_domain(name):
    if not isinstance(name, str) or (name and
            (len(name) > 253 or '.' not in name or name != name.lower() or
             any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', x)
                 for x in name.split('.')))):
        raise ValueError('Standardhost muss ein kleingeschriebener ASCII-/Punycode-Domainname sein')
    return name


def main_policy(expanded):
    """Read listener policy; TLS may remain OFF on a disabled main server."""
    stack, ports, defaults, foreign_defaults = [], [], [], []
    for line in expanded.splitlines():
        words = shlex.split(line, comments=True)
        if not words or words[0] == '@@VIRTUALMIN_FTPS@@':
            continue
        key = words[0].lower()
        if key.startswith('</'):
            if stack:
                stack.pop()
        elif key.startswith('<'):
            stack.append(key[1:].rstrip('>'))
        elif len(words) == 2:
            in_vhost = 'virtualhost' in stack
            if not in_vhost and key == 'port':
                ports.append(words[1])
            if key == 'defaultserver':
                (foreign_defaults if in_vhost else defaults).append(words[1].lower())
    issues = []
    if not ports or set(ports) != {'0'}:
        issues.append('Der Hauptserver ist noch aktiv. Für reinen VirtualHost-Betrieb muss dort Port 0 stehen.')
    if not defaults or set(defaults) != {'off'} or 'on' in foreign_defaults:
        issues.append('DefaultServer muss im Hauptserver off sein; kein fremder VirtualHost darf als DefaultServer on eingerichtet sein.')
    return {'port_values': ports, 'default_values': defaults,
            'foreign_default_values': foreign_defaults, 'issues': issues}


def pem_certs(data):
    certs = re.findall(rb'-----BEGIN CERTIFICATE-----\s+.*?-----END CERTIFICATE-----',
                       data, re.S)
    if not certs:
        raise ValueError('No PEM certificate')
    return [c + b'\n' for c in certs]


def certificate(d, directory=None):
    """Validate website material without writing certificate/key copies."""
    if not d.get('cert') or not d.get('key'):
        raise ValueError('Missing certificate or key path')
    material = {}
    for k in ('cert', 'key', 'ca'):
        path = d.get(k)
        if path:
            # Reads are bounded, key is never printed or placed in a command line.
            fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                os.close(fd)
                raise ValueError(f'Not a regular {k} file')
            with os.fdopen(fd, 'rb') as f:
                b = f.read(2 * 1024 * 1024 + 1)
            if len(b) > 2 * 1024 * 1024 or not b:
                raise ValueError(f'Empty/oversized {k} file for {d["dom"]}')
            material[k] = b
    certs = pem_certs(material['cert'])
    if material.get('ca'):
        for ca in pem_certs(material['ca']):
            if ca not in certs:
                certs.append(ca)
    # Refuse key/certificate swap during a non-atomic renewal. Next poll retries.
    key = material['key']
    kp = run(['/usr/bin/openssl', 'pkey', '-passin', 'pass:', '-pubout'], key)
    cp = run(['/usr/bin/openssl', 'x509', '-pubkey', '-noout'], certs[0])
    if kp != cp:
        raise ValueError(f'Certificate/key mismatch: {d["dom"]}')
    run(['/usr/bin/openssl', 'x509', '-checkend', '0', '-noout'], certs[0])
    # x509 -checkhost can report failure with success exit on some OpenSSL builds.
    hostname_result = run(['/usr/bin/openssl', 'x509', '-checkhost', d['dom'], '-noout'], certs[0])
    if b'does match certificate' not in hostname_result:
        raise ValueError(f'Certificate hostname mismatch: {d["dom"]}')
    public_description = run(['/usr/bin/openssl', 'pkey', '-pubin', '-text', '-noout'], kp)
    if b'ASN1 OID:' in public_description:
        kind = 'EC'
    elif b'Modulus:' in public_description:
        kind = 'RSA'
    else:
        raise ValueError('Only RSA and EC server certificates supported')
    # Read the website files directly for chain verification; no temporary PEMs.
    argv = ['/usr/bin/openssl', 'verify', '-purpose', 'sslserver',
            '-verify_hostname', d['dom'], '-untrusted', d.get('ca') or d['cert'], d['cert']]
    run(argv)
    # Detect replacement during verification. Direct references cannot provide
    # immutable generations; a later external replacement remains outside control.
    for name, data in material.items():
        with open(d[name], 'rb') as handle:
            if handle.read(2 * 1024 * 1024 + 1) != data:
                raise ValueError('Website certificate files changed during validation; retry')
    h = hashlib.sha256()
    for name in sorted(material):
        h.update(name.encode() + b'\0' + material[name])
    return kind, h.hexdigest(), bool(d.get('ca'))


def conflict(d, hosts):
    for h in hosts:
        if h['port'] != 21:
            continue
        names = h['aliases'] + h['addresses']
        if any(n.lower() == d['dom'] or ('*' in n and
               __import__('fnmatch').fnmatchcase(d['dom'], n.lower())) for n in names):
            return f'Foreign VirtualHost for {d["dom"]} in {h["file"]}:{h["line"]}'
        # A plain IP vhost on a target address could become an unexpected default.
        if not h['named'] and any(a in (d.get('ip'), d.get('ip6'), '*', '0.0.0.0', '::')
                                  for a in h['addresses']):
            return f'Foreign IP VirtualHost in {h["file"]}:{h["line"]}'
    return None



def validate_home(home):
    if (not isinstance(home, str) or not re.fullmatch(r'/[A-Za-z0-9_./-]+', home)
            or home == '/' or '..' in Path(home).parts
            or str(Path(home)) != home):
        raise ValueError('Domain home must be a canonical absolute ASCII path')
    return home


def log_paths(d):
    directory = d.get('log_dir') or (validate_home(d['home']) + '/logs')
    return (directory + '/ftp.log', directory + '/xferlog')


def effective_log_root(c):
    configured = c.get('log_root')
    state = Path(c.get('state_dir', '/var/lib/virtualmin-ftps'))
    previous_default = str(state.parent / (state.name + '-logs'))
    if not configured or configured in ('/var/log/virtualmin-ftps', previous_default):
        return '/var/log/virtualmin-ftps-logs'
    return configured


def protected_log_dir(ident, c):
    if not re.fullmatch(r'[0-9]{1,40}', str(ident)):
        raise ValueError('Invalid domain ID for log directory')
    root = effective_log_root(c)
    validate_home(root)
    return str(Path(root) / str(ident))


def source_log(path, d, gid):
    """Open a bounded historical snapshot without following any symlink."""
    import pwd
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in Path(path).parts[1:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=fd)
            os.close(fd)
            fd = child
            if os.fstat(fd).st_mode & 0o002:
                raise ValueError(f'World-writable historical log path: {path}')
        f = os.open(Path(path).name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                    dir_fd=fd)
    except FileNotFoundError:
        return None
    finally:
        os.close(fd)
    st = os.fstat(f)
    uid = pwd.getpwnam(d['user']).pw_uid if d.get('user') else None
    if (not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or
            st.st_uid not in (0, uid) or st.st_gid not in (0, gid) or
            st.st_mode & 0o002):
        os.close(f)
        raise ValueError(f'Unsafe historical FTPS log: {path}')
    return f


def prepare_logs(domains, c, apply=True, old_domains=None):
    """Root-controlled destination tree; previews only inspect existing files.

    Copy historical logs once, bounded by their size at open. Existing source
    files and existing destination contents are never removed or truncated.
    """
    import grp
    if not domains:
        return
    root = Path(effective_log_root(c))
    validate_home(str(root))
    trusted(root.parent, directory=True, log_path=True)
    if not root.exists() and apply:
        root.mkdir(mode=0o711)
        os.chown(root, 0, 0)
        root.chmod(0o711)
    if root.exists() or root.is_symlink():
        trusted(root, directory=True, log_path=True)
    for ident, d in domains.items():
        target = Path(protected_log_dir(ident, c))
        if d.get('log_dir') != str(target):
            raise ValueError('Protected logs require a full domain reconciliation')
        gid = grp.getgrnam(d['group']).gr_gid
        created_dir = False
        if not target.exists() and apply:
            target.mkdir(mode=0o750)
            os.chown(target, 0, gid)
            target.chmod(0o750)
            created_dir = True
        if target.exists() or target.is_symlink():
            trusted(target, directory=True, log_path=True)
            if target.stat().st_gid != gid:
                raise ValueError(f'Unexpected protected log directory group: {target}')
        old = (old_domains or {}).get(ident, d)
        for name in ('ftp.log', 'xferlog'):
            path = target / name
            if path.exists() or path.is_symlink():
                fd = os.open(path, (os.O_WRONLY if apply else os.O_RDONLY) |
                             os.O_NOFOLLOW | os.O_NONBLOCK)
                try:
                    st = os.fstat(fd)
                    if (not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or
                            st.st_uid != 0 or st.st_gid != gid or st.st_mode & 0o022):
                        raise ValueError(f'Unsafe protected FTPS log: {path}')
                finally:
                    os.close(fd)
                continue
            # Existing states can have legacy home paths or an older log root.
            previous = Path(log_paths(old)[0 if name == 'ftp.log' else 1])
            src = source_log(previous, d, gid) if previous != path else None
            try:
                if not apply:
                    continue
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                             os.O_NOFOLLOW | os.O_NONBLOCK, 0o640)
                try:
                    os.fchown(fd, 0, gid)
                    os.fchmod(fd, 0o640)
                    if src is not None:
                        remaining = os.fstat(src).st_size
                        while remaining:
                            data = os.read(src, min(remaining, 1024 * 1024))
                            if not data:
                                raise ValueError('Historical log changed during copy; retry')
                            remaining -= len(data)
                            view = memoryview(data)
                            while view:
                                n = os.write(fd, view)
                                if n <= 0:
                                    raise OSError('Unable to write historical log snapshot')
                                view = view[n:]
                    os.fsync(fd)
                except BaseException:
                    os.unlink(path)
                    raise
                finally:
                    os.close(fd)
            finally:
                if src is not None:
                    os.close(src)



def server_fqdn():
    """Resolve the local server identity each run; reject unsafe/short/IP names."""
    name = run(['/usr/bin/hostname', '--fqdn']).decode('ascii').strip().lower().rstrip('.')
    if (len(name) > 253 or '.' not in name or
            any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', label)
                for label in name.split('.'))):
        raise ValueError('Server hostname must be a valid ASCII/punycode FQDN')
    try:
        ipaddress.ip_address(name)
    except ValueError:
        return name
    raise ValueError('Server hostname must not be an IP address')


def render_state(state, c, legacy_login=False):
    # Old releases used domain identities. Stored identity preserves exact drift
    # checks even after the operating system hostname changes.
    return render(state['domains'], c, legacy_login=legacy_login,
                  legacy_ident='server_fqdn' not in state,
                  identity=state.get('server_fqdn'),
                  allow_overwrite=state.get('allow_overwrite', False),
                  allow_override=state.get('allow_override', False))


def render(domains, c, legacy_login=False, legacy_ident=False, identity=None,
           allow_overwrite=True, allow_override=True):
    default = validate_default_domain(c.get('default_domain', ''))
    identity = identity if identity is not None else (None if legacy_ident or not domains else server_fqdn())
    out = [HEADER]
    for ident in sorted(domains, key=lambda i: (domains[i]['dom'] != default, i)):
        d = domains[ident]
        ips = ' '.join(d[k] for k in ('ip', 'ip6') if d.get(k))
        direct = d.get('certificate_source') == 'website'
        root = Path(d['snapshot']) if not direct else None
        cert = d['cert'] if direct else str(root / 'cert.pem')
        key = d['key'] if direct else str(root / 'key.pem')
        chain = d.get('ca') if direct else str(root / 'ca.pem')
        prefix = 'TLSEC' if d['kind'] == 'EC' else 'TLSRSA'
        out += [f'# Domain ID {ident}\n<VirtualHost {ips}>\n',
                f'ServerName "{d["dom"]}"\nServerAlias {d["dom"]}\n'
                f'ServerIdent on "{d["dom"] if legacy_ident else identity}"\nDefaultServer {"on" if d["dom"] == default else "off"}\nPort 21\n',
                f'DefaultRoot ~\nAllowOverride {"on" if allow_override else "off"}\n' +
                ('AllowOverwrite on\n' if allow_overwrite else ''),
                f'PassivePorts {c["passive_ports"][0]} {c["passive_ports"][1]}\n',
                'TLSEngine on\nTLSRequired on\nTLSProtocol TLSv1.2 TLSv1.3\nTLSVerifyClient off\n',
                f'{prefix}CertificateFile {cert}\n',
                f'{prefix}CertificateKeyFile {key}\n']
        if d.get('home'):
            extended, transfer = log_paths(d)
            out += [f'ExtendedLog {extended} ALL\n',
                    f'TransferLog {transfer}\n']
        if d['has_ca']:
            out.append(f'TLSCertificateChainFile {chain}\n')
        out += ['<Limit LOGIN>\n', 'DenyAll\n' if d['suspended'] else
                f'Order {"deny,allow" if legacy_login else "allow,deny"}\nDenyAll\nAllowGroup {d["group"]}\n',
                '</Limit>\n</VirtualHost>\n']
    return ''.join(out).encode()


class Engine:
    def __init__(self, c):
        self.c = c
        self.root = Path(c['state_dir'])
        self.managed = Path(c['managed_file'])

    def read_state(self):
        state = load_json(self.root / 'state.json', {'domains': {}})
        state.setdefault('pending', {})
        return state

    def validate_config(self, candidate):
        expanded, _, _, _, count = scan(self.c['proftpd_conf'], self.c['managed_file'])
        if count != 1:
            raise ValueError('Exactly one top-level managed Include is required; run activate')
        # Includes are expanded into the shadow config; no live file replacement.
        with tempfile.TemporaryDirectory(prefix='ftps-config-') as tmp:
            p = Path(tmp) / 'proftpd.conf'
            p.write_text(expanded.replace('@@VIRTUALMIN_FTPS@@\n', candidate.decode()))
            run([self.c['proftpd_bin'], '-t', '-c', str(p)])

    def reload(self):
        run(['/usr/bin/systemctl', 'reload', 'proftpd.service'])
        run(['/usr/bin/systemctl', 'is-active', '--quiet', 'proftpd.service'])

    def restore(self, old):
        current = self.read_state()
        for ident, d in current['domains'].items():
            previous = old['state'].get('domains', {}).get(ident, {})
            if d.get('log_view') and (d.get('log_view') != previous.get('log_view') or
                                      d.get('log_dir') != previous.get('log_dir')):
                unmount_view(d)
        data = base64.b64decode(old['config'])
        self.validate_config(data)
        atomic(self.managed, data, 0o600)
        atomic(self.root / 'state.json', json_bytes(old['state']))
        self.reload()
        prepare_views(old['state'].get('domains', {}))

    @contextlib.contextmanager
    def lock(self):
        trusted(self.root, directory=True)
        p = self.root / 'lock'
        fd = os.open(p, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            os.close(fd)

    def recover(self):
        journal = self.root / 'journal.json'
        if journal.exists():
            self.restore(load_json(journal))
            journal.unlink()

    def commit(self, state, data, expected_current=None):
        current = self.managed.read_bytes()
        if not current.startswith(HEADER.encode()):
            raise ValueError('Managed file ownership marker missing')
        oldstate = self.read_state()
        expected = render_state(oldstate, self.c) if expected_current is None else expected_current
        if current != expected:
            raise ValueError('Managed configuration drift; manual review required')
        prepare_logs(state['domains'], self.c, old_domains=oldstate['domains'])
        self.validate_config(data)
        old = {'state': oldstate, 'config': base64.b64encode(current).decode()}
        atomic(self.root / 'journal.json', json_bytes(old))
        mounted = []
        try:
            for ident, previous in oldstate['domains'].items():
                current_domain = state['domains'].get(ident, {})
                if previous.get('log_view') and previous.get('log_dir') != current_domain.get('log_dir'):
                    unmount_view(previous)
            mounted = prepare_views(state['domains'])
            atomic(self.managed, data)
            self.reload()
            atomic(self.root / 'state.json', json_bytes(state))
            atomic(self.root / 'previous.json', json_bytes(old))
        except BaseException as original:
            for d in reversed(mounted):
                unmount_view(d)
            try:
                self.restore(old)
                (self.root / 'journal.json').unlink()
            except Exception:
                raise ValueError('Apply AND recovery failed. Journal retained; '
                                 'stop timer and inspect service immediately') from original
            raise
        (self.root / 'journal.json').unlink()

    def execute(self, request, apply=False):
        op = request['operation']
        if op == 'read-log':
            if apply:
                raise ValueError('Log viewing is read-only')
            return self.read_log(request)
        if op == 'inspect':
            if apply:
                raise ValueError('Domain inspection is read-only')
            return self.inspect(request)
        if op not in ('upsert', 'delete', 'reconcile', 'rollback', 'repair-login-order', 'use-website-certificates'):
            raise ValueError('Unknown operation')
        if apply and self.c['mode'] != 'live' and op != 'rollback':
            raise ValueError('Plugin is in dry-run mode. No active settings changed')
        if apply:
            with self.lock():
                if self.c.get('_config_path') and op != 'rollback':
                    current = configuration(self.c['_config_path'])
                    if current != self.c or current['mode'] != 'live':
                        raise ValueError('Configuration changed while waiting for lock; retry')
                self.recover()
                return self._execute(request, True)
        # Dry runs do not create locks, state, managed files or issue reloads.
        return self._execute(request, False)

    def read_log(self, request):
        if set(request) != {'operation', 'id', 'log'}:
            raise ValueError('Unexpected log request fields')
        ident, name = str(request['id']), request['log']
        if not re.fullmatch(r'[0-9]{1,40}', ident) or name not in ('ftp', 'transfer'):
            raise ValueError('Invalid domain or log selector')
        d = self.read_state()['domains'].get(ident)
        if not d or not d.get('log_dir'):
            raise ValueError('Protected logs are not yet configured for this domain')
        directory = Path(d['log_dir'])
        trusted(directory, directory=True, log_path=True)
        path = directory / ('ftp.log' if name == 'ftp' else 'xferlog')
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            st = os.fstat(fd)
            import grp
            if (not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or st.st_uid != 0 or
                    st.st_gid != grp.getgrnam(d['group']).gr_gid or st.st_mode & 0o022):
                raise ValueError('Unsafe protected log')
            start = max(0, st.st_size - 65536)
            os.lseek(fd, start, os.SEEK_SET)
            data = os.read(fd, 65536)
            if start:
                data = data.split(b'\n', 1)[-1]
            lines = data.decode('utf-8', errors='replace').splitlines()
            return {'operation': 'read-log', 'scope': {'id': ident, 'domain': d['dom']},
                    'log': name, 'text': '\n'.join(lines[-200:]),
                    'truncated': bool(start or len(lines) > 200)}
        finally:
            os.close(fd)

    def inspect(self, request):
        """Only validate the selected domain. No reconciliation, writes or reloads.

        Foreign definitions are read solely for conflicts and site prerequisites.
        Certificates/state of other domains are never validated or listed.
        """
        if len(request.get('domains', [])) != 1:
            raise ValueError('Select exactly one domain for inspection')
        d = normalize(request['domains'][0])
        checks, requirements = [], []
        kind = None
        default = validate_default_domain(self.c.get('default_domain', ''))
        role_check = {'label': 'Rolle dieses FTPS-Hosts', 'status': 'info',
                       'detail': 'Als ProFTPD-Standardhost vorgesehen (DefaultServer on). Bei bereits passenden IP-VirtualHosts hängt die erste Auswahl weiterhin von der Konfiguration ab.'
                                 if d['dom'] == default else 'Domain-VirtualHost; kein ausdrücklich gesetzter Standardhost.'}
        with tempfile.TemporaryDirectory(prefix='ftps-inspect-') as tmp:
            try:
                kind, _, has_ca = certificate(d, Path(tmp) / d['id'])
                checks.append({'label': 'Zertifikat und Schlüssel', 'status': 'ok',
                               'detail': f'{kind}: Schlüssel passt, Domainname und Gültigkeit sind geprüft; die Zertifikatskette ist vertrauenswürdig.'})
            except (ValueError, OSError) as err:
                checks.append({'label': 'Zertifikat und Schlüssel', 'status': 'error',
                               'detail': 'Das Zertifikat konnte nicht bestätigt werden. Dateien, Schlüsselpaar, Domainname, Gültigkeit und Zertifikatskette prüfen.',
                               'technical': str(err)})
        try:
            expanded, hosts, _, ipv6, count = scan(self.c['proftpd_conf'], self.c['managed_file'])
            collision = conflict(d, hosts)
            checks.append({'label': 'Vorhandener FTP-VirtualHost',
                           'status': 'error' if collision else 'ok',
                           'detail': 'Für diese Domain besteht eine fremde FTP-Konfiguration. Eine automatische Übernahme erfolgt nicht.' if collision else
                                     'Kein Konflikt für die ausgewählte Domain gefunden.',
                           'technical': collision or ''})
            if d.get('ip6') and 'off' in ipv6:
                checks.append({'label': 'IPv6', 'status': 'error',
                               'detail': 'Diese Domain hat eine IPv6-Adresse, ProFTPD hat IPv6 aber global deaktiviert.'})
            policy = main_policy(expanded)
            requirements.append({'label': 'Hauptserver ausgeschaltet',
                                 'status': 'warning' if policy['issues'] else 'ok',
                                 'detail': ' '.join(policy['issues']) if policy['issues'] else
                                           'Port 0 und DefaultServer off: kein eigener Hauptserver-Dienst. TLS muss dort nicht eingeschaltet werden.'})
            requirements.append({'label': 'Einbindung des Plugins',
                                 'status': 'ok' if count == 1 else 'info',
                                 'detail': 'Der Plugin-Include ist eingebunden.' if count == 1 else
                                           'Noch nicht eingebunden. Das ist im Prüfmodus normal; es wurde nichts aktiviert.'})
        except (ValueError, OSError) as err:
            requirements.append({'label': 'ProFTPD-Konfiguration lesen', 'status': 'error',
                                 'detail': 'Die gemeinsamen Konfigurationsvoraussetzungen konnten nicht gelesen werden.',
                                 'technical': str(err)})
        requirements.insert(0, role_check)
        # Deliberately no global proftpd -t: it would validate other hosts too.
        requirements.append({'label': 'ProFTPD-Gesamtkonfiguration', 'status': 'info',
                             'detail': 'Nicht getestet: Diese Einzelprüfung untersucht keine Zertifikate anderer Domains. Vor aktiven Änderungen erfolgt weiterhin ein vollständiger Syntaxcheck.'})
        return {'operation': 'inspect', 'applied': False, 'mode': self.c['mode'],
                'scope': {'id': d['id'], 'domain': d['dom']},
                'domain': {'ip': d.get('ip', ''), 'ip6': d.get('ip6', ''),
                           'group': d['group'], 'kind': kind, 'greeting': d['dom'], 'default_host': d['dom'] == default},
                'checks': checks, 'requirements': requirements,
                'notice': 'Nur die ausgewählte Domain wurde geprüft. Keine aktive Konfiguration wurde geändert.',
                'name_selection': 'Bei gemeinsamer IP erfolgt die Namensauswahl durch HOST oder TLS-SNI. Vor dieser Auswahl ist die erste FTP-Begrüßung nicht domainbezogen garantiert.'}

    def _execute(self, request, apply):
        op = request['operation']
        if (self.root / 'journal.json').exists():
            raise ValueError('Unfinished transaction; recovery required before planning')
        if op == 'rollback':
            old = load_json(self.root / 'previous.json')
            if not old:
                raise ValueError('No previous transaction')
            if apply:
                # Keep a journal until the recovery reload has succeeded.
                atomic(self.root / 'journal.json', json_bytes(old))
                self.restore(old)
                (self.root / 'journal.json').unlink()
                (self.root / 'previous.json').unlink()
            return {'operation': op, 'applied': apply}
        state = self.read_state()
        if op == 'repair-login-order':
            expanded, _, _, _, count = scan(self.c['proftpd_conf'], self.c['managed_file'])
            if count != 1:
                raise ValueError('Repair requires exactly one managed Include')
            current = self.managed.read_bytes()
            identity = server_fqdn()
            corrected = render(state['domains'], self.c, identity=identity)
            legacy = render_state(state, self.c, legacy_login=True)
            if current not in (corrected, render_state(state, self.c), legacy):
                raise ValueError('Managed configuration drift; repair refuses foreign changes')
            changed = current != corrected
            if apply and changed:
                updated = dict(state, server_fqdn=identity, allow_overwrite=True, allow_override=True)
                self.commit(updated, corrected, expected_current=current)
            elif not apply:
                self.validate_config(corrected)
            return {'operation': op, 'changed': changed, 'applied': bool(apply and changed),
                    'mode': self.c['mode'], 'syntax_test': 'passed' if changed or not apply else 'not-needed'}
        expected_current = None
        if op == 'use-website-certificates':
            current = self.managed.read_bytes()
            accepted = [render_state(state, self.c),
                        render_state(state, self.c, legacy_login=True)]
            if current not in accepted and 'server_fqdn' not in state:
                # Older installs may already have the approved server greeting
                # in the file but no identity in state. Accept ONLY an exact
                # render with the currently validated local server FQDN.
                identity = server_fqdn()
                accepted.extend(render(
                    state['domains'], self.c, legacy_login=legacy_login,
                    identity=identity,
                    allow_overwrite=state.get('allow_overwrite', False),
                    allow_override=state.get('allow_override', False))
                    for legacy_login in (False, True))
            if current not in accepted:
                raise ValueError('Managed configuration drift; migration refuses foreign changes')
            expected_current = current
            op = 'reconcile'
        if expected_current is None and self.managed.exists() and self.managed.read_bytes() != render_state(state, self.c):
            raise ValueError('Managed configuration drift; manual review required')
        # Core lifecycle hooks can precede save_domain(). Do not let a timer
        # snapshot of the old domain files immediately undo a just-applied hook.
        if (apply and op == 'reconcile' and
                0 <= now() - state.get('last_lifecycle', 0) < 120):
            return {'operation': op, 'applied': False, 'changed': False,
                    'deferred': 'recent lifecycle operation; retry after save grace period',
                    'syntax_test': 'not-run: lifecycle grace period'}
        domains = dict(state['domains'])
        pending = dict(state['pending'])
        expanded, hosts, tls, ipv6, count = scan(self.c['proftpd_conf'], self.c['managed_file'])
        warnings = []
        warnings.extend(main_policy(expanded)['issues'])
        if count != 1:
            warnings.append('Managed Include is not installed; activate before live use')
        if op == 'delete':
            ident = str(request['id'])
            if not re.fullmatch(r'[0-9]{1,40}', ident):
                raise ValueError('Invalid domain ID')
            if apply and ident in domains:
                unmount_view(domains[ident])
            domains.pop(ident, None)
            pending.pop(ident, None)
            targets = []
        else:
            targets = [normalize(d) for d in request['domains']]
            if len({d['id'] for d in targets}) != len(targets):
                raise ValueError('Duplicate domain IDs')
            names = [d['dom'] for d in targets]
            ids = {d['id'] for d in targets}
            if op == 'upsert':
                names += [d['dom'] for i, d in domains.items() if i not in ids]
                names += [p['domain']['dom'] for i, p in pending.items() if i not in ids]
            if len(set(names)) != len(names):
                raise ValueError('Duplicate domain names')
            if op == 'reconcile':
                domains = {}
                pending = {}
        changes = []
        with tempfile.TemporaryDirectory(prefix='ftps-cert-') as temp:
            for d in targets:
                err = conflict(d, hosts)
                if err:
                    raise ValueError(err + '; automatic migration is deliberately disabled')
                try:
                    kind, fingerprint, has_ca = certificate(d, Path(temp) / d['id'])
                except (ValueError, OSError) as err:
                    # Domain creation can precede the first successful ACME issue.
                    # Queue only a NEW, not-yet-served host; never hide a failed
                    # renewal of an existing active host behind a pending status.
                    if (d['id'] not in state['domains'] and
                            (request.get('defer_certificate') or op == 'reconcile')):
                        pending[d['id']] = {'domain': d, 'error': str(err)}
                        continue
                    raise
                pending.pop(d['id'], None)
                old = state['domains'].get(d['id'], {})
                item = dict(d, kind=kind, fingerprint=fingerprint, has_ca=has_ca,
                            certificate_source='website')
                if old != item:
                    public_keys = ('dom', 'ip', 'ip6', 'group', 'suspended', 'kind', 'certificate_source', 'home', 'user')
                    changes.append({'id': d['id'], 'domain': d['dom'], 'kind': kind,
                                    'before': {k: old.get(k) for k in public_keys},
                                    'after': {k: item.get(k) for k in public_keys}})
                domains[d['id']] = item
            if len({d['dom'] for d in domains.values()}) != len(domains):
                raise ValueError('Duplicate domain names')
            if any(d.get('ip6') for d in domains.values()) and 'off' in ipv6:
                raise ValueError('IPv6 domain requested but main UseIPv6 is off')
            # Deletion remains possible even if the site's primary TLS is broken.
            if apply and op != 'delete' and domains and warnings:
                raise ValueError('; '.join(warnings))
            domains = {ident: dict(d, log_dir=protected_log_dir(ident, self.c),
                                               log_view=str(Path(d['home']) / 'logs/ftps'))
                       for ident, d in domains.items()}
            identity = server_fqdn() if domains else state.get('server_fqdn')
            data = render(domains, self.c, identity=identity)
            newstate = {'domains': domains, 'pending': pending, 'allow_overwrite': True, 'allow_override': True}
            if identity is not None:
                newstate['server_fqdn'] = identity
            if 'last_lifecycle' in state:
                newstate['last_lifecycle'] = state['last_lifecycle']
            removed = sorted(set(state['domains']) - set(domains))
            changed = newstate != state or (expected_current is not None and expected_current != data)
            if apply and changed:
                if op in ('upsert', 'delete'):
                    newstate['last_lifecycle'] = now()
                self.commit(newstate, data, expected_current=expected_current)
            elif apply:
                prepare_logs(domains, self.c, old_domains=state['domains'])
                prepare_views(domains)
            elif not apply:
                prepare_logs(domains, self.c, apply=False, old_domains=state['domains'])
                preview_views = {ident: dict(d, log_dir=state['domains'].get(ident, d).get('log_dir', d['log_dir']))
                                 for ident, d in domains.items()}
                prepare_views(preview_views, apply=False)
                if count == 1:
                    self.validate_config(data)
            return {'operation': op, 'applied': bool(apply and changed),
                    'changed': changed, 'updates': changes, 'removed_ids': removed,
                    'pending': {i: {'domain': p['domain']['dom'], 'reason': p['error']}
                                for i, p in pending.items()},
                    'mode': self.c['mode'],
                    'warnings': warnings,
                    'syntax_test': ('not-run: no Include' if count != 1 else
                                    'not-run: no changes' if apply and not changed else 'passed')}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', default=CONFIG)
    p.add_argument('--apply', action='store_true')
    args = p.parse_args()
    if os.geteuid() != 0:
        p.error('Must run as root')
    c = configuration(args.config)
    trusted(c['proftpd_conf'])
    trusted(c['proftpd_bin'])
    trusted(Path(c['managed_file']).parent, directory=True)
    if Path(c['state_dir']).exists():
        trusted(c['state_dir'], directory=True)
    request = json.loads(sys.stdin.buffer.read(8 * 1024 * 1024))
    result = Engine(c).execute(request, args.apply)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)
