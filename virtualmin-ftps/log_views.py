"""Linux read-only bind views, attached via pinned directory descriptors."""
import ctypes
import grp
import os
from pathlib import Path
import platform
import pwd
import stat

LIBC = ctypes.CDLL(None, use_errno=True)



def resolve_log_source(source):
    """Allow only the administrator-owned /var/log alias; pin its safe target later."""
    source = Path(source)
    alias = Path('/var/log')
    if not source.is_relative_to(alias) or not alias.is_symlink():
        return str(source)
    link = alias.lstat()
    parent = alias.parent.lstat()
    if (link.st_uid != 0 or parent.st_uid != 0 or
            not stat.S_ISDIR(parent.st_mode) or parent.st_mode & 0o022):
        raise ValueError('Unprotected /var/log alias')
    raw = os.readlink(alias)
    target = Path(raw)
    if (not target.is_absolute() or '..' in target.parts or str(target) != raw):
        raise ValueError('Noncanonical /var/log alias target')
    for p in (target, *target.parents):
        s = p.lstat()
        if (not stat.S_ISDIR(s.st_mode) or s.st_uid != 0 or s.st_mode & 0o022):
            raise ValueError(f'Unprotected /var/log alias target: {p}')
    return str(target / source.relative_to(alias))


def mount_entry(target):
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        fields = line.split(' - ', 1)[0].split()
        if len(fields) > 5 and fields[4] == str(target):
            return set(fields[5].split(','))
    return None


def open_directory(path):
    fd = os.open('/', os.O_PATH | os.O_DIRECTORY)
    try:
        for part in Path(path).parts[1:]:
            child = os.open(part, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=fd)
            os.close(fd)
            fd = child
            if os.fstat(fd).st_mode & 0o002:
                raise ValueError('World-writable customer view ancestor')
        return fd
    except BaseException:
        os.close(fd)
        raise


def unmount_fd(fd, detach=True):
    if LIBC.umount2(('/proc/self/fd/' + str(fd)).encode(), 2 if detach else 0) < 0:
        err = ctypes.get_errno()
        raise OSError(err, os.strerror(err))


def unmount_view(d):
    target, source = d.get('log_view'), d.get('log_dir')
    if not target or not source:
        return
    if target != str(Path(d['home']) / 'logs/ftps'):
        raise ValueError('Unexpected FTP log mount path')
    a = os.stat(source)
    candidates = {target} if mount_entry(target) is not None else set()
    # Identify relocated views by protected source inode, not by a user path.
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        fields = line.split(' - ', 1)[0].split()
        if len(fields) > 5 and fields[4].startswith(d['home'] + '/'):
            candidates.add(fields[4])
    for candidate in sorted(candidates, key=len, reverse=True):
        try:
            fd = open_directory(candidate)
        except FileNotFoundError:
            continue
        try:
            b = os.fstat(fd)
            if (a.st_dev, a.st_ino) != (b.st_dev, b.st_ino):
                if candidate == target:
                    raise ValueError('Refusing to unmount foreign filesystem')
                continue
            unmount_fd(fd)
        finally:
            os.close(fd)


