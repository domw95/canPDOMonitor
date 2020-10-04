from threading import Thread
from collections import deque
import random
import time

plot_data = deque(maxlen=2000)

data_rate = 1000
active = True

def data_gen_loop():
    start_time = time.time()
    data_count = 0
    while active:
        plot_data.append(random.gauss(0, 1))
        data_count = data_count + 1
        if data_count / (time.time() - start_time):
            time.sleep(0.001)

data_gen = Thread(target=data_gen_loop)
data_gen.start()

for i in range(10):
    time.sleep(1)
    print(plot_data)

active = False
time.sleep(1)
