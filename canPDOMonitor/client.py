"""Client connecting to port specified. Also parses json so kinda need to rename this"""

import sys
import socket
import json

#TODO(jjad) these will get passed in
HOST, PORT = (localhost, 8888)

class client(HOST, PORT)
  """
  Will open connection to socket created by cpp app in __init__
  Will then accept data from (virtual initially) can, convert to json, and send
  """

  def __init__(self):
    self.host = HOST
    self.port = PORT
    # Create a socket (SOCK_STREAM means a TCP socket)
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
    # Connect to server and send data
    self.sock.connect((HOST, PORT))

  def toJson():
    sock.sendall(jsonObj)
