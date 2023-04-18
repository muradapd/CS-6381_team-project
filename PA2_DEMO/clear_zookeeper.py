import argparse
from kazoo.client import KazooClient

# parse the command line
parser = argparse.ArgumentParser ()

parser.add_argument ("-a", "--zkIPAddr", default="127.0.0.1", help="ZooKeeper server ip address, default 127.0.0.1")
parser.add_argument ("-z", "--zNode", required=True, type=str, help="Path to the znode to delete")
parser.add_argument ("-p", "--zkPort", type=int, default=2181, help="ZooKeeper server port, default 2181")

args = parser.parse_args ()

print(f'Attempting to delete {args.zNode} from Zookeeper at {args.zkIPAddr}:{args.zkPort}')

zk = KazooClient (f'{args.zkIPAddr}:{str(args.zkPort)}')

zk.start()

zk.delete(args.zNode, recursive=True)

zk.stop()
zk.close()

print(f'Successfully deleted {args.zNode} from Zookeeper at {args.zkIPAddr}:{args.zkPort}')