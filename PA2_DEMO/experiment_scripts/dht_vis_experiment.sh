h1 python3 PA2_DEMO/DiscoveryAppln.py -n disc3 -j PA2_DEMO/dht_vis_experiment.json --port 5555 -p 4 -s 2 > PA2_DEMO/experiment_scripts/dht_test/disc3.out 2>&1 &
h3 python3 PA2_DEMO/DiscoveryAppln.py -n disc1 -j PA2_DEMO/dht_vis_experiment.json --port 5555 -p 4 -s 2 > PA2_DEMO/experiment_scripts/dht_test/disc1.out 2>&1 &
h3 python3 PA2_DEMO/DiscoveryAppln.py -n disc7 -j PA2_DEMO/dht_vis_experiment.json --port 5556 -p 4 -s 2 > PA2_DEMO/experiment_scripts/dht_test/disc7.out 2>&1 &
h5 python3 PA2_DEMO/DiscoveryAppln.py -n disc4 -j PA2_DEMO/dht_vis_experiment.json --port 5555 -p 4 -s 2 > PA2_DEMO/experiment_scripts/dht_test/disc4.out 2>&1 &
h9 python3 PA2_DEMO/DiscoveryAppln.py -n disc5 -j PA2_DEMO/dht_vis_experiment.json --port 5555 -p 4 -s 2 > PA2_DEMO/experiment_scripts/dht_test/disc5.out 2>&1 &
h10 python3 PA2_DEMO/DiscoveryAppln.py -n disc6 -j PA2_DEMO/dht_vis_experiment.json --port 5555 -p 4 -s 2 > PA2_DEMO/experiment_scripts/dht_test/disc6.out 2>&1 &
h12 python3 PA2_DEMO/DiscoveryAppln.py -n disc2 -j PA2_DEMO/dht_vis_experiment.json --port 5555 -p 4 -s 2 > PA2_DEMO/experiment_scripts/dht_test/disc2.out 2>&1 &
h18 python3 PA2_DEMO/DiscoveryAppln.py -n disc8 -j PA2_DEMO/dht_vis_experiment.json --port 5555 -p 4 -s 2 > PA2_DEMO/experiment_scripts/dht_test/disc8.out 2>&1 &
h3 python3 PA2_DEMO/PublisherAppln.py -n pub1 -d 10.0.0.1:5555 -a 10.0.0.3 --port 7777 -t 5 -i 20 > PA2_DEMO/experiment_scripts/dht_test/pub1.out 2>&1 &
h12 python3 PA2_DEMO/PublisherAppln.py -n pub2 -d 10.0.0.1:5555 -a 10.0.0.12 --port 7777 -t 5 -i 20 > PA2_DEMO/experiment_scripts/dht_test/pub2.out 2>&1 &
h3 python3 PA2_DEMO/PublisherAppln.py -n pub3 -d 10.0.0.1:5555 -a 10.0.0.3 --port 7778 -t 5 -i 20 > PA2_DEMO/experiment_scripts/dht_test/pub3.out 2>&1 &
h12 python3 PA2_DEMO/PublisherAppln.py -n pub4 -d 10.0.0.1:5555 -a 10.0.0.12 --port 7778 -t 5 -i 20 > PA2_DEMO/experiment_scripts/dht_test/pub4.out 2>&1 &
h6 python3 PA2_DEMO/SubscriberAppln.py -n sub2 -d 10.0.0.1:5555 -t 9 > PA2_DEMO/experiment_scripts/dht_test/sub2.out 2>&1 &
h13 python3 PA2_DEMO/SubscriberAppln.py -n sub1 -d 10.0.0.1:5555 -t 8 > PA2_DEMO/experiment_scripts/dht_test/sub1.out 2>&1 &