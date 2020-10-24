#include <iostream>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <string>
#include <arpa/inet.h>
#include <stdio.h>
#include <string>
#include "socket.h"
#include "rapidjson/stringbuffer.h"
#include "rapidjson/writer.h"
#include <iostream>
#include <regex>

using namespace std;
namespace connections
{
#define SERVER_PORT htons(8888)

Socket::Socket()
{
  serverSock=socket(AF_INET, SOCK_STREAM, 0);
  n=0;
}

void Socket::setupSocket()
{
  serverAddr.sin_family = AF_INET;
  serverAddr.sin_port = SERVER_PORT;
  serverAddr.sin_addr.s_addr = INADDR_ANY;

  /* bind (this socket, local address, address length)
     bind server socket (serverSock) to server address (serverAddr).
     Necessary so that server can use a specific port */
  bind(serverSock, (struct sockaddr*)&serverAddr, sizeof(struct sockaddr));

  // wait for a client
  /* listen (this socket, request queue length) */
  listen(serverSock,1);
  bzero(buffer, 1024);

  {
    sockaddr_in clientAddr;
    socklen_t sin_size=sizeof(struct sockaddr_in);
    int clientSock=accept(serverSock,(struct sockaddr*)&clientAddr, &sin_size);
    // testcode
    rapidjson::Document d;

    // ends
    while (1 == 1)
    {
        //receive a message from a client
        n = read(clientSock, buffer, 500);
        std::string bufferString = buffer;
        bufferString.erase(bufferString.find("}") + 1);
        // std::regex regexMatch("(?<=\})(,)");
        // std::cout << bufferString << std::endl;

        d.Parse(bufferString.c_str());
        // d.SetObject();

        // TODO(jjad) testcode
        rapidjson::StringBuffer strbuffer;
        rapidjson::Writer<rapidjson::StringBuffer> writer(strbuffer);
        d.Accept(writer);
        std::cout << strbuffer.GetString() << std::endl;
        // testCodeEnds
        bzero(buffer, 1024);
    }
  }
}

void Socket::startSocket()
{
  std::thread t1(&connections::Socket::setupSocket, this);
  t1.join();
}

Socket::~Socket()
{
}

}
