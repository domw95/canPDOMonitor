import threading
import queue
import time
import random


class DaveysScopeServer:
    """
    Python API to whatever hot mess you churn out
    """

    def __init__(self):
        """
        Opens the scope executable (presumably with subprocess.run or
        popen or some shit) which starts the server
        """
        # queue for incoming datapoints
        self.data_queue = queue.Queue()
        # thread for sending data
        self.send_thread = threading.Thread(target=self._send_loop)
        # flag to inidcate status
        self.active = threading.Event()

    def start(self, scope_format=None):
        """
        Sends some command (json) to server that indicates how many scopes,
        which signals to display, number of datapoints, triggermode etc
        Also starts send loop
        """

        # start the send thread
        self.active.set()
        self.send_thread.start()

    def stop(self):
        """
        Sends some sort of command (json) to server that exits everything,
        releasing all the memory that hasnt leaked
        Also quits send loop
        """

        # stop send thread
        self.active.clear()
        if self.send_thread.is_alive():
            self.send_thread.join(timeout=1)
            if self.send_thread.is_alive():
                print("You fucked it")

    def add_datapoints(self, datapoints):
        """
        add  datapoints to a queue, ready to be sent to server
        """
        self.data_queue.put(datapoints)

    def _send_loop(self):
        """
        Loop to be run in a thread that yeets datapoints to server in json
        format
        """
        while(self.active.is_set()):
            # get next set of datapoints
            datapoints = self.data_queue.get(True)

            # INSERT SOCKET SEND SHIT HERE
            print("Send to server:", datapoints[0:2])


def data_gen_loop():
    active.set()
    start_time = time.time()
    data_count = 0
    while active.is_set():
        datapoints = [("Time", data_count*0.001)]
        for i in range(16):
            datapoints.append(("Signal_{}".format(i), random.gauss(10*i, 1)))
        scope_server.add_datapoints(datapoints)
        data_count = data_count + 1
        if (data_count / (time.time() - start_time)) > data_rate:
            time.sleep(0.001)


if __name__ == "__main__":
    # create a scope server and start it
    scope_server = DaveysScopeServer()
    scope_server.start()

    # start random data gen
    data_rate = 1000
    active = threading.Event()
    data_gen = threading.Thread(target=data_gen_loop)
    data_gen.start()

    # wait for 10s
    time.sleep(10)

    # stop server
    scope_server.stop()
    # stop data gen
    active.clear()

