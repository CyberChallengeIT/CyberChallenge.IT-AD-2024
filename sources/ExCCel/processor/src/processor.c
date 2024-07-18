#define _GNU_SOURCE
#include <err.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#include <unistd.h>
#include <string.h>
#include <limits.h>
#include <assert.h>
#include <sys/mman.h>
#include <stdbool.h>
#include <ctype.h>
#include <time.h>

#include "vm.h"
#include "util.h"
#include "worksheet.h"

int main() {
    unsigned char timestamp_sz;
    long timestamp;
    long curr_timestamp;
    value_t result;
    char worksheet_id[WORKSHEET_ID_SZ + 1];
    char timestamp_str[32];

    memset(&result, 0, sizeof(result));
    memset(&worksheet_id, 0, sizeof(worksheet_id));
    memset(&timestamp_str, 0, sizeof(timestamp_str));

    setupbuf();
    
    // Worksheet id
    read_exactly(0, &worksheet_id, WORKSHEET_ID_SZ);

    // Timestamp, code, blob sizes
    read_exactly(0, &timestamp_sz, sizeof(timestamp_sz));
    read_exactly(0, &g_code_sz, sizeof(g_code_sz));
    read_exactly(0, &g_blob_sz, sizeof(g_blob_sz));
    
    g_code_start = g_code_ptr = calloc(g_code_sz, 1);
    g_blob = calloc(g_blob_sz, 1);

    if (g_code_ptr == NULL || g_blob == NULL)
        errx(1, "calloc failed");

    // Timestamp
    read_exactly(0, &timestamp_str, timestamp_sz);

    timestamp = strtoll(timestamp_str, NULL, 10);
    curr_timestamp = time(NULL) * 1000;
    
    if (labs(curr_timestamp - timestamp) > 30 * 1000)
        error("invalid timestamp");

    // GADGET 2 FOR VULN PWN 3 (hard)
    asm volatile (
        "jmp handle_main;"
        ".byte 0x66;" // -> NOP
        ".byte 0x0F;"
        ".byte 0x1F;"
        ".byte 0x84;" // <- NOP
        ".byte 0x5f;" // pop rdi, rdx, rsi; ret
        ".byte 0x5a;"
        ".byte 0x5e;"
        ".byte 0xc3;"
        ".byte 0x90;"
        "handle_main:"
    );

    // Code and blob
    read_exactly(0, g_code_ptr, g_code_sz);
    read_exactly(0, g_blob, g_blob_sz);

    parse_worksheet(worksheet_id);

    vm(&result);

    success(result.data.raw.len, result.data.raw.data);
}
