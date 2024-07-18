#ifndef VM_H
#define VM_H

#include "worksheet.h"

enum opcode_num {
    OPCODE_STORE = 0,
    OPCODE_ADD,
    OPCODE_SUB,
    OPCODE_MUL,
    OPCODE_DIV,
    OPCODE_AND,
    OPCODE_OR,
    OPCODE_XOR,
    OPCODE_ABS,
    OPCODE_COUNTA,
    OPCODE_MIN,
    OPCODE_MAX,
    OPCODE_AVG,

    OPCODE_LEN,
    OPCODE_CONCAT,
    OPCODE_JOIN,
    OPCODE_TRIM,
    OPCODE_LOWER,
    OPCODE_UPPER
};

enum value_type {
    VALUE_TYPE_RAW = 0,
    VALUE_TYPE_REF_IMM,
    VALUE_TYPE_REF_RANGE
};

typedef struct store_data {
    union {
        struct imm_type {
            unsigned int blob_idx;
        } imm;
        struct range_type {
            unsigned char x_start, y_start, x_end, y_end;
        } range;
    } data;
} store_data_t;

typedef struct value {
    unsigned char type;
    union {
        struct raw_type raw;
        struct store_data ref;
    } data;
} value_t;

struct __attribute__((packed)) opcode {
    unsigned char op;
    unsigned short n_params;
};

#define STACK_SZ (sizeof(value_t) * 0x100000)
extern value_t *g_stack_ptr;
extern value_t *g_stack_start;

extern unsigned int g_code_sz;
extern unsigned char *g_code_ptr;
extern unsigned char *g_code_start;

extern unsigned int g_blob_sz;
extern struct raw_type *g_blob;

void pop_val(value_t *out);
void push_val(value_t *arg);
void handle_store(unsigned short n_params, unsigned char *st);
void handle_add(unsigned short n_params);
void handle_sub();
void handle_mul(unsigned short n_params);
void handle_div();
void handle_and(unsigned short n_params);
void handle_or(unsigned short n_params);
void handle_xor(unsigned short n_params);
void handle_abs();
void handle_counta(unsigned short n_params);
void handle_min(unsigned short n_params);
void handle_max(unsigned short n_params);
void handle_avg(unsigned short n_params);
void handle_len();
void handle_concat(unsigned short n_params);
void handle_join(unsigned short n_params);
void handle_trim();
void handle_lower();
void handle_upper();
void vm(value_t *result);

#endif