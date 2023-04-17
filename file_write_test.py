lookup_fname = f'stats/sub1_DHT_lookup.txt'

for i in range(5):
    with open(lookup_fname, 'a') as file:
        file.write(f'{i}\n')