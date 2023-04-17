###############################################
#
# Author: John Gordley
# Professor: Aniruddha Gokhale
# Vanderbilt University
#
# Simple Discovery Application that can handle pubs/subs entering and leaving
#
# Created: Spring 2023
#
###############################################

import argparse
import time
import logging
import configparser
import atexit
import json
import sys

# Now import our CS6381 Middleware
from CS6381_MW.ActiveDiscoveryMW import DiscoveryMW

##################################
#       DiscoveryAppln class
##################################

class DiscoveryAppln ():

    ########################################
    # constructor
    ########################################
    def __init__(self, logger):
        self.broker = None
        # storage array for publishers
        self.publishers = dict()
        # storage array for subscribers
        self.subscribers = dict()
        self.dissemination = None  # direct or via broker
        self.mw_obj = None  # handle to the underlying Middleware object
        self.logger = logger  # internal logger for print statements
        self.name = None

    ########################################
    # configure/initialize
    ########################################
    def configure(self, args):
        ''' Initialize the object '''

        self.name = args.name
        self.logger.info(f"DiscoveryAppln: Configuring {self.name}")
        config = configparser.ConfigParser()
        config.read(args.config)
        self.lookup = config["Discovery"]["Strategy"]
        self.dissemination = config["Dissemination"]["Strategy"]

        # Now setup up our underlying middleware object to which we delegate
        self.mw_obj = DiscoveryMW(self.logger)

        # pass remainder of the args to the m/w object
        self.mw_obj.configure(args)

        # Register atexit
        atexit.register(self.mw_obj.clean_exit)

    ########################################
    # driver program
    ########################################
    def driver(self):
        ''' Driver program '''

        try:
            self.logger.debug("DiscoveryAppln::driver")

            # dump our contents (debugging purposes)
            self.dump()

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

                        self.logger.info(f"DiscoveryAppln: Registering new {role} with id {id}")

                        if role == "publisher":
                            self.publishers[id] = {'topicList': topiclist, 'address': address, 'port': port}
                        elif role == "subscriber":
                            # Handle registration from subscriber
                            self.subscribers[id] = topiclist
                        else:
                            self.logger.info('DiscoveryAppln: the broker is here!')
                            self.broker = {'address': address, 'port': port}
                            self.mw_obj.update_broker(f'{address}:{port}')

                        self.mw_obj.verify_registration(identity, True)
                        self.mw_obj.update_pubs(self.publishers)

                    # Result of type lookup
                    elif result.get('request_type', 0) == 'lookup':
                        sub_topics = set(result.get('topicList'))
                        pub_addresses = []
                        identity = result.get('identity', None)

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
                            
                    # Result of type lookup all pubs
                    elif result.get('request_type', 0) == 'lookup_all_pubs':
                        
                        pub_addresses = []
                        self.logger.debug(f'DiscoveryAppln::driver - Looking up all publishers')

                        for pub in self.publishers.values():
                            pub_addresses.append(f'{pub.get("address")}:{pub.get("port")}')

                        self.logger.debug(f'DiscoveryAppln::driver - List of all publishers: {pub_addresses}')


                        final_addresses = set()
                        for address in pub_addresses:
                            if address:
                                final_addresses.add(address)

                        self.logger.info(f"DiscoveryAppln: Sending back all pubs list: {list(final_addresses)}")

                        self.mw_obj.lookup_response(identity, list(final_addresses), all=True)

                    elif result.get('request_type', 0) == 'exit':
                        role = result.get("role")
                        id = result.get("id")
                        address = result.get("address")

                        if role == "publisher":
                            self.logger.info(f"DiscoveryAppln: Publisher {id} left.")
                            self.logger.info(f'DiscoveryAppln: publishers: {self.publishers}')
                            self.publishers.pop(f'{id}:{address}')
                            self.mw_obj.update_pubs(self.publishers)

                        elif role == "subscriber":
                            self.logger.info(f"DiscoveryAppln: Subscriber {id} left.")
                            if len(self.subscribers) > 0:
                                self.subscribers.pop(id)

                        else:
                            self.logger.info(f"DiscoveryAppln: The Broker {id} left.")
                            self.broker = None
                            self.mw_obj.update_broker('')
                    
                    elif result.get('request_type', 0) == 'leader':

                        # Set new publisher info
                        self.publishers = result.get('pub_info')
                        broker = result.get('broker')
                        if broker:
                            broker = broker.split(':')
                            self.broker = {'address': broker[0], 'port': broker[1]}
                            self.mw_obj.update_broker(result.get('broker'))
                        self.mw_obj.update_pubs(self.publishers)

                else:
                    self.mw_obj.verify_registration(False)

                    self.logger.debug(f'DiscoveryAppln::driver - no new events')

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
            self.logger.debug("**********************************")

        except Exception as e:
            raise e


def parseCmdLineArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', required=True, type=str, help='the name of this discovery service node ex. disc11')
    parser.add_argument('--address', required=True, type=str, help='our own address to be sent to Zookeeper')
    parser.add_argument('--port', required=True, type=int, help='the port of the discovery service')
    parser.add_argument('-c', '--config', default="config.ini", help='the location of the configuration file')
    parser.add_argument ("-a", "--zkIPAddr", default="127.0.0.1", help="ZooKeeper server ip address, default 127.0.0.1")
    parser.add_argument ("-p", "--zkPort", type=int, default=2181, help="ZooKeeper server port, default 2181")

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
