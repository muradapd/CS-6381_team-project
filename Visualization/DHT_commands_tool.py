import argparse
from filelock import FileLock

# Gather command line args
parser = argparse.ArgumentParser(description="DHT commands tool")

parser.add_argument('-i', '--infile', type=str, required=True, help='The file path of the input file from which commands are pulled')

args = parser.parse_args()
infile = args.infile
lockfile = args.infile + '.lock'

# Initiate lockfile
lock = FileLock(lockfile)

command = input('DHT vis> ')
while command != 'q' and command != 'quit':

    with lock:
        with open(infile, "a") as f:
            f.write(command + '\n')

    command = input('DHT vis> ')