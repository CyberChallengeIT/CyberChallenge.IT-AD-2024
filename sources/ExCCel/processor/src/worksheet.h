#ifndef WORKSHEET_H
#define WORKSHEET_H

#define CELL_DATA_SZ (64ul)
struct raw_type {
    unsigned char len;
    unsigned char pad1[7]; // Unused
    char data[CELL_DATA_SZ];
    unsigned long pad2; // Unused
};

#define WORKSHEET_ID_SZ (32ul)
#define WORKSHEET_DIM (64ul)
#define COORD(x, y) ((x) * WORKSHEET_DIM + (y))
extern struct raw_type g_worksheet[WORKSHEET_DIM*WORKSHEET_DIM];

void parse_worksheet(char *worksheet_id);

#endif