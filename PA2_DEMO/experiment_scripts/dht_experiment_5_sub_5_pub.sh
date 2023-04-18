h2 python3 DiscoveryAppln.py -n disc12 -j dht.json --port 5555 -p 5 -s 5 > dht_test/disc12.out 2>&1 &
h5 python3 DiscoveryAppln.py -n disc3 -j dht.json --port 5555 -p 5 -s 5 > dht_test/disc3.out 2>&1 &
h7 python3 DiscoveryAppln.py -n disc2 -j dht.json --port 5555 -p 5 -s 5 > dht_test/disc2.out 2>&1 &
h7 python3 DiscoveryAppln.py -n disc4 -j dht.json --port 5556 -p 5 -s 5 > dht_test/disc4.out 2>&1 &
h7 python3 DiscoveryAppln.py -n disc6 -j dht.json --port 5557 -p 5 -s 5 > dht_test/disc6.out 2>&1 &
h8 python3 DiscoveryAppln.py -n disc14 -j dht.json --port 5555 -p 5 -s 5 > dht_test/disc14.out 2>&1 &
h8 python3 DiscoveryAppln.py -n disc16 -j dht.json --port 5556 -p 5 -s 5 > dht_test/disc16.out 2>&1 &
h9 python3 DiscoveryAppln.py -n disc5 -j dht.json --port 5555 -p 5 -s 5 > dht_test/disc5.out 2>&1 &
h10 python3 DiscoveryAppln.py -n disc7 -j dht.json --port 5555 -p 5 -s 5 > dht_test/disc7.out 2>&1 &
h10 python3 DiscoveryAppln.py -n disc17 -j dht.json --port 5556 -p 5 -s 5 > dht_test/disc17.out 2>&1 &
h11 python3 DiscoveryAppln.py -n disc13 -j dht.json --port 5555 -p 5 -s 5 > dht_test/disc13.out 2>&1 &
h12 python3 DiscoveryAppln.py -n disc9 -j dht.json --port 5555 -p 5 -s 5 > dht_test/disc9.out 2>&1 &
h12 python3 DiscoveryAppln.py -n disc10 -j dht.json --port 5556 -p 5 -s 5 > dht_test/disc10.out 2>&1 &
h13 python3 DiscoveryAppln.py -n disc1 -j dht.json --port 5555 -p 5 -s 5 > dht_test/disc1.out 2>&1 &
h13 python3 DiscoveryAppln.py -n disc18 -j dht.json --port 5556 -p 5 -s 5 > dht_test/disc18.out 2>&1 &
h13 python3 DiscoveryAppln.py -n disc20 -j dht.json --port 5557 -p 5 -s 5 > dht_test/disc20.out 2>&1 &
h15 python3 DiscoveryAppln.py -n disc15 -j dht.json --port 5555 -p 5 -s 5 > dht_test/disc15.out 2>&1 &
h15 python3 DiscoveryAppln.py -n disc19 -j dht.json --port 5556 -p 5 -s 5 > dht_test/disc19.out 2>&1 &
h18 python3 DiscoveryAppln.py -n disc11 -j dht.json --port 5555 -p 5 -s 5 > dht_test/disc11.out 2>&1 &
h19 python3 DiscoveryAppln.py -n disc8 -j dht.json --port 5555 -p 5 -s 5 > dht_test/disc8.out 2>&1 &
h1 python3 SubscriberAppln.py -n sub1 -d 10.0.0.13:5555 -a 10.0.0.1 -t 3 > dht_test/sub1.out 2>&1 &
h3 python3 SubscriberAppln.py -n sub2 -d 10.0.0.11:5555 -a 10.0.0.3 -t 3 > dht_test/sub2.out 2>&1 &
h4 python3 SubscriberAppln.py -n sub3 -d 10.0.0.7:5557 -a 10.0.0.4 -t 3 > dht_test/sub3.out 2>&1 &
h4 python3 SubscriberAppln.py -n sub4 -d 10.0.0.7:5555 -a 10.0.0.4 -t 3 > dht_test/sub4.out 2>&1 &
h14 python3 SubscriberAppln.py -n sub5 -d 10.0.0.13:5555 -a 10.0.0.14 -t 3 > dht_test/sub5.out 2>&1 &
h20 python3 PublisherAppln.py -n pub1 -d 10.0.0.2:5555 -a 10.0.0.20 -p 7777 -t 5 -i 10 > dht_test/pub1.out 2>&1 &
h21 python3 PublisherAppln.py -n pub2 -d 10.0.0.8:5555 -a 10.0.0.21 -p 7777 -t 5 -i 10 > dht_test/pub2.out 2>&1 &
h22 python3 PublisherAppln.py -n pub3 -d 10.0.0.8:5556 -a 10.0.0.22 -p 7777 -t 5 -i 10 > dht_test/pub3.out 2>&1 &
h23 python3 PublisherAppln.py -n pub4 -d 10.0.0.11:5555 -a 10.0.0.23 -p 7777 -t 5 -i 10 > dht_test/pub4.out 2>&1 &
h24 python3 PublisherAppln.py -n pub5 -d 10.0.0.9:5555 -a 10.0.0.24 -p 7777 -t 5 -i 10 > dht_test/pub5.out 2>&1 &