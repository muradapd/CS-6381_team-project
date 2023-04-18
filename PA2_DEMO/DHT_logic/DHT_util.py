import hashlib

def hash_func (value, bits_hash=48):
    '''Hash function take from professor Gokhales exp_generator.py script'''

    # first get the digest from hashlib and then take the desired number of bytes from the
    # lower end of the 256 bits hash. Big or little endian does not matter.
    hash_digest = hashlib.sha256 (bytes (value, "utf-8")).digest ()  # this is how we get the digest or hash value
    # figure out how many bytes to retrieve
    num_bytes = int(bits_hash/8)  # otherwise we get float which we cannot use below
    hash_val = int.from_bytes (hash_digest[:num_bytes], "big")  # take lower N number of bytes

    return hash_val

def closest_preceding_node(hash, value, ftable):
    ''' 
    Takes in the current nodes hash, a value to search for, and a finger table and returns the 
    highest node without going over
    '''

    for i in range(len(ftable)-1, -1, -1):
        # if (finger[i] E (n, id))
        #   return finger[i]
        finger_i = ftable[str(i)].get('hash')
        if finger_i > hash and finger_i < value:

            # Found a shortcut
            return ftable[str(i)]
        
    return ftable['0']

def put(topic, value, first_node):
    '''Put function to put topic values into the DHT'''
    
    # Get hash value of topic
    t_hash = hash_func(topic) % (2**48)

    print(f'Topic [{topic}] hash is {t_hash}')

    # Check if the value is between our hash and our successor hash
    if t_hash > first_node.get('hash') and t_hash <= first_node.get('ftable')['0'].get('hash'):

        print(f'Hash {t_hash} is with our successor ({first_node.get("hash")}, {first_node.get("ftable")["0"].get("hash")}]')

        # Our topic belongs with our successor
        if first_node.get('ftable')['0']['pub_info'].get(t_hash, 0):
            first_node.get('ftable')['0']['pub_info'][t_hash].append(f'{topic}//{value}')
        else:
            first_node.get('ftable')['0']['pub_info'][t_hash] = [f'{topic}//{value}']

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
    if t_hash > first_node.get('hash') and t_hash <= first_node.get('ftable')['0'].get('hash'):

        # print(f'Hash {t_hash} is with our successor ({first_node.get("hash")}, {first_node.get("ftable")[0].get("hash")}]')

        return first_node.get("ftable")['0'].get('pub_info')[t_hash]

    highest_predecessor = closest_preceding_node(first_node, t_hash)
    # print(f'Highest without going over: {highest_predecessor.get("hash")}')

    return search(topic, highest_predecessor)