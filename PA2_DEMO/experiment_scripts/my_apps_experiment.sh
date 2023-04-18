h1 python3 Apps/Discovery/application.py -a 10.0.0.1 -p 5555 -kn 10.0.0.1:5555 -np 3 -ns 3 > experiment_scripts/dht_test/disc1.out 2>&1 &
h2 python3 Apps/Discovery/application.py -a 10.0.0.2 -p 5555 -kn 10.0.0.1:5555 -np 3 -ns 3 > experiment_scripts/dht_test/disc2.out 2>&1 &
h3 python3 Apps/Discovery/application.py -a 10.0.0.3 -p 5555 -kn 10.0.0.2:5555 -np 3 -ns 3 > experiment_scripts/dht_test/disc3.out 2>&1 &
h4 python3 Apps/Discovery/application.py -a 10.0.0.4 -p 5555 -kn 10.0.0.3:5555 -np 3 -ns 3 > experiment_scripts/dht_test/disc4.out 2>&1 &
h5 python3 Apps/Publisher/application.py -n pub1 -a 10.0.0.5 -p 5566 -d 10.0.0.1:5555 > experiment_scripts/dht_test/pub1.out 2>&1 &
h6 python3 Apps/Publisher/application.py -n pub2 -a 10.0.0.6 -p 5566 -d 10.0.0.2:5555 > experiment_scripts/dht_test/pub2.out 2>&1 &
h7 python3 Apps/Subscriber/application.py -n sub1 -a 10.0.0.7 -p 5577 -d 10.0.0.2:5555 > experiment_scripts/dht_test/sub2.out 2>&1 &
h8 python3 Apps/Subscriber/application.py -n sub2 -a 10.0.0.8 -p 5577 -d 10.0.0.3:5555 > experiment_scripts/dht_test/sub1.out 2>&1 &