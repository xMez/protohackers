#include "net.h"

#define LISTEN_BACKLOG 50

int create_socket(unsigned short port, const char* host) {
    int sfd;
    struct sockaddr_in saddr;

    sfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sfd < 0) {
        perror("socket");
        return -1;
    }

    memset(&saddr, 0, sizeof(saddr));
    saddr.sin_family = AF_INET;
    saddr.sin_port = htons(port);
    saddr.sin_addr.s_addr = inet_addr(host);

    if (bind(sfd, (struct sockaddr *) &saddr, sizeof(saddr)) < 0) {
        perror("bind");
        return -1;
    }

    if (listen(sfd, LISTEN_BACKLOG) < 0) {
        perror("listen");
        return -1;
    }

    return sfd;
}
