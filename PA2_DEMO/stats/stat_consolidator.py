import argparse

parser = argparse.ArgumentParser(description="Consolidate multiple csv files with statistics into master files")

parser.add_argument('--directory', type=str, help="The directory where stat csv files are stored")
parser.add_argument('--num_subs', type=int, help="The number of sub files to look for")
parser.add_argument('--num_pubs', type=int, help="The number of pub files to look for")

args = parser.parse_args()

directory = args.directory
num_subs = args.num_subs
num_pubs = args.num_pubs

for stat in ['isready', 'register', 'lookup']:
    for i in range(1, num_subs + 1):

        # Create the filename
        fname = f'{directory}/sub{i}_Centralized_{stat}.csv'
        lines = []

        print(f'Reading and copying {fname}')

        # Open the file
        with open(fname, "r") as f:

            # Copy the lines
            for line in f.readlines():
                lines.append(line)
        
        # Open the master file
        master_fname = f'{directory}/master/sub_{stat}.csv'
        with open(master_fname, 'a') as f:

            # Append the copied lines
            for line in lines:
                f.write(line)

for stat in ['isready', 'register']:
    for i in range(1, num_pubs + 1):

        # Create the filename
        fname = f'{directory}/pub{i}_Centralized_{stat}.csv'
        lines = []

        print(f'Reading and copying {fname}')

        # Open the file
        try:
            with open(fname, "r") as f:

                # Copy the lines
                for line in f.readlines():
                    lines.append(line)
        except:
            print(f'Could not open {fname}')
        
        # Open the master file
        master_fname = f'{directory}/master/pub_{stat}.csv'

        try:
            with open(master_fname, 'a') as f:

                # Append the copied lines
                for line in lines:
                    f.write(line)
        except:
            print(f'Could not open {fname}')