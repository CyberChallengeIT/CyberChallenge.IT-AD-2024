#ifndef UTIL_H
#define UTIL_H

#include <unistd.h>

void setupbuf(void);
void error(const char *msg);
void success(const unsigned int sz, const char *result);
int check_num(unsigned char sz, const char *str);
int read_exactly(int fd, void *buf, size_t size);

#endif