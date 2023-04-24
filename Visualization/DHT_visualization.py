import tkinter as tk
import time
import math
import json
import argparse
from filelock import FileLock

# Gather command line args
parser = argparse.ArgumentParser(description="DHT visualization program")

parser.add_argument('-j', '--json', type=str, required=True, help='The file path of the input json file that describes the DHT')
parser.add_argument('-i', '--infile', type=str, required=True, help='The file path of the input file from which commands are pulled')
parser.add_argument('-d', '--delay', type=int, default=100, help="The time delay between command animations in milliseconds")

args = parser.parse_args()
infile = args.infile
lockfile = args.infile + '.lock'
delay = float(args.delay) / 1000
dht_file = args.json

# Initiate lockfile
lock = FileLock(lockfile)
empty_checks = 0 # the number of times that we check and there are no new commands

node_info = {}
node_topics = {}
subscriber_info = {}
publisher_info = {}
commands_queue = []

# Initiate tkinter
animation_window_width = 800
animation_window_height = 600
animation_refresh_seconds = 0.01

pub_y_increment = animation_window_height / 6
sub_y_increment = animation_window_height / 6
pub_x = 75
sub_x = animation_window_width - 75
radius = 15

# The main window of the animation
window = tk.Tk()
window.title("Tkinter Node Example")
window.geometry(f'{animation_window_width}x{animation_window_height}')

# Create the canvas
canvas = tk.Canvas(window)
canvas.configure(bg="black")
canvas.pack(fill="both", expand=True)

# Read in DHT nodes generated in json
dht_nodes = None
with open(dht_file, 'r') as f:
    dht_nodes = json.load(f)

nodes_list = []
for id, vals in dht_nodes.items():
    nodes_list.append((id, vals.get('hash')))

# nodes_list.sort(key=lambda x: x[1])

def points_on_circle(num_points, radius):
    '''
        Generates a list of equally spaced point positions around a unit circle
    '''

    # Calculate the angle between each point
    angle = 2 * math.pi / num_points

    # Calculate the coordinates of each point
    points = []
    for i in range(num_points):
        x = radius * math.cos(i * angle)
        y = radius * math.sin(i * angle)
        points.append((x, y))

    return points

def midpoint(coord1, coord2):
    '''
        Calculates the midpoint between two coordinates
    '''

    x1, y1 = coord1
    x2, y2 = coord2
    return ((x1 + x2) / 2, (y1 + y2) / 2)

def draw_arrow(source_id, destination_id, label=None, color='white'):
    '''
        Draws an arrow between the source and destination objects in tkinter
        with an optional label in the center of the arrow
    '''

    coords = node_info.get(source_id, 0) or publisher_info.get(source_id, 0) or subscriber_info.get(source_id, 0)
    if not coords:
        print(f'Error: invalid ID {source_id}')
        return
    source_x, source_y = coords

    coords = node_info.get(destination_id, 0) or publisher_info.get(destination_id, 0) or subscriber_info.get(destination_id, 0)
    if not coords:
        print(f'Error: invalid ID {destination_id}')
        return
    des_x, des_y = coords

    line = canvas.create_line(source_x, source_y, des_x, des_y, arrow='last', fill=color)

    if label:
        text_x, text_y = midpoint((source_x, source_y), (des_x, des_y))
        label = canvas.create_text(text_x, text_y, text=label, fill='white')

    # Delete the line after 1 second
    delay = 1500  # milliseconds

    def delete_line():
        canvas.delete(line)
        canvas.delete(label)

    canvas.after(delay, delete_line)

def loop_nodes():
    '''
        Function that draws arrows around all points of the circle
        basically loops around the whole thing
    '''

    for i in range(0, len(nodes_list)):

        source = nodes_list[i][0]
        target = None

        if i == len(nodes_list) - 1:
            target = nodes_list[0][0]
        else:
            target = nodes_list[i+1][0]

        draw_arrow(source, target, 'is_ready')

        window.update()
        time.sleep(0.5)

def draw_dht_nodes(dht_nodes):
    '''
        Takes in the dht_nodes and draws them in tkinter equally spaced around
        a unit circle
    '''

    points = points_on_circle(len(dht_nodes), 200)
    x_origin = animation_window_width/2
    y_origin = animation_window_height/2

    for i in range(len(points)):
        x = x_origin + points[i][0]
        y = y_origin + points[i][1]

        node_info[dht_nodes[i][0]] = (x, y)
        node_topics[dht_nodes[i][0]] = []

        # x1, y1, x2, y2
        canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="blue", outline="white", width=4)
        canvas.create_text(x, y + 25, text=dht_nodes[i][0], fill='white')
        canvas.create_text(x, y + 40, text=dht_nodes[i][1], fill='white')
        time.sleep(delay)
        window.update()

def draw_actor(name, category):
    '''
        Draws either the pub, sub, or broker on the canvas
    '''

    if category == 'publisher':

        num_pubs = len(publisher_info) + 1

        y = num_pubs * pub_y_increment
        publisher_info[name] = (pub_x, y)

        canvas.create_oval(pub_x - radius, y - radius, pub_x + radius, y + radius, fill="orange", outline="white", width=4)
        canvas.create_text(pub_x, y + 25, text=name, fill='white')

    elif category == 'subscriber':
        
        num_subs = len(subscriber_info) + 1

        y = num_subs * sub_y_increment
        subscriber_info[name] = (sub_x, y)

        canvas.create_oval(sub_x - radius, y - radius, sub_x + radius, y + radius, fill="green", outline="white", width=4)
        canvas.create_text(sub_x, y + 25, text=name, fill='white')

    elif category == 'broker':
        pass

def save_topic(source, topic):
    '''
        Adds a topic to a DHT node and draws it underneath the node name
    '''

    source_x, source_y = node_info[source]

    if not topic in node_topics[source]: 
        node_topics[source].append(topic)
        num_topics = len(node_topics[source])

        topic_y = source_y + 30 + 15 * (num_topics + 1)

        canvas.create_text(source_x, topic_y, text=topic, fill='white')
        window.update()
        time.sleep(0.5)


def parse_command(command):
    '''
        Takes commands in the format type-content-...
        Can specify either req/reps or new actors joining

        types can be either request, response, save, or configure:

        request-source-label-target
        response-source-label-target
        save-source-topic
        configure-name-category (pub or sub)
    '''

    splt = command.split('-')
    if splt:
        cmd_type = splt[0]

        if cmd_type == 'request':
            source = splt[1]
            label = splt[2]
            destination = splt[3]
            draw_arrow(source, destination, label)

        elif cmd_type == 'response':
            source = splt[1]
            label = splt[2]
            destination = splt[3]
            draw_arrow(source, destination, label, color='green')

        elif cmd_type == 'save':
            source = splt[1]
            topic = splt[2]

            save_topic(source, topic)

        elif cmd_type == 'configure':

            name = splt[1]
            category = splt[2]
            draw_actor(name, category)

# Generate base DHT nodes
draw_dht_nodes(nodes_list)

# while empty_checks < 300:
while True:
    time.sleep(animation_refresh_seconds)

    # Check the lockfile to see if there are new commands
    with lock:
        with open(infile, "r") as f:
            lines = f.readlines()
            if len(lines) == 0: empty_checks += 1
            else:
                for line in lines:
                    commands_queue.append(line.strip())
                    empty_checks = 0

        # Clear the lockfile
        with open(infile, "w") as f:
            f.write('')

    while commands_queue:
        next = commands_queue.pop(0)
        parse_command(next)

        time.sleep(delay)
        window.update()

    window.update()