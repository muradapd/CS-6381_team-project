###############################################
#
# Author: Aniruddha Gokhale
# Vanderbilt University
#
# Purpose: Skeleton/Starter code for the subscriber application
#
# Created: Spring 2023
#
###############################################


# This is left as an exercise to the student. Design the logic in a manner similar
# to the PublisherAppln. As in the publisher application, the subscriber application
# will maintain a handle to the underlying subscriber middleware object.
#
# The key steps for the subscriber application are
# (1) parse command line and configure application level parameters
# (2) obtain the subscriber middleware object and configure it.
# (3) As in the publisher, register ourselves with the discovery service
# (4) since we are a subscriber, we need to ask the discovery service to
# let us know of each publisher that publishes the topic of interest to us. Then
# our middleware object will connect its SUB socket to all these publishers
# for the Direct strategy else connect just to the broker.
# (5) Subscriber will always be in an event loop waiting for some matching
# publication to show up. We also compute the latency for dissemination and
# store all these time series data in some database for later analytics.

# import the needed packages
import os     # for OS functions
import sys    # for syspath and system exception
import time   # for sleep
import argparse  # for argument parsing
import configparser  # for configuration parsing
import logging  # for logging. Use it in place of print statements.
import random  # needed in the topic selection using random numbers

from datetime import datetime


# Import our topic selector. Feel free to use alternate way to
# get your topics of interest
from topic_selector import TopicSelector

# Now import our CS6381 Middleware
from CS6381_MW.SubscriberMW import SubscriberMW

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

            register_start = int(round(time.time() * 1000))

            # First ask our middleware to register ourselves with the discovery service
            self.logger.info(f"SubscriberAppln - Attempting to register with Discovery service")
            self.logger.debug(
                "SubscriberAppln::driver - register with the discovery service")
            result = self.mw_obj.register(self.name, self.topicList)
            self.logger.debug(
                "SubscriberAppln::driver - result of registration".format(result))
            self.logger.info(f"SubscriberAppln - Result of registration: {result}")

            register_end = int(round(time.time() * 1000))
            register_time = register_end - register_start

            register_fname = f'stats/{self.name}_{self.lookup}_register.csv'
            with open(register_fname, 'a') as file:
                file.write(f'{register_time}\n')
            

            # Now keep checking with the discovery service if we are ready to go
            self.logger.debug(
                "SubscriberAppln::driver - check if are ready to go")

            is_ready_start = int(round(time.time() * 1000))

            while (not self.mw_obj.is_ready()):
                self.logger.info(f"SubscriberAppln - Sending is_ready request")

                # sleep between calls so that we don't make excessive calls
                time.sleep(5)
                self.logger.debug(
                    "SubscriberAppln::driver - check again if are ready to go")
            
            is_ready_end = int(round(time.time() * 1000))
            is_ready_time = is_ready_end - is_ready_start

            is_ready_fname = f'stats/{self.name}_{self.lookup}_isready.csv'
            with open(is_ready_fname, 'a') as file:
                file.write(f'{is_ready_time}\n')

            # TODO: Write reg_time_ms and is_ready_time_ms to a file

            self.logger.info(f"SubscriberAppln - System is ready!")

            # We broke out so we are ready to go
            self.logger.debug(
                "SubscriberAppln::driver - Received True from Discovery Service ready check")

            # Perform a lookup request to find the publishers to connect to
            self.logger.info(f"SubscriberAppln - Looking up publishers for: {self.topicList}")

            pub_addressses = []
            lookup_fname = f'stats/{self.name}_{self.lookup}_lookup.csv'

            for topic in self.topicList:

                lookup_start = int(round(time.time() * 1000))

                new_addresses = self.mw_obj.lookup([topic])

                lookup_end = int(round(time.time() * 1000))
                lookup_time = lookup_end - lookup_start

                with open(lookup_fname, 'a') as file:
                    file.write(f'{lookup_time}\n')
                
                for address in new_addresses:
                    pub_addressses.append(address)

            pub_addressses = list(set(pub_addressses))

            # pub_addressses = self.mw_obj.lookup(self.topicList)
            # while len(pub_addressses) == 0:
            #     self.logger.debug(
            #         "SubscriberAppln::driver - No publishers for our topics found. Checking again...")
            #     time.sleep(5)
            #     pub_addressses = self.mw_obj.lookup(self.topicList)

            # Tell MW to connect to publishers
            self.logger.info(f"SubscriberAppln - Connecting to publishers: {pub_addressses}")
            self.mw_obj.connect_pubs(pub_addressses, self.topicList)

            self.logger.debug(
                "SubscriberAppln::driver - Listening for publishes of interest")

            # Now begin listening to publishes
            while True:
                result = self.mw_obj.event_loop()
                self.logger.debug(f"SubscriberAppln::driver - Received {result}")
                
                latency = str(datetime.now() - datetime.strptime(result.timestamp, "%m/%d/%Y, %H:%M:%S.%f"))
                self.logger.info(f"SubscriberAppln - (latency: {latency.split(':')[-1]}) Received {result}")
                
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

###################################
#
# Parse command line arguments
#
###################################


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


###################################
#
# Main entry point
#
###################################
if __name__ == "__main__":

    # set underlying default logging capabilities
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    main()
