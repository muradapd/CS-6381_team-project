import subprocess
from threading import Thread
from time import sleep

def start_visualization():
    cmd_str = "python3 ./DHT_logic/DHT_visualization.py -j dht_vis_experiment.json -i commands.txt"
    subprocess.run(cmd_str, shell=True)

def run_demo_experiment():
    cmd_str = "sudo mn --topo=single,20 --pre=./experiment_scripts/dht_vis_experiment.sh"
    subprocess.run(cmd_str, shell=True)

def teardown_and_exit():
    cmd_str = 'echo "stop vis"'
    subprocess.run(cmd_str, shell=True)

if __name__ == '__main__':
    # Start the vizualization (which also shows the nodes joining)
    vis_thread = Thread(target = start_visualization)
    vis_thread.start()
    # Run the demo mininet experiment
    exp_thread = Thread(target = run_demo_experiment)
    exp_thread.start()
    # Stop the vizualization which also shows the nodes leaving
    vis_thread.join()
    exp_thread.join()