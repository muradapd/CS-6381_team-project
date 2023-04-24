# Network Node Visualization

A simple script to visualize requests/responses between nodes in a distributed hash table implementation as described in the [MIT Chord Algorithm Paper](https://pdos.csail.mit.edu/papers/chord:sigcomm01/chord_sigcomm.pdf).

![tkinter vis screenshot](/images/dht_vis_screenshot.png?raw=true "tkinter Visualization")

## Installation

Clone the repo and install the necessary requirements from `requirements.txt` using [pip](https://pypi.org/project/pip/) or your preferred package manager.

```bash
git clone [repo here]
cd [repo here]

pip install -r requirements.txt
```

## Usage

### Setup
There are two parts to implementing this visualization:
* `DHT_visualization.py` - the [tkinter](https://docs.python.org/3/library/tkinter.html) visualization itself to display the network
* `DHT_vis_util.py` - contains function to write commands to the visualization

While `DHT_visualization.py` is running it will be looking at the file specified by the `-i` flag. Any program that imports and uses the `write_vis_command()` function from `DHT_vis_util.py` can write commands to that file that will be shown in sequential order in the tkinter visualization. A diagram of this logic is shown below:

![tkinter vis diagram](/images/dht_vis_diagram.png?raw=true "Logic Breakdown")

### Importing the command logic
This is to be done in files such as a DiscoveryNode, Subscriber, or Publisher. When the actor performs a request/response, they will need to write this command to a shared file to be picked up by the DHT Tkinter Visualization. Writing an example register request is shown below:
```python
from DHT_vis_util import write_vis_command

def lookup_request(target):
    # Start lookup logic
    # ...
    # End lookup logic

    # Writing a register request to shared commands.txt file
    write_vis_command('commands.txt', 'request', source_id, target_id, 'register')
```

### Parameter explanation

`DHT_visualization.py`
* `-j` - the file path of the input json file that describes the DHT (note: this DHT json must have format { id1: {'hash': hashval}, id2 {'hash': hashval}, ...}). An example json is shown in the repo under `dht_example.json`. 
* `-i` - the file path of the input file from which commands are pulled (ex. `commands.txt`)
* `-d` - the time delay between command animations in milliseconds

### Testing with Command Util
The file `DHT_commands_tool.py` provides a CLI for writing test commands to the visualization. You can quit the CLI by using the `quit` command. Otherwise, commands should follow the format shown below in the commands specification. Here is an example usage that draws a register request:

```bash
$ python .\DHT_commands_tool.py -i commands.txt
DHT vis> request-disc1-lookup-disc2
DHT vis> quit
```

## Command Format 
The command writing format is taken care of by the write_vis_command() function that takes in:
* `infile` - the name of the shared file (ex. commands.txt)
* `cmd_type` - the type of the command can either be request, response, or configure
* `source` - the string id of the source node
* `destination` - the string id of the destination node for the request 
* `command` - the string label of the command, could be any string (ex. 'lookup')

If you are using the `DHT_commands_tool.py` CLI, you must write commands in the following format separated by dashes: 
```bash
cmd_type-source-command-destination
```

For example:
```bash
response-disc1-isready-disc2
```

To configure a new pub or sub the following command structure must be used:
```bash
configure-id-id-actor_type
```
Where `actor_type` is either publisher or subscriber. For example in the CLI:

```bash
configure-pub1-publisher-pub1
```

or with the imported python code from `DHT_vis_util`:

```python
write_vis_command('commands.txt', 'configure', 'sub1', 'sub1', 'subscriber')
```

## License

[MIT](https://choosealicense.com/licenses/mit/)