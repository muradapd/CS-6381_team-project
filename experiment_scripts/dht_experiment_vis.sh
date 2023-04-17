h19 python3 DiscoveryAppln.py -n disc1 -j dht.json --port 5556 -p 2 -s 2 > dht_test/disc12.out 2>&1 &
h5 python3 DiscoveryAppln.py -n disc2 -j dht.json --port 5555 -p 2 -s 2 > dht_test/disc3.out 2>&1 &
h7 python3 DiscoveryAppln.py -n disc3 -j dht.json --port 5555 -p 2 -s 2 > dht_test/disc2.out 2>&1 &
h7 python3 DiscoveryAppln.py -n disc4 -j dht.json --port 5556 -p 2 -s 2 > dht_test/disc4.out 2>&1 &
h18 python3 DiscoveryAppln.py -n disc5 -j dht.json --port 5555 -p 2 -s 2 > dht_test/disc6.out 2>&1 &
h8 python3 DiscoveryAppln.py -n disc6 -j dht.json --port 5555 -p 2 -s 2 > dht_test/disc14.out 2>&1 &
h4 python3 DiscoveryAppln.py -n disc7 -j dht.json --port 5555 -p 2 -s 2 > dht_test/disc16.out 2>&1 &
h9 python3 DiscoveryAppln.py -n disc8 -j dht.json --port 5555 -p 2 -s 2 > dht_test/disc5.out 2>&1 &
h3 python3 PublisherAppln.py -n pub1 -d 10.0.0.5:5555 -a 10.0.0.3 -p 7777 -t 5 -i 10 > dht_test/pub1.out 2>&1 &
h4 python3 PublisherAppln.py -n pub2 -d 10.0.0.2:5555 -a 10.0.0.4 -p 7776 -t 5 -i 10 > dht_test/pub2.out 2>&1 &
h6 python3 SubscriberAppln.py -n sub1 -d 10.0.0.8:5555 -a 10.0.0.6 -t 3 > dht_test/sub1.out 2>&1 &
h1 python3 SubscriberAppln.py -n sub2 -d 10.0.0.9:5555 -a 10.0.0.1 -t 3 > dht_test/sub2.out 2>&1 &