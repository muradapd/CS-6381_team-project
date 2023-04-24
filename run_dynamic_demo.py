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
    cmd_str = "python3 ./Visualization/DHT_visualization.py -j Visualization/dynamic.json -i Visualization/commands.txt -d 700"
    subprocess.run(cmd_str, shell=True)

def run_demo_experiment():
    net = Mininet(topo=SingleSwitchTopo(10))
    net.start()
    host_index = 1
    for host in net.hosts:
        if host_index == 1: host.sendCmd(f'{RUN_DISCOVERY} -a 10.0.0.1 -p 5555 -kn 10.0.0.1:5555 -np 2 -ns 2 -l 20 {PIPE_OUTPUT}disc_1.txt'); time.sleep(1)
        elif host_index == 2: host.sendCmd(f'{RUN_DISCOVERY} -a 10.0.0.2 -p 5555 -kn 10.0.0.1:5555 -np 2 -ns 2 -l 20 {PIPE_OUTPUT}disc_2.txt'); time.sleep(1)
        elif host_index == 3: host.sendCmd(f'{RUN_DISCOVERY} -a 10.0.0.3 -p 5555 -kn 10.0.0.2:5555 -np 2 -ns 2 -l 20 {PIPE_OUTPUT}disc_3.txt'); time.sleep(1)
        elif host_index == 4: host.sendCmd(f'{RUN_DISCOVERY} -a 10.0.0.4 -p 5555 -kn 10.0.0.3:5555 -np 2 -ns 2 -l 20 {PIPE_OUTPUT}disc_4.txt'); time.sleep(1)
        elif host_index == 5: host.sendCmd(f'{RUN_DISCOVERY} -a 10.0.0.5 -p 5555 -kn 10.0.0.1:5555 -np 2 -ns 2 -l 20 {PIPE_OUTPUT}disc_5.txt'); time.sleep(1)
        elif host_index == 6: host.sendCmd(f'{RUN_DISCOVERY} -a 10.0.0.6 -p 5555 -kn 10.0.0.4:5555 -np 2 -ns 2 -l 20 {PIPE_OUTPUT}disc_6.txt'); time.sleep(1)
        elif host_index == 7: host.sendCmd(f'{RUN_PUBLISHER} -n pub1 -a 10.0.0.7 -p 5566 -d 10.0.0.1:5555 -l 20 {PIPE_OUTPUT}pub_1.txt'); time.sleep(1)
        elif host_index == 8: host.sendCmd(f'{RUN_PUBLISHER}  -n pub2 -a 10.0.0.8 -p 5566 -d 10.0.0.2:5555 -l 20 {PIPE_OUTPUT}pub_2.txt'); time.sleep(1)
        elif host_index == 9: host.sendCmd(f'{RUN_SUBSCRIBER}  -n sub1 -a 10.0.0.9 -p 5577 -d 10.0.0.3:5555 -l 20 {PIPE_OUTPUT}sub_1.txt'); time.sleep(1)
        elif host_index == 10: host.sendCmd(f'{RUN_SUBSCRIBER}  -n sub2 -a 10.0.0.10 -p 5577 -d 10.0.0.4:5555 -l 20 {PIPE_OUTPUT}sub_2.txt'); time.sleep(1)
        host_index += 1
    time.sleep(30)
    for host in net.hosts: host.stop()
    subprocess.run("sudo mn -c", shell=True)

if __name__ == '__main__':
    # Start the vizualization (which also shows the nodes joining)
    vis_thread = Thread(target = start_visualization)
    vis_thread.start()
    # Run the demo mininet experiment
    exp_thread = Thread(target = run_demo_experiment)
    exp_thread.start()
    vis_thread.join()
    exp_thread.join()