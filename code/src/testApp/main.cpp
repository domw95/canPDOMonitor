#include <iostream>
#include "socket.h"
// #include "client.h"


// TODO(jjad) change name to 'coreWorkflow'
// class to be instansiated by an actual main
// main will take number of signals to plot, how many seconds of data to display

int main()  // int argc, char const *argv[])
{
  connections::Socket socket = connections::Socket();
  socket.setupSocket();
  socket.startSocket();

  // shared pointer up signalStore
  // socket gets pointer to signalStore
  // egress from socket to store

  // plotting /egress class setup and configured here
  // plotting to use store's egress impl
  // get shit out of store, code
  // connections::Client client = connections::Client();
  return 0;
}
