#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <string.h>

#include "util.h"

void setupbuf(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin,  NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
}

void error(const char *msg) {
    unsigned int len;
    unsigned char status;

    // Write status code
    status = 1;
    write(1, &status, sizeof(status));

    // Write msg
    len = strlen(msg);
    write(1, &len, sizeof(len));
    write(1, msg, len);

    _exit(1);
}

void success(const unsigned int sz, const char *result) {
    unsigned char status;
    
    // Write status code
    status = 0;
    write(1, &status, sizeof(status));

    // Write result
    write(1, &sz, sizeof(sz));
    write(1, result, sz);
    
    _exit(0);
}

int check_num(unsigned char sz, const char *str) {
    for (int i = 0; i < sz; i++) {
        if (i == 0 && (str[i] == '-' || str[i] == '+'))
            continue;
        if (str[i] < '0' || str[i] > '9')
            return -1;
    }
    return 0;
}

int read_exactly(int fd, void *buf, size_t size) {
    size_t done = 0;
    while (done != size) {
        size_t count = read(fd, (char *)buf + done, size - done);
        if (count <= 0)
            return -1;
        done += count;
    }
    return 0;
}