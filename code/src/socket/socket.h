#include <stdlib.h>
#include <stdio.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <string>
#include <thread>
#include <pthread.h>

#include "rapidjson/document.h"

namespace connections
{

class Socket
{
  public:
    Socket();
    ~Socket();

    void setupSocket();
    void startSocket();
  private:
    char buffer[1024] = {0};
    // std::thread _socketThread;
    int n;
    sockaddr_in serverAddr;
    int serverSock;
    void createNewSocket();
};


}
