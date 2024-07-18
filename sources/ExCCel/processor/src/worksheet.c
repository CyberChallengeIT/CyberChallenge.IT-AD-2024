#define _GNU_SOURCE
#include <string.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/mman.h>

#include "util.h"
#include "worksheet.h"

struct raw_type g_worksheet[WORKSHEET_DIM*WORKSHEET_DIM];

void parse_worksheet(char *worksheet_id) {
    int fd;
    unsigned short n_elems;
    unsigned char x, y, len;
    char path[256];

    memset(path, 0, sizeof(path));

    memset(g_worksheet, 0, sizeof(g_worksheet));

    snprintf(path, sizeof(path), "/worksheets/%s", basename(worksheet_id));

    fd = open(path, O_RDONLY);
    if (fd < 0)
        error("open failed");

    read_exactly(fd, &n_elems, sizeof(n_elems));

    for (; n_elems > 0; n_elems--) {
        read_exactly(fd, &x, sizeof(x));
        read_exactly(fd, &y, sizeof(y));
        read_exactly(fd, &len, sizeof(len));

        if (x >= WORKSHEET_DIM || y >= WORKSHEET_DIM)
            error("oob coordinates");
        
        if (len > CELL_DATA_SZ)
            error("oob cell sz");

        g_worksheet[COORD(x, y)].len = len;
        read_exactly(fd, &g_worksheet[COORD(x, y)].data, len);
    }
}
