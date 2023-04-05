###############################################
# Author: Patrick Muradaz
# Vanderbilt University
# Purpose: File for testing PAs in mininet
# Semester: Spring 2023
###############################################
#
# I recommend running this file using the following command: 
# clear && sudo mn -c && clear && sudo python3 run_mininet_test.py
#
# import statements
import sys, os; sys.path.append(os.getcwd())
import time, configparser
from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.topo import SingleSwitchTopo

RUN_PUBLISHER = 'python3 Apps/Publisher/application.py'
RUN_SUBSCRIBER = 'python3 Apps/Subscriber/application.py'
RUN_DISCOVERY = 'python3 Apps/Discovery/application.py'
RUN_BROKER = 'python3 Apps/Broker/application.py'
PIPE_OUTPUT = 'tbd...'

# Get the configuration object
config = configparser.ConfigParser()
config.read('Apps/Common/config.ini')
LOOKUP = config["Discovery"]["Strategy"]
DISSEMINATION = config["Dissemination"]["Strategy"]
if DISSEMINATION == "Direct" and LOOKUP == "Distributed": PIPE_OUTPUT = '2>&1 | tee logs/Direct_Distrib/'
elif DISSEMINATION == "Broker" and LOOKUP == "Distributed": PIPE_OUTPUT = '2>&1 | tee logs/Broker_Distrib/'
elif DISSEMINATION == "Direct" and LOOKUP == "Centralized": PIPE_OUTPUT = '2>&1 | tee logs/Direct_Central/'
elif DISSEMINATION == "Broker" and LOOKUP == "Centralized": PIPE_OUTPUT = '2>&1 | tee logs/Broker_Central/'

# Define our experiment types as functions
def run_direct_distrib_experiment():
    net = Mininet(topo=SingleSwitchTopo(10))
    net.start()
    host_index = 1
    for host in net.hosts:
        if host_index == 1: host.sendCmd(f'{RUN_DISCOVERY} -a 10.0.0.1 -p 5555 -kn 10.0.0.1:5555 -np 3 -ns 3 -l 20 {PIPE_OUTPUT}disc_1.txt'); time.sleep(1)
        elif host_index == 2: host.sendCmd(f'{RUN_DISCOVERY} -a 10.0.0.2 -p 5555 -kn 10.0.0.1:5555 -np 3 -ns 3 -l 20 {PIPE_OUTPUT}disc_2.txt'); time.sleep(1)
        elif host_index == 3: host.sendCmd(f'{RUN_DISCOVERY} -a 10.0.0.3 -p 5555 -kn 10.0.0.2:5555 -np 3 -ns 3 -l 20 {PIPE_OUTPUT}disc_3.txt'); time.sleep(1)
        elif host_index == 4: host.sendCmd(f'{RUN_DISCOVERY} -a 10.0.0.4 -p 5555 -kn 10.0.0.3:5555 -np 3 -ns 3 -l 20 {PIPE_OUTPUT}disc_4.txt'); time.sleep(1)
        elif host_index == 5: host.sendCmd(f'{RUN_PUBLISHER} -n pub1 -a 10.0.0.5 -p 5566 -d 10.0.0.1:5555 -i 5 -l 20 {PIPE_OUTPUT}pub_1.txt'); time.sleep(1)
        elif host_index == 6: host.sendCmd(f'{RUN_PUBLISHER}  -n pub2 -a 10.0.0.6 -p 5566 -d 10.0.0.2:5555 -i 5 -l 20 {PIPE_OUTPUT}pub_2.txt'); time.sleep(1)
        elif host_index == 7: host.sendCmd(f'{RUN_PUBLISHER}  -n pub3 -a 10.0.0.7 -p 5566 -d 10.0.0.3:5555 -i 5 -l 20 {PIPE_OUTPUT}pub_3.txt'); time.sleep(1)
        elif host_index == 8: host.sendCmd(f'{RUN_SUBSCRIBER}  -n sub1 -a 10.0.0.8 -p 5577 -d 10.0.0.2:5555 -l 20 {PIPE_OUTPUT}sub_1.txt'); time.sleep(1)
        elif host_index == 9: host.sendCmd(f'{RUN_SUBSCRIBER}  -n sub2 -a 10.0.0.9 -p 5577 -d 10.0.0.3:5555 -l 20 {PIPE_OUTPUT}sub_2.txt'); time.sleep(1)
        elif host_index == 10: host.sendCmd(f'{RUN_SUBSCRIBER}  -n sub3 -a 10.0.0.10 -p 5577 -d 10.0.0.4:5555 -l 20 {PIPE_OUTPUT}sub_3.txt'); time.sleep(1)
        host_index += 1
    time.sleep(20)
    net.stop()

