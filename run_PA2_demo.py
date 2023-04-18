import subprocess, time
from mininet.net import Mininet
from mininet.topo import SingleSwitchTopo
from threading import Thread

RUN_PUBLISHER = 'python3 Apps/Publisher/application.py'
RUN_SUBSCRIBER = 'python3 Apps/Subscriber/application.py'
RUN_DISCOVERY = 'python3 Apps/Discovery/application.py'
RUN_BROKER = 'python3 Apps/Broker/application.py'
PIPE_OUTPUT = '2>&1 | tee Logs/'

def start_visualization():
    cmd_str = "python3 ./PA2_DEMO/DHT_logic/DHT_visualization.py -j ./PA2_DEMO/dht_vis_experiment.json -i ./PA2_DEMO/commands.txt -d 300"
    subprocess.run(cmd_str, shell=True)

def run_demo_experiment():
    cmd_str = "sudo mn --topo=single,21 --pre=./PA2_DEMO/experiment_scripts/dht_vis_experiment.sh"
    subprocess.run(cmd_str, shell=True)

if __name__ == '__main__':
    # Start the vizualization (which also shows the nodes joining)
    vis_thread = Thread(target = start_visualization)
    vis_thread.start()
    # Run the demo mininet experiment
    exp_thread = Thread(target = run_demo_experiment)
    exp_thread.start()
    vis_thread.join()
    exp_thread.join()