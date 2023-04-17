h1 python3 DiscoveryAppln.py -n disc1 --port 5555 -p 1 -s 1 > centralized_test/disc1.out 2>&1 &
h2 python3 SubscriberAppln.py -n sub1 -d 10.0.0.1:5555 -a 10.0.0.2 -t 3 > centralized_test/sub1.out 2>&1 &
h3 python3 SubscriberAppln.py -n sub2 -d 10.0.0.1:5555 -a 10.0.0.3 -t 3 > centralized_test/sub2.out 2>&1 &
h4 python3 SubscriberAppln.py -n sub3 -d 10.0.0.1:5555 -a 10.0.0.4 -t 3 > centralized_test/sub3.out 2>&1 &
h5 python3 SubscriberAppln.py -n sub4 -d 10.0.0.1:5555 -a 10.0.0.5 -t 3 > centralized_test/sub4.out 2>&1 &
h6 python3 SubscriberAppln.py -n sub5 -d 10.0.0.1:5555 -a 10.0.0.6 -t 3 > centralized_test/sub5.out 2>&1 &
h7 python3 PublisherAppln.py -n pub1 -d 10.0.0.1:5555 -a 10.0.0.7 -p 7777 -t 5 -i 10 > centralized_test/pub1.out 2>&1 &
h8 python3 PublisherAppln.py -n pub2 -d 10.0.0.1:5555 -a 10.0.0.8 -p 7777 -t 5 -i 10 > centralized_test/pub2.out 2>&1 &
h9 python3 PublisherAppln.py -n pub3 -d 10.0.0.1:5555 -a 10.0.0.9 -p 7777 -t 5 -i 10 > centralized_test/pub3.out 2>&1 &
h10 python3 PublisherAppln.py -n pub4 -d 10.0.0.1:5555 -a 10.0.0.10 -p 7777 -t 5 -i 10 > centralized_test/pub4.out 2>&1 &
h11 python3 PublisherAppln.py -n pub5 -d 10.0.0.1:5555 -a 10.0.0.11 -p 7777 -t 5 -i 10 > centralized_test/pub5.out 2>&1 &