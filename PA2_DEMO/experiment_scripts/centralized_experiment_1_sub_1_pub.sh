h1 python3 DiscoveryAppln.py -n disc1 --port 5555 -p 1 -s 1 > centralized_test/disc1.out 2>&1 &
h2 python3 SubscriberAppln.py -n sub1 -d 10.0.0.1:5555 -a 10.0.0.2 -t 3 > centralized_test/sub1.out 2>&1 &
h3 python3 PublisherAppln.py -n pub1 -d 10.0.0.1:5555 -a 10.0.0.3 -p 7777 -t 5 -i 10 > centralized_test/pub1.out 2>&1 &