###############################################
#
# Author: John Gordley
# Professor: Aniruddha Gokhale
# Vanderbilt University
#
# Simple Broker application that works with dynamic subs/pubs
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
import atexit

from CS6381_MW.ActiveBrokerMW import BrokerMW

class BrokerAppln ():

    ########################################
    # constructor
    ########################################
    def __init__(self, logger):
        self.name = None  # our name (some unique name)
        self.lookup = None  # one of the diff ways we do lookup
        self.dissemination = None  # direct or via broker
        self.mw_obj = None  # handle to the underlying Middleware object
        self.logger = logger  # internal logger for print statements

    ########################################
    # configure/initialize
    ########################################
    def configure(self, args):
        ''' Initialize the object '''

        try:

            # initialize our variables
            self.name = args.name  # our name
            config = configparser.ConfigParser()
            config.read(args.config)
            self.lookup = config["Discovery"]["Strategy"]
            self.dissemination = config["Dissemination"]["Strategy"]

            self.mw_obj = BrokerMW(self.logger)
            self.mw_obj.configure(args)

            atexit.register(self.mw_obj.clean_exit, self.name)

            
        except Exception as e:
            raise e

    ########################################
    # driver program
    ########################################
    def driver(self):
        ''' Driver program '''

        try:

            result = self.mw_obj.register(self.name)
            self.logger.info(f"BrokerAppln - Result of registration: {result}")

            # Perform a lookup request to find the publishers to connect to
            pub_addresses = self.mw_obj.lookup_all_pubs()

            while len(pub_addresses) == 0:
                self.logger.info("BrokerAppln::driver - No publishers for our topics found. Checking again...")
                time.sleep(1)
                pub_addresses = self.mw_obj.lookup_all_pubs()

            self.logger.info(f"BrokerAppln::driver - Found the following publishers: {pub_addresses}")

            # Tell MW to connect to publishers
            self.mw_obj.connect_pubs(pub_addresses)

            # Now begin listening to publishes
            while True:
                result = self.mw_obj.event_loop()
                self.logger.debug(f"BrokerAppln - Received {result}")
                self.mw_obj.disseminate(result[0], result[1])

        except Exception as e:
            raise e

def parseCmdLineArgs():
    # instantiate a ArgumentParser object
    parser = argparse.ArgumentParser(description="Broker Application")

    # Now specify all the optional arguments we support
    # At a minimum, you will need a way to specify the IP and port of the lookup
    # service, the role we are playing, what dissemination approach are we
    # using, what is our endpoint (i.e., port where we are going to bind at the
    # ZMQ level)

    parser.add_argument("-n", "--name", default="pub",
                        help="Some name assigned to us. Keep it unique per Broker")

    parser.add_argument("-a", "--addr", default="localhost",
                        help="IP addr of this Broker to advertise (default: localhost)")

    parser.add_argument("-p", "--port", default="5577",
                        help="Port number on which our underlying Broker ZMQ service runs, default=5577")

    parser.add_argument("-d", "--discovery", default="localhost:5555",
                        help="IP Addr:Port combo for the discovery service, default localhost:5555")

    parser.add_argument("-c", "--config", default="config.ini",
                        help="configuration file (default: config.ini)")

    parser.add_argument("-l", "--loglevel", type=int, default=logging.INFO, choices=[
                        logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL], help="logging level, choices 10,20,30,40,50: default 10=logging.DEBUG")

    return parser.parse_args()

def main():
    # obtain a system wide logger and initialize it to debug level to begin with
    logging.debug("Main - acquire a child logger and then log messages in the child")
    logger = logging.getLogger("BrokerAppln")

    # first parse the arguments
    logger.debug("Main: parse command line arguments")
    args = parseCmdLineArgs()

    # reset the log level to as specified
    logger.debug("Main: resetting log level to {}".format(args.loglevel))
    logger.setLevel(args.loglevel)
    logger.debug("Main: effective log level is {}".format(
        logger.getEffectiveLevel()))

    # Obtain a Broker application
    sub_app = BrokerAppln(logger)

    # configure the object
    sub_app.configure(args)

    # now invoke the driver program
    sub_app.driver()

    return

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
