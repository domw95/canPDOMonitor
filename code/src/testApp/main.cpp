#include <iostream>
#include "socket.h"

int main()  // int argc, char const *argv[])
{
  connections::Socket socket = connections::Socket();
  socket.setupSocket();
  socket.startSocket();
  // connections::Cli;ent client = connections::Client();
  return 0;
}
