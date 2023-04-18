h1 python3 DiscoveryAppln.py -p 4 -s 4 --port 5000 -c config.ini > mininet_logs/direct/discovery.out 2>&1 &
h2 python3 PublisherAppln.py -a 10.0.0.2 -d 10.0.0.1:5000 --iters 10 -t 5 -n pub1 > mininet_logs/direct/pub1.out 2>&1 &
h3 python3 PublisherAppln.py -a 10.0.0.3 -d 10.0.0.1:5000 --iters 10 -t 5 -n pub2 > mininet_logs/direct/pub2.out 2>&1 &
h4 python3 PublisherAppln.py -a 10.0.0.4 -d 10.0.0.1:5000 --iters 10 -t 5 -n pub3 > mininet_logs/direct/pub3.out 2>&1 &
h5 python3 PublisherAppln.py -a 10.0.0.5 -d 10.0.0.1:5000 --iters 10 -t 5 -n pub4 > mininet_logs/direct/pub4.out 2>&1 &
h6 python3 SubscriberAppln.py -a 10.0.0.6 -d 10.0.0.1:5000 -t 5 -o mininet_logs/direct/latencies/sub1.out -n sub1 > mininet_logs/direct/sub1.out 2>&1 &
h7 python3 SubscriberAppln.py -a 10.0.0.7 -d 10.0.0.1:5000 -t 5 -o mininet_logs/direct/latencies/sub2.out -n sub2 > mininet_logs/direct/sub2.out 2>&1 &
h8 python3 SubscriberAppln.py -a 10.0.0.8 -d 10.0.0.1:5000 -t 5 -o mininet_logs/direct/latencies/sub3.out -n sub3 > mininet_logs/direct/sub3.out 2>&1 &
h9 python3 SubscriberAppln.py -a 10.0.0.9 -d 10.0.0.1:5000 -t 5 -o mininet_logs/direct/latencies/sub4.out -n sub4 > mininet_logs/direct/sub4.out 2>&1 &