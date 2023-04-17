import atexit

def print_my_int(i, j):
    print(i, j)

my_int = 30

atexit.register(print_my_int, my_int, my_int*2)

while True:
    my_int += 1