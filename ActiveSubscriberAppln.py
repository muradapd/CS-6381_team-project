###############################################
#
# Author: John Gordley
# Professor: Aniruddha Gokhale
# Vanderbilt University
#
# Purpose: Simple subscriber implementation without is ready check
# 
# Created: Spring 2023
#
###############################################

# import the needed packages
import os     # for OS functions
import sys    # for syspath and system exception
import time   # for sleep
import argparse  # for argument parsing
import configparser  # for configuration parsing
import logging  # for logging. Use it in place of print statements.
import random  # needed in the topic selection using random numbers
import atexit # needed to handle exiting cleanly

from datetime import datetime


# Import our topic selector. Feel free to use alternate way to
# get your topics of interest
from topic_selector import TopicSelector

# Now import our CS6381 Middleware
from CS6381_MW.ActiveSubscriberMW import SubscriberMW

# import any other packages you need.

##################################
#       SubscriberAppln class
##################################


class SubscriberAppln ():

    ########################################
    # constructor
    ########################################
    def __init__(self, logger):
        self.name = None  # our name (some unique name)
        self.topicList = None  # the different topics that we publish on
        self.lookup = None  # one of the diff ways we do lookup
        self.dissemination = None  # direct or via broker
        self.mw_obj = None  # handle to the underlying Middleware object
        self.logger = logger  # internal logger for print statements
        self.latencies = []
        self.output = None
        self.num_topics = None # number of topics to select

    ########################################
    # configure/initialize
    ########################################
    def configure(self, args):
        ''' Initialize the object '''

        try:
            # Here we initialize any internal variables
            self.logger.debug("SubscriberAppln::configure")

            # initialize our variables
            self.name = args.name  # our name
            self.output = args.output
            self.num_topics = args.num_topics

            # Now, get the configuration object
            self.logger.debug(
                "SubscriberAppln::configure - parsing config.ini")
            config = configparser.ConfigParser()
            config.read(args.config)
            self.lookup = config["Discovery"]["Strategy"]
            self.dissemination = config["Dissemination"]["Strategy"]

            # Now get our topic list of interest
            self.logger.debug(
                "SubscriberAppln::configure - selecting our topic list")
            ts = TopicSelector()
            self.topicList = ts.interest(self.num_topics)

            # Now setup up our underlying middleware object to which we delegate
            # everything
            self.logger.debug(
                "SubscriberAppln::configure - initialize the middleware object")
            self.mw_obj = SubscriberMW(self.logger)
            # pass remainder of the args to the m/w object
            self.mw_obj.configure(args)

            atexit.register(self.mw_obj.clean_exit, self.name)

            self.logger.debug(
                "SubscriberAppln::configure - configuration complete")
            self.logger.info(f"SubscriberAppln - {self.name} configured with topics: {self.topicList}")

        except Exception as e:
            raise e

    ########################################
    # driver program
    ########################################
    def driver(self):
        ''' Driver program '''

        try:
            self.logger.debug("SubscriberAppln::driver")

            # dump our contents (debugging purposes)
            self.dump()

            time.sleep(random.uniform(1.2, 2.0))

            # First ask our middleware to register ourselves with the discovery service
            self.logger.info(f"SubscriberAppln - Attempting to register with Discovery service")
            self.logger.debug(
                "SubscriberAppln::driver - register with the discovery service")
            result = self.mw_obj.register(self.name, self.topicList)
            self.logger.debug(
                "SubscriberAppln::driver - result of registration".format(result))
            self.logger.info(f"SubscriberAppln - Result of registration: {result}")

            # Perform a lookup request to find the publishers to connect to
            self.logger.info(f"SubscriberAppln - Looking up publishers for: {self.topicList}")

            pub_addressses = []
            lookup_fname = f'stats/{self.name}_{self.lookup}_lookup.csv'

            for topic in self.topicList:

                new_addresses = self.mw_obj.lookup([topic])
                
                for address in new_addresses:
                    pub_addressses.append(address)

            pub_addressses = list(set(pub_addressses))

            # Tell MW to connect to publishers
            self.logger.info(f"SubscriberAppln - Connecting to publishers: {pub_addressses}")
            self.mw_obj.connect_pubs(pub_addressses, self.topicList)

            self.logger.debug(
                "SubscriberAppln::driver - Listening for publishes of interest")

            # Now begin listening to publishes
            while True:
                result = self.mw_obj.event_loop()
                self.logger.info(f"SubscriberAppln::driver - Received {result}")
                
                # latency = str(datetime.now() - datetime.strptime(result.timestamp, "%m/%d/%Y, %H:%M:%S.%f"))
                # self.logger.info(f"SubscriberAppln - (latency: {latency.split(':')[-1]}) Received {result}")
                
        except Exception as e:
            raise e

    ########################################
    # dump the contents of the object
    ########################################
    def dump(self):
        ''' Pretty print '''

        try:
            self.logger.debug("**********************************")
            self.logger.debug("SubscriberAppln::dump")
            self.logger.debug("------------------------------")
            self.logger.debug("     Name: {}".format(self.name))
            self.logger.debug("     Lookup: {}".format(self.lookup))
            self.logger.debug(
                "     Dissemination: {}".format(self.dissemination))
            self.logger.debug("     topicList: {}".format(self.topicList))
            self.logger.debug("**********************************")

        except Exception as e:
            raise e

def parseCmdLineArgs():
    # instantiate a ArgumentParser object
    parser = argparse.ArgumentParser(description="Subscriber Application")

    # Now specify all the optional arguments we support
    # At a minimum, you will need a way to specify the IP and port of the lookup
    # service, the role we are playing, what dissemination approach are we
    # using, what is our endpoint (i.e., port where we are going to bind at the
    # ZMQ level)

    parser.add_argument("-n", "--name", default="pub",
                        help="Some name assigned to us. Keep it unique per Subscriber")

    parser.add_argument("-a", "--addr", default="localhost",
                        help="IP addr of this Subscriber to advertise (default: localhost)")

    parser.add_argument("-p", "--port", default="5577",
                        help="Port number on which our underlying Subscriber ZMQ service runs, default=5577")

    parser.add_argument("-d", "--discovery", default="localhost:5555",
                        help="IP Addr:Port combo for the discovery service, default localhost:5555")

    parser.add_argument("-t", "--num_topics", type=int, choices=range(1,10), default=1, help="number of topics to select")

    parser.add_argument("-c", "--config", default="config.ini",
                        help="configuration file (default: config.ini)")

    parser.add_argument("-l", "--loglevel", type=int, default=logging.INFO, choices=[
                        logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL], help="logging level, choices 10,20,30,40,50: default 10=logging.DEBUG")

    parser.add_argument("-o", "--output", help="output filename to put latencies into")

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
    logger = logging.getLogger("SubAppln")

    # first parse the arguments
    logger.debug("Main: parse command line arguments")
    args = parseCmdLineArgs()

    # reset the log level to as specified
    logger.debug("Main: resetting log level to {}".format(args.loglevel))
    logger.setLevel(args.loglevel)
    logger.debug("Main: effective log level is {}".format(
        logger.getEffectiveLevel()))

    # Obtain a Subscriber application
    logger.debug("Main: obtain the object")
    sub_app = SubscriberAppln(logger)

    # configure the object
    sub_app.configure(args)

    # now invoke the driver program
    sub_app.driver()

if __name__ == "__main__":

    # set underlying default logging capabilities
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    main()