def run_broker_distrib_experiment():
    net = Mininet(topo=SingleSwitchTopo(11))
    net.start()
    host_index = 1
    for host in net.hosts:
        if host_index == 1: host.sendCmd(f'{RUN_DISCOVERY} -a 10.0.0.1 -p 5555 -kn 10.0.0.1:5555 -np 3 -ns 3 -l 20 {PIPE_OUTPUT}disc_1.txt'); time.sleep(1)
        elif host_index == 2: host.sendCmd(f'{RUN_DISCOVERY} -a 10.0.0.2 -p 5555 -kn 10.0.0.1:5555 -np 3 -ns 3 -l 20 {PIPE_OUTPUT}disc_2.txt'); time.sleep(1)
        elif host_index == 3: host.sendCmd(f'{RUN_DISCOVERY} -a 10.0.0.3 -p 5555 -kn 10.0.0.2:5555 -np 3 -ns 3 -l 20 {PIPE_OUTPUT}disc_3.txt'); time.sleep(1)
        elif host_index == 4: host.sendCmd(f'{RUN_DISCOVERY} -a 10.0.0.4 -p 5555 -kn 10.0.0.3:5555 -np 3 -ns 3 -l 20 {PIPE_OUTPUT}disc_4.txt'); time.sleep(1)
        elif host_index == 5: host.sendCmd(f'{RUN_BROKER} -a 10.0.0.5 -d 10.0.0.4:5555 -l 20 {PIPE_OUTPUT}broker.txt'); time.sleep(1)
        elif host_index == 6: host.sendCmd(f'{RUN_PUBLISHER} -n pub1 -a 10.0.0.6 -p 5566 -d 10.0.0.1:5555 -i 5 -l 20 {PIPE_OUTPUT}pub_1.txt'); time.sleep(1)
        elif host_index == 7: host.sendCmd(f'{RUN_PUBLISHER}  -n pub2 -a 10.0.0.7 -p 5566 -d 10.0.0.2:5555 -i 5 -l 20 {PIPE_OUTPUT}pub_2.txt'); time.sleep(1)
        elif host_index == 8: host.sendCmd(f'{RUN_PUBLISHER}  -n pub3 -a 10.0.0.8 -p 5566 -d 10.0.0.3:5555 -i 5 -l 20 {PIPE_OUTPUT}pub_3.txt'); time.sleep(1)
        elif host_index == 9: host.sendCmd(f'{RUN_SUBSCRIBER}  -n sub1 -a 10.0.0.9 -p 5577 -d 10.0.0.2:5555 -l 20 {PIPE_OUTPUT}sub_1.txt'); time.sleep(1)
        elif host_index == 10: host.sendCmd(f'{RUN_SUBSCRIBER}  -n sub2 -a 10.0.0.10 -p 5577 -d 10.0.0.3:5555 -l 20 {PIPE_OUTPUT}sub_2.txt'); time.sleep(1)
        elif host_index == 11: host.sendCmd(f'{RUN_SUBSCRIBER}  -n sub3 -a 10.0.0.11 -p 5577 -d 10.0.0.4:5555 -l 20 {PIPE_OUTPUT}sub_3.txt'); time.sleep(1)
        host_index += 1
    time.sleep(22)
    net.stop()

