h1 python3 DiscoveryAppln.py -n disc3 -j dht_vis_experiment.json --port 5555 -p 2 -s 2 > experiment_scripts/dht_test/disc3.out 2>&1 &
h3 python3 DiscoveryAppln.py -n disc1 -j dht_vis_experiment.json --port 5555 -p 2 -s 2 > experiment_scripts/dht_test/disc1.out 2>&1 &
h3 python3 DiscoveryAppln.py -n disc7 -j dht_vis_experiment.json --port 5556 -p 2 -s 2 > experiment_scripts/dht_test/disc7.out 2>&1 &
h5 python3 DiscoveryAppln.py -n disc4 -j dht_vis_experiment.json --port 5555 -p 2 -s 2 > experiment_scripts/dht_test/disc4.out 2>&1 &
h9 python3 DiscoveryAppln.py -n disc5 -j dht_vis_experiment.json --port 5555 -p 2 -s 2 > experiment_scripts/dht_test/disc5.out 2>&1 &
h10 python3 DiscoveryAppln.py -n disc6 -j dht_vis_experiment.json --port 5555 -p 2 -s 2 > experiment_scripts/dht_test/disc6.out 2>&1 &
h12 python3 DiscoveryAppln.py -n disc2 -j dht_vis_experiment.json --port 5555 -p 2 -s 2 > experiment_scripts/dht_test/disc2.out 2>&1 &
h18 python3 DiscoveryAppln.py -n disc8 -j dht_vis_experiment.json --port 5555 -p 2 -s 2 > experiment_scripts/dht_test/disc8.out 2>&1 &
h3 python3 PublisherAppln.py -n pub1 -d 10.0.0.1:5555 -a 10.0.0.3 --port 7777 -t 5 -i 20 > experiment_scripts/dht_test/pub1.out 2>&1 &
h12 python3 PublisherAppln.py -n pub2 -d 10.0.0.1:5555 -a 10.0.0.12 --port 7777 -t 5 -i 20 > experiment_scripts/dht_test/pub2.out 2>&1 &
h6 python3 SubscriberAppln.py -n sub2 -d 10.0.0.1:5555 -t 9 > experiment_scripts/dht_test/sub2.out 2>&1 &
h13 python3 SubscriberAppln.py -n sub1 -d 10.0.0.1:5555 -t 8 > experiment_scripts/dht_test/sub1.out 2>&1 &