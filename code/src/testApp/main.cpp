#include <iostream>
#include "socket.h"
// #include "client.h"

int main()  // int argc, char const *argv[])
{
  connections::Socket socket = connections::Socket();
  socket.setupSocket();
  socket.startSocket();
  // connections::Client client = connections::Client();
  return 0;
}
