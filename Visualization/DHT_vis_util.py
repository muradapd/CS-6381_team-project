from filelock import FileLock

def write_vis_command(infile, cmd_type, source, destination, command):

    lockfile = infile + '.lock'

    # Initiate lockfile
    lock = FileLock(lockfile)

    with lock:
        with open(infile, "a") as f:
            f.write(f'{cmd_type}-{source}-{command}-{destination}\n')
