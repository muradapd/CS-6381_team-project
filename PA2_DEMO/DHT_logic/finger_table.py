import json
import random
import hashlib

def hash_func (value, bits_hash=8):
    '''Hash function take from professor Gokhales exp_generator.py script'''

    # first get the digest from hashlib and then take the desired number of bytes from the
    # lower end of the 256 bits hash. Big or little endian does not matter.
    hash_digest = hashlib.sha256 (bytes (value, "utf-8")).digest ()  # this is how we get the digest or hash value
    # figure out how many bytes to retrieve
    num_bytes = int(bits_hash/8)  # otherwise we get float which we cannot use below
    hash_val = int.from_bytes (hash_digest[:num_bytes], "big")  # take lower N number of bytes

    return hash_val

def calculate_target_node(value, sorted_nodes):
    '''Takes in a sorted list of nodes and a value to find
     and returns the target node according to the finger table algorithm'''
    for node in sorted_nodes:
        if value % (2**8) < node.get('hash'):
            return node
    return sorted_nodes[0]

def gen_successors(dht_nodes, log=False):
    '''Takes in a list of nodes and sorts them by their hash value to create an ordered ring'''
    sorted_nodes = sorted(dht_nodes, key=lambda x: x.get('hash'))

    if log:
        for node in sorted_nodes:
            print(node.get('hash'))

    return sorted_nodes

def gen_48_bit_finger_tables(nodes):
    '''Takes in a sorted list of nodes and loops through to generate a dict of finger tables'''

    with open('finger_tables.out', 'w') as outfile:

        finger_tables = dict()
        
        for node in nodes:
            outfile.write(f'{node.get("id")}: {node.get("hash")}\n')

        for node in nodes:
            finger_tables[node.get('id')] = dict()
            outfile.write('--------------------------\n')
            outfile.write(f'{node.get("id")}: {node.get("hash")}\n')
            for i in range(0, 8):
                finger_tables[node.get("id")][i] = calculate_target_node(node.get('hash') + 2**i, nodes)
                outfile.write(f'{i} ({node.get("hash")} + 2^{i} = {node.get("hash") + 2**i}): {finger_tables[node.get("id")][i]}\n')
            
    outfile.close()
    return finger_tables

dht = None
with open('dht.json') as f:
    dht = json.load(f)

sorted_dht = gen_successors(dht.get('dht'))

fts = gen_48_bit_finger_tables(sorted_dht)

output_finger_dht = dict()
for node in sorted_dht:
    output_finger_dht[node.get('id')] = {
        'hash': node.get('hash'),
        'IP': node.get('IP'),
        'port': node.get('port'),
        'host': node.get('host'),
        'ftable': fts.get(node.get('id')).copy()
    }

with open('dht_vis_experiment.json', 'w') as fp:
    json.dump(output_finger_dht, fp)

def closest_preceding_node(node, value):

    for i in range(len(node.get('ftable'))-1, -1, -1):
        # if (finger[i] E (n, id))
        #   return finger[i]
        finger_i = node.get('ftable')[i].get('hash')
        if finger_i > node.get('hash') and finger_i < value:

            # Found a shortcut
            return node.get('ftable')[i]
        
    return node.get('ftable')[0]

def put(topic, value, first_node):
    '''Put function to put topic values into the DHT'''
    
    # Get hash value of topic
    t_hash = hash_func(topic) % (2**48)

    print(f'Topic [{topic}] hash is {t_hash}')

    # Check if the value is between our hash and our successor hash
    if t_hash > first_node.get('hash') and t_hash <= first_node.get('ftable')[0].get('hash'):

        print(f'Hash {t_hash} is with our successor ({first_node.get("hash")}, {first_node.get("ftable")[0].get("hash")}]')

        # Our topic belongs with our successor
        if first_node.get('ftable')[0]['pub_info'].get(t_hash, 0):
            first_node.get('ftable')[0]['pub_info'][t_hash].append(f'{topic}//{value}')
        else:
            first_node.get('ftable')[0]['pub_info'][t_hash] = [f'{topic}//{value}']

        return

    highest_predecessor = closest_preceding_node(first_node, t_hash)
    print(f'Highest without going over: {highest_predecessor.get("hash")}')

    put(topic, value, highest_predecessor)
    
def search(topic, first_node):
    '''Search function to find a list of publisher info from the DHT'''
    
    # Get hash value of topic
    t_hash = hash_func(topic) % (2**48)

    # print(f'Topic [{topic}] hash is {t_hash}')

    # Check if the value is between our hash and our successor hash
    if t_hash > first_node.get('hash') and t_hash <= first_node.get('ftable')[0].get('hash'):

        # print(f'Hash {t_hash} is with our successor ({first_node.get("hash")}, {first_node.get("ftable")[0].get("hash")}]')

        return first_node.get("ftable")[0].get('pub_info')[t_hash]

    highest_predecessor = closest_preceding_node(first_node, t_hash)
    # print(f'Highest without going over: {highest_predecessor.get("hash")}')

    return search(topic, highest_predecessor)
    
# topics = ["weather", "humidity", "airquality", "light", "pressure", "temperature", "sound", "altitude", "location"]

# for id, topic in enumerate(topics):

#     # Pick a random node
#     first_node = sorted_dht[random.randint(0, len(sorted_dht) - 1)]
#     print(first_node)

#     print(first_node.get('hash'))

#     # Put the topic value
#     put(topic, id, first_node)

# for node in sorted_dht:
#     print(f'{node.get("id")} - {node.get("hash")}: {node.get("pub_info")}')

# print('-------- Searching --------')
# for topic in topics:
#     first_node = sorted_dht[random.randint(0, len(sorted_dht) - 1)]
#     print(f'Searching {topic}: {search(topic, first_node)}')
