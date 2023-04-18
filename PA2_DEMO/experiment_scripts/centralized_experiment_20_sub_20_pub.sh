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
h12 python3 SubscriberAppln.py -n sub6 -d 10.0.0.1:5555 -a 10.0.0.12 -t 3 > centralized_test/sub1.out 2>&1 &
h13 python3 SubscriberAppln.py -n sub7 -d 10.0.0.1:5555 -a 10.0.0.13 -t 3 > centralized_test/sub2.out 2>&1 &
h14 python3 SubscriberAppln.py -n sub8 -d 10.0.0.1:5555 -a 10.0.0.14 -t 3 > centralized_test/sub3.out 2>&1 &
h15 python3 SubscriberAppln.py -n sub9 -d 10.0.0.1:5555 -a 10.0.0.15 -t 3 > centralized_test/sub4.out 2>&1 &
h16 python3 SubscriberAppln.py -n sub10 -d 10.0.0.1:5555 -a 10.0.0.16 -t 3 > centralized_test/sub5.out 2>&1 &
h17 python3 SubscriberAppln.py -n sub11 -d 10.0.0.1:5555 -a 10.0.0.17 -t 3 > centralized_test/sub1.out 2>&1 &
h18 python3 SubscriberAppln.py -n sub12 -d 10.0.0.1:5555 -a 10.0.0.18 -t 3 > centralized_test/sub2.out 2>&1 &
h19 python3 SubscriberAppln.py -n sub13 -d 10.0.0.1:5555 -a 10.0.0.19 -t 3 > centralized_test/sub3.out 2>&1 &
h20 python3 SubscriberAppln.py -n sub14 -d 10.0.0.1:5555 -a 10.0.0.20 -t 3 > centralized_test/sub4.out 2>&1 &
h21 python3 SubscriberAppln.py -n sub15 -d 10.0.0.1:5555 -a 10.0.0.21 -t 3 > centralized_test/sub5.out 2>&1 &
h22 python3 SubscriberAppln.py -n sub16 -d 10.0.0.1:5555 -a 10.0.0.22 -t 3 > centralized_test/sub1.out 2>&1 &
h23 python3 SubscriberAppln.py -n sub17 -d 10.0.0.1:5555 -a 10.0.0.23 -t 3 > centralized_test/sub2.out 2>&1 &
h24 python3 SubscriberAppln.py -n sub18 -d 10.0.0.1:5555 -a 10.0.0.24 -t 3 > centralized_test/sub3.out 2>&1 &
h25 python3 SubscriberAppln.py -n sub19 -d 10.0.0.1:5555 -a 10.0.0.25 -t 3 > centralized_test/sub4.out 2>&1 &
h26 python3 SubscriberAppln.py -n sub20 -d 10.0.0.1:5555 -a 10.0.0.26 -t 3 > centralized_test/sub5.out 2>&1 &
h27 python3 PublisherAppln.py -n pub6 -d 10.0.0.1:5555 -a 10.0.0.27 -p 7777 -t 5 -i 10 > centralized_test/pub1.out 2>&1 &
h28 python3 PublisherAppln.py -n pub7 -d 10.0.0.1:5555 -a 10.0.0.28 -p 7777 -t 5 -i 10 > centralized_test/pub2.out 2>&1 &
h29 python3 PublisherAppln.py -n pub8 -d 10.0.0.1:5555 -a 10.0.0.29 -p 7777 -t 5 -i 10 > centralized_test/pub3.out 2>&1 &
h30 python3 PublisherAppln.py -n pub9 -d 10.0.0.1:5555 -a 10.0.0.30 -p 7777 -t 5 -i 10 > centralized_test/pub4.out 2>&1 &
h31 python3 PublisherAppln.py -n pub10 -d 10.0.0.1:5555 -a 10.0.0.31 -p 7777 -t 5 -i 10 > centralized_test/pub5.out 2>&1 &
h32 python3 PublisherAppln.py -n pub11 -d 10.0.0.1:5555 -a 10.0.0.32 -p 7777 -t 5 -i 10 > centralized_test/pub1.out 2>&1 &
h33 python3 PublisherAppln.py -n pub12 -d 10.0.0.1:5555 -a 10.0.0.33 -p 7777 -t 5 -i 10 > centralized_test/pub2.out 2>&1 &
h34 python3 PublisherAppln.py -n pub13 -d 10.0.0.1:5555 -a 10.0.0.34 -p 7777 -t 5 -i 10 > centralized_test/pub3.out 2>&1 &
h35 python3 PublisherAppln.py -n pub14 -d 10.0.0.1:5555 -a 10.0.0.35 -p 7777 -t 5 -i 10 > centralized_test/pub4.out 2>&1 &
h36 python3 PublisherAppln.py -n pub15 -d 10.0.0.1:5555 -a 10.0.0.36 -p 7777 -t 5 -i 10 > centralized_test/pub5.out 2>&1 &
h37 python3 PublisherAppln.py -n pub16 -d 10.0.0.1:5555 -a 10.0.0.37 -p 7777 -t 5 -i 10 > centralized_test/pub1.out 2>&1 &
h38 python3 PublisherAppln.py -n pub17 -d 10.0.0.1:5555 -a 10.0.0.38 -p 7777 -t 5 -i 10 > centralized_test/pub2.out 2>&1 &
h39 python3 PublisherAppln.py -n pub18 -d 10.0.0.1:5555 -a 10.0.0.39 -p 7777 -t 5 -i 10 > centralized_test/pub3.out 2>&1 &
h40 python3 PublisherAppln.py -n pub19 -d 10.0.0.1:5555 -a 10.0.0.40 -p 7777 -t 5 -i 10 > centralized_test/pub4.out 2>&1 &
h41 python3 PublisherAppln.py -n pub20 -d 10.0.0.1:5555 -a 10.0.0.41 -p 7777 -t 5 -i 10 > centralized_test/pub5.out 2>&1 &