def readonly_bind(source, target_fd, target):
    if platform.machine() not in ('x86_64', 'aarch64'):
        raise ValueError('Read-only FTP views currently require Linux x86_64 or aarch64')
    source = resolve_log_source(source)
    source_fd = open_directory(source)
    tree = -1
    attached = False
    try:
        # open_tree(AT_EMPTY_PATH | OPEN_TREE_CLONE | O_CLOEXEC).
        tree = LIBC.syscall(428, source_fd, ctypes.c_char_p(b''),
                            0x1000 | 1 | os.O_CLOEXEC)
        if tree < 0:
            err = ctypes.get_errno()
            raise OSError(err, 'Cannot clone FTP log mount: ' + os.strerror(err))
        class Attr(ctypes.Structure):
            _fields_ = [('attr_set', ctypes.c_uint64), ('attr_clr', ctypes.c_uint64),
                        ('propagation', ctypes.c_uint64), ('userns_fd', ctypes.c_uint64)]
        attrs = Attr(1 | 2 | 4 | 8, 0, 0, 0)  # ro,nosuid,nodev,noexec
        if LIBC.syscall(442, tree, ctypes.c_char_p(b''), 0x1000,
                        ctypes.byref(attrs), ctypes.sizeof(attrs)) < 0:
            err = ctypes.get_errno()
            raise OSError(err, 'Cannot protect FTP log mount: ' + os.strerror(err))
        # move_mount uses only pinned FDs; customers cannot redirect its target
        # by replacing/renaming a home directory during this operation.
        if LIBC.syscall(429, tree, ctypes.c_char_p(b''), target_fd,
                        ctypes.c_char_p(b''), 0x44) < 0:
            err = ctypes.get_errno()
            raise OSError(err, 'Cannot attach FTP log mount: ' + os.strerror(err))
        attached = True
        entry = mount_entry(target)
        a, b = os.stat(source), os.stat(target)
        if (not entry or not {'ro', 'nosuid', 'nodev', 'noexec'} <= entry or
                (a.st_dev, a.st_ino) != (b.st_dev, b.st_ino)):
            raise ValueError('FTP log mount path changed during attachment')
    except BaseException:
        if attached:
            unmount_fd(tree, detach=True)
        raise
    finally:
        if tree >= 0:
            os.close(tree)
        os.close(source_fd)


def prepare_views(domains, apply=True):
    mounted = []
    try:
        for d in domains.values():
            target = d.get('log_view')
            if not target:
                continue
            if target != str(Path(d['home']) / 'logs/ftps'):
                raise ValueError('Unexpected customer log view path')
            if apply and mount_entry(target) is None:
                unmount_view(d)
            home_fd = open_directory(d['home'])
            logs_fd = target_fd = None
            try:
                try:
                    logs_fd = os.open('logs', os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW,
                                      dir_fd=home_fd)
                except FileNotFoundError:
                    if not apply:
                        continue
                    os.mkdir('logs', 0o750, dir_fd=home_fd)
                    logs_fd = os.open('logs', os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW,
                                      dir_fd=home_fd)
                    os.chown('/proc/self/fd/' + str(logs_fd),
                             pwd.getpwnam(d['user']).pw_uid, grp.getgrnam(d['group']).gr_gid)
                    os.chmod('/proc/self/fd/' + str(logs_fd), 0o750)
                if os.fstat(logs_fd).st_mode & 0o002:
                    raise ValueError('World-writable customer logs directory')
                try:
                    target_fd = os.open('ftps', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                        dir_fd=logs_fd)
                except FileNotFoundError:
                    if not apply:
                        continue
                    os.mkdir('ftps', 0o750, dir_fd=logs_fd)
                    target_fd = os.open('ftps', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                        dir_fd=logs_fd)
                    os.fchown(target_fd, 0, grp.getgrnam(d['group']).gr_gid)
                    os.fchmod(target_fd, 0o750)
                entry = mount_entry(target)
                if entry is not None:
                    a, b = os.stat(d['log_dir']), os.fstat(target_fd)
                    if ((a.st_dev, a.st_ino) != (b.st_dev, b.st_ino) or
                            not {'ro', 'nosuid', 'nodev', 'noexec'} <= entry):
                        raise ValueError('Foreign or writable mount at FTP log view')
                    continue
                if os.listdir(target_fd):
                    raise ValueError('FTP log mountpoint is not empty')
                if not apply:
                    continue
                st = os.fstat(target_fd)
                if st.st_uid != 0 or st.st_mode & 0o022:
                    raise ValueError('Unprotected FTP log mountpoint')
                readonly_bind(d['log_dir'], target_fd, target)
                mounted.append(d)
            finally:
                if target_fd is not None:
                    os.close(target_fd)
                if logs_fd is not None:
                    os.close(logs_fd)
                os.close(home_fd)
        return mounted
    except BaseException:
        for d in reversed(mounted):
            unmount_view(d)
        raise
