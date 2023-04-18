import argparse
import time
import logging
import configparser
import json
import zmq  # ZMQ sockets

parser = argparse.ArgumentParser()
parser.add_argument('-n', '--name', required=False, type=str,
                    help='the name of this discovery service node ex. disc11')
parser.add_argument('-p', '--publishers', required=True,
                    type=int, help='number of publishers in the system')
parser.add_argument('-s', '--subscribers', required=True,
                    type=int, help='number of subscribers in the system')
parser.add_argument('--port', required=True,
                    type=int, help='the port of the discovery service')
parser.add_argument('-j', '--json', required=False, type=str,
                    help='the path to a json file with DHT information')

args = parser.parse_args()

hash = None
finger_table = None
ip = None
port = None

name = args.name
num_subscribers = args.subscribers
num_publishers = args.publishers

input_dht = args.json
if input_dht:
    with open(input_dht) as f:
        dht = json.load(f)

        hash = dht.get(name, 0).get('hash')
        finger_table = dht.get(name, 0).get('ftable').copy()
        ip = dht.get(name, 0).get('IP')
        port = dht.get(name, 0).get('port')
        
# Next get the ZMQ context
logger.debug("DiscoveryMW::configure - obtain ZMQ context")
context = zmq.Context()  # returns a singleton object

# get the ZMQ poller object
logger.debug("DiscoveryMW::configure - obtain the poller")
poller = zmq.Poller()
        
rep = context.socket(zmq.DEALER)
rep.setsockopt(zmq.IDENTITY, hash)

connect_str = f'tcp://*:{port}'
rep.bind(connect_str)

poller.register(rep, zmq.POLLIN)

req = context.socket(zmq.ROUTER)
