#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <arpa/inet.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>

#define BUF_SIZE 1024
#define LISTEN_BACKLOG 50

#define handle_error(msg) do { perror(msg); exit(EXIT_FAILURE); } while (0)

int main(int argc, char *argv[]) {
    char buf[BUF_SIZE];

    int sfd;
    struct sockaddr_in saddr, caddr;

    unsigned short port = 10005;
    const char *host = "0.0.0.0";

    if ((sfd = socket(AF_INET, SOCK_STREAM, 0)) == -1)
        handle_error("socket");

    memset(&saddr, 0, sizeof(saddr));
    memset(&caddr, 0, sizeof(caddr));
    saddr.sin_family = AF_INET;
    saddr.sin_port = htons(port);
    saddr.sin_addr.s_addr = inet_addr(host);
    caddr.sin_family = AF_INET;
    caddr.sin_port = htons(port);

    if (bind(sfd, (struct sockaddr *) &saddr, sizeof(saddr)) == -1)
        handle_error("bind");

    if (listen(sfd, LISTEN_BACKLOG) == -1)
        handle_error("listen");

    int cfd = accept(sfd, NULL, NULL);
    if (cfd == -1)
        handle_error("accept");

    ssize_t msg;
    while ((msg = recv(cfd, buf, BUF_SIZE - 1, 0)) != 0) {
        if (msg == -1)
            handle_error("recv");
        if (msg == 0)
            break;
        printf("%s\n", buf);
        send(cfd, buf, strlen(buf), 0);
    }
}
