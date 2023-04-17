# John Gordley
# Tools to unpack zNode values

def unpack_znode_val(value):
    # Format is in the following
    # disc_addr-127.0.0.1:2128|broker_addr-10.0.0.1:5555|disc_list-10.0.0.2:5555,10.0.0.3:5555

    value_dict = {}

    split_1 = value.decode().split('|')
    
    disc_split = split_1[0].split('-')
    value_dict[disc_split[0]] = disc_split[1]

    broker_split = split_1[1].split('-')
    value_dict[broker_split[0]] = broker_split[1]

    disc_list_split = split_1[2].split('-')
    value_dict[disc_list_split[0]] = list(disc_list_split[1].split(','))

    return value_dict

def pack_znode_val(disc_addr, broker_addr, disc_list):

    return f'disc_addr-{disc_addr}|broker_addr-{broker_addr}|disc_list-{",".join(disc_list)}'