def run_direct_central_experiment():
    net = Mininet(topo=SingleSwitchTopo(7))
    net.start()
    host_index = 1
    for host in net.hosts:
        if host_index == 1: host.sendCmd(f'{RUN_DISCOVERY} -a 10.0.0.1 -p 5555 -np 3 -ns 3 -l 20 {PIPE_OUTPUT}disc_1.txt'); time.sleep(1)
        elif host_index == 2: host.sendCmd(f'{RUN_PUBLISHER} -n pub1 -a 10.0.0.2 -p 5566 -d 10.0.0.1:5555 -i 5 -l 20 {PIPE_OUTPUT}pub_1.txt'); time.sleep(1)
        elif host_index == 3: host.sendCmd(f'{RUN_PUBLISHER}  -n pub2 -a 10.0.0.3 -p 5566 -d 10.0.0.1:5555 -i 5 -l 20 {PIPE_OUTPUT}pub_2.txt'); time.sleep(1)
        elif host_index == 4: host.sendCmd(f'{RUN_PUBLISHER}  -n pub3 -a 10.0.0.4 -p 5566 -d 10.0.0.1:5555 -i 5 -l 20 {PIPE_OUTPUT}pub_3.txt'); time.sleep(1)
        elif host_index == 5: host.sendCmd(f'{RUN_SUBSCRIBER}  -n sub1 -a 10.0.0.5 -p 5577 -d 10.0.0.1:5555 -l 20 {PIPE_OUTPUT}sub_1.txt'); time.sleep(1)
        elif host_index == 6: host.sendCmd(f'{RUN_SUBSCRIBER}  -n sub2 -a 10.0.0.6 -p 5577 -d 10.0.0.1:5555 -l 20 {PIPE_OUTPUT}sub_2.txt'); time.sleep(1)
        elif host_index == 7: host.sendCmd(f'{RUN_SUBSCRIBER}  -n sub3 -a 10.0.0.7 -p 5577 -d 10.0.0.1:5555 -l 20 {PIPE_OUTPUT}sub_3.txt'); time.sleep(1)
        host_index += 1
    time.sleep(15)
    net.stop()

def run_broker_central_experiment():
    net = Mininet(topo=SingleSwitchTopo(8))
    net.start()
    host_index = 1
    for host in net.hosts:
        if host_index == 1: host.sendCmd(f'{RUN_DISCOVERY} -a 10.0.0.1 -p 5555 -np 3 -ns 3 -l 20 {PIPE_OUTPUT}disc_1.txt'); time.sleep(1)
        elif host_index == 2: host.sendCmd(f'{RUN_BROKER} -a 10.0.0.2 -d 10.0.0.1:5555 -l 20 {PIPE_OUTPUT}broker.txt'); time.sleep(1)
        elif host_index == 3: host.sendCmd(f'{RUN_PUBLISHER} -n pub1 -a 10.0.0.3 -p 5566 -d 10.0.0.1:5555 -i 5 -l 20 {PIPE_OUTPUT}pub_1.txt'); time.sleep(1)
        elif host_index == 4: host.sendCmd(f'{RUN_PUBLISHER}  -n pub2 -a 10.0.0.4 -p 5566 -d 10.0.0.1:5555 -i 5 -l 20 {PIPE_OUTPUT}pub_2.txt'); time.sleep(1)
        elif host_index == 5: host.sendCmd(f'{RUN_PUBLISHER}  -n pub3 -a 10.0.0.5 -p 5566 -d 10.0.0.1:5555 -i 5 -l 20 {PIPE_OUTPUT}pub_3.txt'); time.sleep(1)
        elif host_index == 6: host.sendCmd(f'{RUN_SUBSCRIBER}  -n sub1 -a 10.0.0.6 -p 5577 -d 10.0.0.1:5555 -l 20 {PIPE_OUTPUT}sub_1.txt'); time.sleep(1)
        elif host_index == 7: host.sendCmd(f'{RUN_SUBSCRIBER}  -n sub2 -a 10.0.0.7 -p 5577 -d 10.0.0.1:5555 -l 20 {PIPE_OUTPUT}sub_2.txt'); time.sleep(1)
        elif host_index == 8: host.sendCmd(f'{RUN_SUBSCRIBER}  -n sub3 -a 10.0.0.8 -p 5577 -d 10.0.0.1:5555 -l 20 {PIPE_OUTPUT}sub_3.txt'); time.sleep(1)
        host_index += 1
    time.sleep(15)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    if DISSEMINATION == "Direct" and LOOKUP == "Distributed": run_direct_distrib_experiment()
    elif DISSEMINATION == "Broker" and LOOKUP == "Distributed": run_broker_distrib_experiment()
    elif DISSEMINATION == "Direct" and LOOKUP == "Centralized": run_direct_central_experiment()
    elif DISSEMINATION == "Broker" and LOOKUP == "Centralized": run_broker_central_experiment()
