"""
Classes for hosting a scope as a server and sending data to it
"""
import socket
import json
from threading import Thread, Event
from canPDOMonitor.scope import (ScopeWindow, Scope, app)
from canPDOMonitor.datalog import Datapoint
import time

import logging
import struct

logger = logging.getLogger(__name__)

class Server():
    """
    Main entry point to running the scope server.

    Recieves connections from clients which are then handled by the Connection class
    """
    def __init__(self, host='127.0.0.1', port=6666):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen()
        logger.info("Starting server on port {} on {}".format(self.port, self.host))
        while(True):
            conn, addr = self.socket.accept()
            logger.info("Recieved connection from {}".format(addr))
            connection = Connection(conn, addr)
            connection.start()

class Client():
    """
    Class for opening a connection with a scope server and communicating
    """
    def __init__(self, host='127.0.0.1', port=6666):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.scopes = []

    def add_scope(self, settings):
        """
        Adds a scope to this window with ScopeSettings settings
        """
        self.scopes.append(settings.__dict__)

    def start(self):
        """
        Opens connection and sends the scope window configuration to the server
        """
        self.socket.connect((self.host, self.port))
        msg = json.dumps({"Scopes":self.scopes}).encode()
        self.socket.send(struct.pack('!BH',1,len(msg)+3) + msg)
    
    def add_datapoints(self, datapoints):
        """
        Accepts a list of Datapoints at current timestep and send them to scope
        """
        msg = json.dumps([d.__dict__ for d in datapoints]).encode()
        self.socket.send(struct.pack('!BH',2,len(msg)+3) + msg)
  
class Connection():
    """
    Holds the connection to a client, creates windows with scopes and recieves data
    """
    def __init__(self, socket, address):
        self.socket = socket    # socket for client communication
        self.address = address  # address of client
        self.data = bytearray() # buffer containing data from client

        self.packet_count = 0

        self.window_settings = None
        self.create_window = Event()
        self.create_window.clear()

    def start(self):
        """
        Starts a thread that recieves data from the client and processes it

        Then waits for instruction to create window and run in main thread (cos qt)
        """
        # Start the socket listening thread
        listen_thread = Thread(target=self.listen)
        listen_thread.start()

        monitor_thread = Thread(target=self.monitor)
        monitor_thread.start()
        # wait for the create window flag to be set
        if not self.create_window.wait(5):
            logger.warn("Timeout waiting to recieve scope window settings")
            return
        # if no settings have been added, end
        if self.window_settings is None:
            logger.warn("No settings for scope window")
            return

        # execute the scope window
        logger.info("Creating scope window with {} scope(s)".format(
                        len(self.window_settings["Scopes"])))
        self.window = ScopeWindow()
        for scope in self.window_settings["Scopes"]:
            self.window.add_scope(Scope(**scope))
        self.window.start()
        app.exec_()
        logger.info("QT Execution finished")

    def listen(self):
        """
        Thread to wait for packets to come in and send them to where they need to go
        """
        with self.socket:
            while(True):
                packet = self.next_packet()
                if packet is None:
                    logger.info("Connection with {} closed".format(self.address))
                    return
                self.packet_count += 1
                # logger.debug("Packet Recieved id {} length {}".format(packet.id, packet.length))
                if packet.id == 1:
                    # packet requesting a scope window
                    if self.window_settings is not None:
                        logger.warn("Recieved multiple scope window settings packets")
                        continue
                    self.window_settings = json.loads(packet.data)
                    self.create_window.set()
                if packet.id == 2:
                    # datapoints packet
                    datapoints = json.loads(packet.data)
                    datapoints = [Datapoint(**d) for d in datapoints]
                    self.window.add_datapoints(datapoints)
            else:
                return
    
    def next_packet(self):
        """
        Returns a string containing a whole packet of data from client or None if connection closed
        """
        while(True):
            new_data = self.socket.recv(1024)
            if not len(new_data):
                return None
            else:
                self.data += new_data
                data_length = len(self.data)
                if data_length > 3:
                    # get the id and length of the packet
                    id, length = struct.unpack('!BH',self.data[:3])
                    if data_length >= length:
                        packet = Packet(id, length, self.data[3:length])
                        self.data[:] = self.data[length:]
                        return packet
                    else:
                        continue
                else:
                    continue

    def monitor(self):
        """
        Thread used to print debug info
        """
        while(True):
            print("Packet Count {}".format(self.packet_count))
            time.sleep(2)

class Packet():
    def __init__(self, id, length, data):
        self.id = id
        self.length = length
        self.data = data


if __name__ == "__main__":
    # logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.DEBUG)
    server = Server()
    server.start()