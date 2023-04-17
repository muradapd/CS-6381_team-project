import argparse
import time
import logging
import configparser
import json
import sys

# Now import our CS6381 Middleware
from CS6381_MW.DiscoveryMW import DiscoveryMW

# Import DHT helper functions
from DHT_logic.DHT_util import hash_func, closest_preceding_node

##################################
#       DiscoveryAppln class
##################################

class DiscoveryAppln ():

    ########################################
    # constructor
    ########################################
    def __init__(self, logger):

        self.num_subscribers = None  # number of subscribers
        self.num_publishers = None  # number of publishers in the system
        self.broker = None
        # storage array for publishers
        self.publishers = dict()
        # storage array for subscribers
        self.subscribers = dict()
        self.dissemination = None  # direct or via broker
        self.mw_obj = None  # handle to the underlying Middleware object
        self.logger = logger  # internal logger for print statements

        # DHT Logic
        self.hash = None
        self.finger_table = None
        self.id = None
        self.ip = None
        self.port = None
        self.pub_count = 0
        self.sub_count = 0
        self.peers = {}

    ########################################
    # configure/initialize
    ########################################
    def configure(self, args):
        ''' Initialize the object '''

        # Here we initialize any internal variables
        self.logger.debug("DiscoveryAppln::configure")

        # initialize our variables
        self.num_subscribers = args.subscribers
        self.num_publishers = args.publishers

        # Now, get the configuration object
        self.logger.debug("DiscoveryAppln::configure - parsing config.ini")
        config = configparser.ConfigParser()
        config.read(args.config)
        self.lookup = config["Discovery"]["Strategy"]
        self.dissemination = config["Dissemination"]["Strategy"]

        # Get dht information
        self.id = args.name
        input_dht = args.json
        if input_dht:
            with open(input_dht) as f:
                dht = json.load(f)
                
                self.hash = dht.get(self.id, 0).get('hash')
                self.finger_table = dht.get(self.id, 0).get('ftable').copy()
                self.ip =  dht.get(self.id, 0).get('IP')
                self.port = dht.get(self.id, 0).get('port')

                for key, value in dht.items():
                    if key != self.id:
                        self.peers[key] = f"{value.get('IP')}:{value.get('port')}"


        # Now setup up our underlying middleware object to which we delegate
        # everything
        self.logger.debug(
            "DiscoveryAppln::configure - initialize the middleware object")
        self.mw_obj = DiscoveryMW(self.logger, self.lookup, self.peers, self.hash)
        # pass remainder of the args to the m/w object
        self.mw_obj.configure(args)

        self.logger.debug("DiscoveryAppln::configure - configuration complete")

        self.logger.info(f"DiscoveryAppln: Configured as {self.id}")

    ########################################
    # driver program
    ########################################
    def driver(self):
        ''' Driver program '''

        try:
            self.logger.debug("DiscoveryAppln::driver")

            # dump our contents (debugging purposes)
            self.dump()

            # logger format
            # self.logger.debug ("DiscoveryAppln::driver - register with the discovery service")

            # Wait forever for client connections
            while True:
                self.logger.info(f"DiscoveryAppln - Waiting for incoming things....")

                time.sleep(0.01)
                result = self.mw_obj.event_loop()
                if result:
                    self.logger.debug(f'DiscoveryAppln::driver - {result}')
                    self.logger.info(f"DiscoveryAppln - {result}")

                    # Handle registration request
                    if result.get('request_type', 0) == 'register':

                        role = result.get("role")
                        id = result.get("id")
                        topiclist = result.get("topic_list")
                        address = result.get("address")
                        port = result.get("port")
                        identity = result.get('identity', None)

                        if self.lookup == 'Centralized':
                            self.logger.debug(
                                f'DiscoveryAppln::driver - Registering new {role} with id {id}')
                            self.logger.info(f"DiscoveryAppln: Registering new {role} with id {id}")

                            if role == "publisher":
                                self.publishers[id] = {'topicList': topiclist, 'address': address, 'port': port}
                            elif role == "subscriber":
                                # Handle registration from subscriber
                                self.subscribers[id] = topiclist
                            else:
                                self.logger.info('DiscoveryAppln: the broker is here!')
                                self.broker = {'address': address, 'port': port}

                            self.logger.info(f'DiscoveryAppln: {len(self.publishers)}/{self.num_publishers} pubs and {len(self.subscribers)}/{self.num_subscribers} subs')
                            

                            self.mw_obj.verify_registration(identity, True)
                        else:
                            # Need to register to the DHT table
                            self.logger.info(f"DiscoveryAppln: Registering new {role} with id {id}")


                            if role == "broker":
                                self.logger.info('DiscoveryAppln - the broker is here!')

                                # Just jot down at this node that the broker is here
                                self.broker = 1

                                role = 'publisher'
                                topiclist = ["b"]

                            # If we get a subscriber we just add them to our node for is_ready purposes
                            if role == "subscriber":
                                self.subscribers[id] = topiclist
                                self.sub_count += 1
                                self.mw_obj.verify_registration(identity, True)

                            elif role == "publisher":

                                self.logger.info(f"DiscoveryAppln: Successor: {result.get('successor', 'False')}")
                                chain = result.get('chain', [])
                                chain.append(identity.hex())
                                
                                # Check for the 'succcessor' flag in the register request
                                # if true, we are the one who needs to store it
                                if result.get('successor', False):
                                    if self.publishers.get(topiclist[0]):
                                        self.publishers[topiclist[0]].append({'address': address, 'port': port})
                                    else:
                                        self.logger.info(f'DiscoveryAppln: We are responsible for topic: {topiclist} Storing it now.')
                                        self.publishers[topiclist[0]] = [{'address': address, 'port': port}]
                                        self.logger.info(f'DiscoveryAppln: Current list of publishers: {self.publishers}')
                                        self.mw_obj.verify_registration(identity, True, result.get('chain'))

                                else:
                                    # increment publisher count if its the first one
                                    if 'pub' in id.split(':')[0]:
                                        self.logger.info('DiscoveryAppln: Received a new register request from a publisher, incrementing pub count')
                                        self.pub_count += 1


                                    self.logger.info(f'Chain object: {chain}')

                                    # Loop through list of topics on publisher we need to place
                                    for topic in topiclist:

                                        # Get hash value of topic
                                        t_hash = hash_func(topic) % (2**8)

                                        # Check if the value is between our hash and our successor hash
                                        if t_hash > self.hash and t_hash <= self.finger_table.get('0').get('hash'):

                                            self.logger.info(f'Discovery: Hash {t_hash} is with our successor ({self.hash}, {self.finger_table.get("0").get("hash")}]')

                                            # Our topic belongs with our successor
                                            # Submit register request on our successor node with the successor flag true
                                            self.mw_obj.register(self.finger_table.get("0").get("id"), self.id, address, port, role, topic, True, chain)

                                        else:
                                            # otherwise, calculate highest preceding node
                                            
                                            highest_predecessor = closest_preceding_node(self.hash, t_hash, self.finger_table)
                                            self.logger.info(f'Highest without going over: {highest_predecessor.get("id")}:{highest_predecessor.get("hash")}')
                                            # Submit register request on highest predecessor node
                                            self.mw_obj.register(highest_predecessor.get("id"), self.id, address, port, role, topic, False, chain)

                            #self.mw_obj.verify_registration(identity, True, chain)

                    elif result.get('request_type', 0) == 'register_resp':

                        self.logger.info('Made it to request type register resp logic ')

                        identity = result.get('identity')
                        chain = result.get('chain')
                        success = result.get('register_result')

                        self.mw_obj.verify_registration(identity, success, chain)

                    # Handle is_ready check
                    elif result.get('request_type', 0) == 'is_ready_resp':

                        success = result.get('is_ready_result')
                        identity = result.get('identity')
                        chain = result.get('chain')
                        self.logger.info(f'DiscoveryAppln: Result object of send_is_ready_check: {result} {type(result)}')
                        self.mw_obj.is_ready(identity, success, chain)

                    elif result.get('request_type', 0) == 'is_ready':

                        self.logger.info(f'DiscoveryAppln - System is ready check')
                        identity = result.get('identity', None)
                        
                        if self.lookup == 'Centralized':
                            self.logger.debug(f'DiscoveryAppln::driver - {len(self.publishers)}/{self.num_publishers} pubs and {len(self.subscribers)}/{self.num_subscribers} subs')

                            if self.dissemination == 'Direct':
                                if len(self.publishers) < self.num_publishers or len(self.subscribers) < self.num_subscribers:
                                    self.mw_obj.is_ready(identity, False)
                                else:
                                    self.mw_obj.is_ready(identity, True)
                            else:
                                if self.broker:
                                    self.logger.debug(f'DiscoveryAppln::driver - Broker is here')
                                else:
                                    self.logger.debug(f'DiscoveryAppln::driver - Broker is NOT here')
                                if len(self.publishers) < self.num_publishers or len(self.subscribers) < self.num_subscribers or self.broker == None:
                                    self.mw_obj.is_ready(identity, False)
                                else:
                                    self.mw_obj.is_ready(identity, True)
                        else:
                            # DHT is_ready - need to loop around the ring and count up everyone

                            # Check if the request had any previously tallied pubs, subs, or the broker
                            pubs = result.get('num_pubs', 0) + self.pub_count
                            subs = result.get('num_subs', 0) + self.sub_count
                            broker = result.get('broker', 0)
                            initiator = result.get('initiator', 0)
                            chain = result.get('chain', [])
                            is_ready = True

                            # Check if our successor is the initiatior
                            if initiator == self.finger_table.get("0").get("id"):
                                # Check if total number of pubs and subs is correct
                                # or
                                # for broker check if broker is here too
                                self.logger.info(f'DiscoveryAppln - Reached final DHT node (initiator {initiator} is next)')
                                self.logger.info(f'DiscoveryAppln: {pubs}/{self.num_publishers} pubs and {subs}/{self.num_subscribers} subs')

                                if pubs != self.num_publishers or subs != self.num_subscribers:
                                    is_ready = False

                                if self.dissemination == 'Broker':
                                    if broker != 1 and self.broker == None:
                                        self.logger.info(f'DiscoveryAppln: Broker is NOT here')
                                        is_ready = False
                                    else:
                                        self.logger.info(f'DiscoveryAppln: Broker is here')

                                self.logger.info(f'DiscoveryAppln: Result of ready check: {is_ready}')
                                chain.append(identity.hex())
                                self.mw_obj.is_ready(identity, is_ready, chain)

                            else:
                                # Send the is_ready request to our successor with our own tallies
                                total_broker = broker
                                if self.broker:
                                    total_broker = 1

                                if not initiator:
                                    initiator = self.id

                                # Send request to successor with that info (include initiator)
                                # TODO: Not blocking
                                chain.append(identity.hex())
                                self.mw_obj.send_is_ready_check(self.finger_table.get("0").get("id"), pubs, subs, total_broker, initiator, chain, self.id)

                    elif result.get('request_type', 0) == 'lookup_resp':

                        identity = result.get('identity')
                        chain = result.get('chain')
                        pub_addresses = result.get('pub_addresses')

                        self.logger.info(f'DiscoveryAppln: Sending all addresses: {list(set(pub_addresses))}')
                        self.mw_obj.lookup_response(identity, list(set(pub_addresses)), chain)

                    # Result of type lookup
                    elif result.get('request_type', 0) == 'lookup':
                        sub_topics = set(result.get('topicList'))
                        pub_addresses = []
                        successor = result.get('successor', False)
                        identity = result.get('identity', None)
                        chain = result.get('chain', [])

                        self.logger.info(f'Discovery Lookup Request: length of chain: {len(chain)}, self.lookup: {self.lookup}, self.dissemination: {self.dissemination}')
                        if len(chain) <= 1 and self.lookup == 'DHT' and self.dissemination != 'Direct':
                            # We are the first DHT node to see this request
                            # have the nodes find only the broker instead of the rest of their topic publishers
                            sub_topics = ["b"]

                        chain.append(identity.hex())

                        if self.lookup == 'Centralized':
                            if self.dissemination == 'Direct':
                                self.logger.debug(f'DiscoveryAppln::driver - Looking up publishers by topics: {sub_topics}')

                                for pub in self.publishers.values():
                                    pub_topics = set(pub.get('topicList'))
                                    if sub_topics.intersection(pub_topics):
                                        pub_addresses.append(f'{pub.get("address")}:{pub.get("port")}')

                                self.logger.debug(f'DiscoveryAppln::driver - Matched the following publishers: {pub_addresses}')
                            else:
                                pub_addresses.append(f'{self.broker.get("address")}:{self.broker.get("port")}')
                                self.logger.debug(f'DiscoveryAppln::driver - Sending broker address: {pub_addresses}')

                            self.logger.info(f'DiscoveryAppln: Sending all addresses: {list(set(pub_addresses))}')
                            self.mw_obj.lookup_response(identity, list(set(pub_addresses)))
                            
                        else:

                            # DHT logic
                            for topic in sub_topics:

                                if successor and topic not in self.publishers.keys():
                                    # No one is publishing this specific topic
                                    self.logger.info(f'DiscoveryAppln: We are supposed to have topic {topic} but no publishers are publishing.')
                                    self.logger.info(f'DiscoveryAppln: Sending all addresses: {list(set(pub_addresses))}')
                                    self.mw_obj.lookup_response(identity, list(set(pub_addresses)), chain)
                                    pass
                                else:
                                    # Check if we have it
                                    if topic in self.publishers.keys():
                                        for pub in self.publishers.get(topic):
                                            pub_addresses.append(f"{pub.get('address')}:{pub.get('port')}")
                                        self.logger.info(f'DiscoveryAppln: Sending all addresses: {list(set(pub_addresses))}')
                                        self.mw_obj.lookup_response(identity, list(set(pub_addresses)), chain)
                                    else:
                                        # Get hash value of topic
                                        t_hash = hash_func(topic) % (2**8)

                                        # Check if the value is between our hash and our successor hash
                                        if t_hash > self.hash and t_hash <= self.finger_table.get('0').get('hash'):

                                            self.logger.info(f'Discovery: Hash {t_hash} is with our successor ({self.hash}, {self.finger_table.get("0").get("hash")}]')

                                            # Our topic belongs with our successor
                                            # Submit register request on our successor node with the successor flag true
                                            # TODO: Make non blocking
                                            self.mw_obj.lookup_request(self.finger_table.get("0").get("id"), topic, True, chain, self.id)
                                            # self.logger.info(f'DiscoveryAppln: Received result addresses from lookup request: {addresses}')
                                            # for address in addresses:
                                            #     pub_addresses.append(address)

                                        else:
                                            # otherwise, calculate highest preceding node
                                            highest_predecessor = closest_preceding_node(self.hash, t_hash, self.finger_table)
                                            self.logger.info(f'Highest without going over: {highest_predecessor.get("id")}:{highest_predecessor.get("hash")}')
                                            # Submit register request on highest predecessor node
                                            # TODO: Make non blocking
                                            self.mw_obj.lookup_request(highest_predecessor.get("id"), topic, False, chain, self.id)
                                            # self.logger.info(f'DiscoveryAppln: Received result addresses from lookup request: {addresses}')
                                            # for address in addresses:
                                            #     pub_addresses.append(address)
                    # Result of type lookup all pubs
                    elif result.get('request_type', 0) == 'lookup_all_pubs':
                        
                        pub_addresses = []
                        self.logger.debug(f'DiscoveryAppln::driver - Looking up all publishers')

                        if self.lookup == 'Centralized':
                            for pub in self.publishers.values():
                                pub_addresses.append(f'{pub.get("address")}:{pub.get("port")}')

                            self.logger.debug(f'DiscoveryAppln::driver - List of all publishers: {pub_addresses}')


                            final_addresses = set()
                            for address in pub_addresses:
                                if address:
                                    final_addresses.add(address)

                            self.mw_obj.lookup_response(identity, list(final_addresses), all=True)

                        else:
                            # DHT is_ready - need to loop around the ring and count up everyone

                            # Check if the request had any previously tallied pubs, subs, or the broker
                            pubs = result.get('pubs', 0)

                            self.logger.info(f'Current pubs: {pubs}')

                            if pubs:
                                for pub in pubs:
                                    pub_addresses.append(pub)

                            for topic, pub_list in self.publishers.items():
                                for pub in pub_list:
                                    if topic != "b":
                                        pub_addresses.append(f'{pub.get("address")}:{pub.get("port")}')

                            identity = result.get('identity')
                            initiator = result.get('initiator', 0)
                            chain = result.get('chain', [])
                            chain.append(identity.hex())

                            # Check if our successor is the initiatior
                            if initiator == self.finger_table.get("0").get("id"):
                                # Check if total number of pubs and subs is correct
                                # or
                                # for broker check if broker is here too
                                self.logger.info(f'DiscoveryAppln - Reached final DHT node for lookup all pubs (initiator {initiator} is next)')

                                final_addresses = set()
                                for address in pub_addresses:
                                    if address:
                                        final_addresses.add(address)

                                self.mw_obj.lookup_response(identity, list(final_addresses), chain, all=True)


                            else:
                                # Send the lookup all pubs request to our successor with our own tallies
                                if not initiator:
                                    initiator = self.id

                                # Send request to successor with that info (include initiator)
                                self.logger.info(f'DiscoveryAppln - Creating new lookup_all_pubs request with current addresses: {pub_addresses} from {initiator}')
                                self.mw_obj.lookup_all_pubs(self.finger_table.get("0").get("id"), pub_addresses, initiator, chain)

                else:
                    self.mw_obj.verify_registration(False)

                    self.logger.debug(
                        f'DiscoveryAppln::driver - no new events')

        except Exception as e:
            raise e

    ########################################
    # dump the contents of the object
    ########################################
    def dump(self):
        ''' Pretty print '''

        try:
            self.logger.debug("**********************************")
            self.logger.debug("DiscoveryAppln::dump")
            self.logger.debug("------------------------------")
            self.logger.debug(f'    Publishers: {self.num_publishers}')
            self.logger.debug(f'    Subscribers: {self.num_subscribers}')
            self.logger.debug("**********************************")

        except Exception as e:
            raise e


def parseCmdLineArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', required=False, type=str, help='the name of this discovery service node ex. disc11')
    parser.add_argument('-p', '--publishers', required=True,
                        type=int, help='number of publishers in the system')
    parser.add_argument('-s', '--subscribers', required=True,
                        type=int, help='number of subscribers in the system')
    parser.add_argument('--port', required=True,
                        type=int, help='the port of the discovery service')
    parser.add_argument('-j', '--json', required=False, type=str, help='the path to a json file with DHT information')

    parser.add_argument('-c', '--config', default="config.ini", help='the location of the configuration file')

    return parser.parse_args()

###################################
#
# Main program
#
###################################


def main():
    # obtain a system wide logger and initialize it to debug level to begin with
    logging.debug(
        "Main - acquire a child logger and then log messages in the child")
    logger = logging.getLogger("DiscoveryAppln")

    # first parse the arguments
    logger.debug("Main: parse command line arguments")
    args = parseCmdLineArgs()

    # display configuration from args
    logger.debug(
        f'Main: Creating Discovery Application with {args.publishers} publishers and {args.subscribers} subscribers')

    # Obtain a publisher application
    logger.debug("Main: obtain the object")
    disc_app = DiscoveryAppln(logger)

    # configure the object
    disc_app.configure(args)

    # now invoke the driver program
    disc_app.driver()


###################################
#
# Main entry point
#
###################################
if __name__ == "__main__":

    # set underlying default logging capabilities
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    main()
