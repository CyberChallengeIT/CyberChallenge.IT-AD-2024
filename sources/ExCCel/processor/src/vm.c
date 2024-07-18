#define _GNU_SOURCE
#include <fcntl.h>
#include <stdlib.h>
#include <stddef.h>
#include <sys/mman.h>
#include <ctype.h>
#include <string.h>
#include <stdio.h>
#include <limits.h>

#include "vm.h"
#include "util.h"

value_t *g_stack_ptr;
value_t *g_stack_start;

unsigned int g_code_sz;
unsigned char *g_code_ptr;
unsigned char *g_code_start;

unsigned int g_blob_sz;
struct raw_type *g_blob;


void pop_val(value_t *out) {
    if (g_stack_ptr == g_stack_start)
        error("stack underflow");

    memcpy(out, g_stack_ptr, sizeof(*out));
    
    if (out->type == VALUE_TYPE_RAW)
        out->data.raw.pad2 = 0;

    g_stack_ptr--;
    return;
}

void push_val(value_t *arg) {
    if ((g_stack_ptr) + 1 >= g_stack_start + STACK_SZ/sizeof(value_t))
        error("stack overflow");

    g_stack_ptr++;
    memcpy(g_stack_ptr, arg, sizeof(*g_stack_ptr));
}

void handle_store(unsigned short n_params, unsigned char *st) {
    value_t tmp;

    for (unsigned i = 0; i < n_params; i++) {
        tmp.type = *st++;
        tmp.data.ref = *(store_data_t*)st;
        push_val(&tmp);
        st += sizeof(store_data_t);
    }
}

void handle_add(unsigned short n_params) {
    value_t res;
    value_t arg;
    long num;
    long acc = 0;

    memset(&res, 0, sizeof(res));

    for (int i = 0; i < n_params; i++) {
        pop_val(&arg);
        if (check_num(arg.data.raw.len, arg.data.raw.data) != 0)
            error("invalid number");
        num = strtoull(arg.data.raw.data, NULL, 10);
        acc += num;
    }

    snprintf((char*)res.data.raw.data, sizeof(res.data.raw.data), "%ld", acc);
    res.data.raw.len = strnlen((char*)res.data.raw.data, sizeof(res.data.raw.data));

    push_val(&res);
}

void handle_sub() {
    value_t res;
    value_t arg1;
    value_t arg2;
    long num1, num2, sub;
    
    memset(&res, 0, sizeof(res));

    pop_val(&arg1);
    pop_val(&arg2);

    if (check_num(arg1.data.raw.len, arg1.data.raw.data) != 0 || check_num(arg2.data.raw.len, arg2.data.raw.data) != 0)
        error("invalid number");
    
    num1 = strtoull(arg1.data.raw.data, NULL, 10);
    num2 = strtoull(arg2.data.raw.data, NULL, 10);
    sub = num1 - num2;

    snprintf((char*)res.data.raw.data, sizeof(res.data.raw.data), "%ld", sub);
    res.data.raw.len = strnlen((char*)res.data.raw.data, sizeof(res.data.raw.data));

    push_val(&res);
}

void handle_mul(unsigned short n_params) {
    value_t res;
    value_t arg;
    long num;
    long acc = 1;
    
    memset(&res, 0, sizeof(res));

    for (int i = 0; i < n_params; i++) {
        pop_val(&arg);
        if (check_num(arg.data.raw.len, arg.data.raw.data) != 0)
            error("invalid number");
        num = strtoull(arg.data.raw.data, NULL, 10);
        acc *= num;
    }
    snprintf((char*)res.data.raw.data, sizeof(res.data.raw.data), "%ld", acc);
    res.data.raw.len = strnlen((char*)res.data.raw.data, sizeof(res.data.raw.data));

    push_val(&res);
}

void handle_div() {
    value_t res;
    value_t arg1;
    value_t arg2;
    long num1, num2, div;

    memset(&res, 0, sizeof(res));

    pop_val(&arg1);
    pop_val(&arg2);

    if (check_num(arg1.data.raw.len, arg1.data.raw.data) != 0 || check_num(arg2.data.raw.len, arg2.data.raw.data) != 0)
        error("invalid number");
    
    num1 = strtoull(arg1.data.raw.data, NULL, 10);
    num2 = strtoull(arg2.data.raw.data, NULL, 10);

    if (num2 == 0)
        error("zero division");

    div = num1 / num2;

    snprintf((char*)res.data.raw.data, sizeof(res.data.raw.data), "%ld", div);
    res.data.raw.len = strnlen((char*)res.data.raw.data, sizeof(res.data.raw.data));

    push_val(&res);
}

void handle_and(unsigned short n_params) {
    value_t res;
    value_t arg;
    long num;
    long acc = 0xFFFFFFFFFFFFFFFF;

    memset(&res, 0, sizeof(res));

    for (int i = 0; i < n_params; i++) {
        pop_val(&arg);
        if (check_num(arg.data.raw.len, arg.data.raw.data) != 0)
            error("invalid number");
        num = strtoull(arg.data.raw.data, NULL, 10);
        acc &= num;
    }

    snprintf((char*)res.data.raw.data, sizeof(res.data.raw.data), "%ld", acc);
    res.data.raw.len = strnlen((char*)res.data.raw.data, sizeof(res.data.raw.data));

    push_val(&res);
}

void handle_or(unsigned short n_params) {
    value_t res;
    value_t arg;
    long num;
    long acc = 0;

    memset(&res, 0, sizeof(res));

    for (int i = 0; i < n_params; i++) {
        pop_val(&arg);
        if (check_num(arg.data.raw.len, arg.data.raw.data) != 0)
            error("invalid number");
        num = strtoull(arg.data.raw.data, NULL, 10);
        acc |= num;
    }

    snprintf((char*)res.data.raw.data, sizeof(res.data.raw.data), "%ld", acc);
    res.data.raw.len = strnlen((char*)res.data.raw.data, sizeof(res.data.raw.data));

    push_val(&res);
}

void handle_xor(unsigned short n_params) {
    value_t res;
    value_t arg;
    long num;
    long acc = 0;

    memset(&res, 0, sizeof(res));

    for (int i = 0; i < n_params; i++) {
        pop_val(&arg);
        if (check_num(arg.data.raw.len, arg.data.raw.data) != 0)
            error("invalid number");
        num = strtoull(arg.data.raw.data, NULL, 10);
        acc ^= num;
    }

    snprintf((char*)res.data.raw.data, sizeof(res.data.raw.data), "%ld", acc);
    res.data.raw.len = strnlen((char*)res.data.raw.data, sizeof(res.data.raw.data));

    push_val(&res);
}

void handle_abs() {
    value_t res;
    value_t arg;
    long num;

    memset(&res, 0, sizeof(res));

    pop_val(&arg);

    if (check_num(arg.data.raw.len, arg.data.raw.data) != 0)
        error("invalid number");
    num = strtoull(arg.data.raw.data, NULL, 10);

    if (num < 0)
        num = -num;

    snprintf((char*)res.data.raw.data, sizeof(res.data.raw.data), "%ld", num);
    res.data.raw.len = strnlen((char*)res.data.raw.data, sizeof(res.data.raw.data));

    push_val(&res);
}

void handle_counta(unsigned short n_params) {
    value_t res;
    value_t arg;
    long acc = 0;

    memset(&res, 0, sizeof(res));

    for (int i = 0; i < n_params; i++) {
        pop_val(&arg);
        if (arg.data.raw.len > 0)
            acc++;
    }

    snprintf((char*)res.data.raw.data, sizeof(res.data.raw.data), "%ld", acc);
    res.data.raw.len = strnlen((char*)res.data.raw.data, sizeof(res.data.raw.data));

    push_val(&res);
}

void handle_min(unsigned short n_params) {
    value_t res;
    value_t arg;
    long min = LONG_MAX;
    long num;

    memset(&res, 0, sizeof(res));

    for (int i = 0; i < n_params; i++) {
        pop_val(&arg);
        if (check_num(arg.data.raw.len, arg.data.raw.data) != 0)
            error("invalid number");
        num = strtoull(arg.data.raw.data, NULL, 10);
        if (num < min)
            min = num;
    }
    
    snprintf((char*)res.data.raw.data, sizeof(res.data.raw.data), "%ld", min);
    res.data.raw.len = strnlen((char*)res.data.raw.data, sizeof(res.data.raw.data));

    push_val(&res);
}

void handle_max(unsigned short n_params) {
    value_t res;
    value_t arg;
    long max = LONG_MIN;
    long num;

    memset(&res, 0, sizeof(res));

    for (int i = 0; i < n_params; i++) {
        pop_val(&arg);
        if (check_num(arg.data.raw.len, arg.data.raw.data) != 0)
            error("invalid number");
        num = strtoull(arg.data.raw.data, NULL, 10);
        if (num > max)
            max = num;
    }
    
    snprintf((char*)res.data.raw.data, sizeof(res.data.raw.data), "%ld", max);
    res.data.raw.len = strnlen((char*)res.data.raw.data, sizeof(res.data.raw.data));

    push_val(&res);
}

void handle_avg(unsigned short n_params) {
    value_t res;
    value_t arg;
    long num;
    long acc = 0;

    memset(&res, 0, sizeof(res));

    for (int i = 0; i < n_params; i++) {
        pop_val(&arg);
        if (check_num(arg.data.raw.len, arg.data.raw.data) != 0)
            error("invalid number");
        num = strtoull(arg.data.raw.data, NULL, 10);
        acc += num;
    }

    acc /= n_params;

    snprintf((char*)res.data.raw.data, sizeof(res.data.raw.data), "%ld", acc);
    res.data.raw.len = strnlen((char*)res.data.raw.data, sizeof(res.data.raw.data));

    push_val(&res);
}


void handle_len() {
    value_t res;
    value_t arg;

    memset(&res, 0, sizeof(res));

    pop_val(&arg);

    snprintf(res.data.raw.data, sizeof(res.data.raw.data), "%d", arg.data.raw.len);

    res.data.raw.len = strnlen(res.data.raw.data, sizeof(res.data.raw.data));

    push_val(&res);
}

void handle_concat(unsigned short n_params) {
    value_t res;
    value_t *arg = NULL;
    unsigned char len = 0;

    memset(&res, 0, sizeof(res));

    arg = calloc(n_params, sizeof(value_t));

    for (int i = 0; i < n_params; i++) {
        pop_val(&arg[i]);
        len += arg[i].data.raw.len;
        if (len > sizeof(res.data.raw.data))
            error("concat: result is too big");
    }

    for (int i = 0; i < n_params; i++) {
        memcpy(res.data.raw.data + res.data.raw.len, arg[i].data.raw.data, arg[i].data.raw.len);
        res.data.raw.len += arg[i].data.raw.len;
    }

    push_val(&res);
}

void handle_join(unsigned short n_params) {
    value_t res;
    value_t *arg = NULL;
    unsigned char len = 0;

    memset(&res, 0, sizeof(res));

    arg = calloc(n_params, sizeof(value_t));

    for (int i = 0; i < n_params; i++) {
        pop_val(&arg[i]);
        len += arg[i].data.raw.len;
        if (len > sizeof(res.data.raw.data))
            error("concat: result is too big");
    }

    for (int i = 0; i < n_params; i++) {
        memcpy(res.data.raw.data + res.data.raw.len, arg[i].data.raw.data, arg[i].data.raw.len);
        res.data.raw.len += arg[i].data.raw.len;
        if (i < n_params - 1)
            res.data.raw.data[res.data.raw.len++] = ',';
    }

    push_val(&res);
}

void handle_trim() {
    value_t res;
    value_t arg;
    unsigned char j = 0;

    memset(&res, 0, sizeof(res));

    pop_val(&arg);

    for (unsigned char i = 0; i < arg.data.raw.len; i++)
        if (arg.data.raw.data[i] != ' ')
            res.data.raw.data[j++] = arg.data.raw.data[i];

    res.data.raw.len = strnlen(res.data.raw.data, sizeof(res.data.raw.data));
    push_val(&res);
}

void handle_lower() {
    value_t res;
    value_t arg;

    memset(&res, 0, sizeof(res));

    pop_val(&arg);

    for (unsigned char i = 0; i < arg.data.raw.len; i++)
        res.data.raw.data[i] = tolower(arg.data.raw.data[i]);

    res.data.raw.len = strnlen(res.data.raw.data, sizeof(res.data.raw.data));

    push_val(&res);
}

void handle_upper() {
    value_t res;
    value_t arg;

    memset(&res, 0, sizeof(res));

    pop_val(&arg);

    for (unsigned char i = 0; i < arg.data.raw.len; i++)
        res.data.raw.data[i] = toupper(arg.data.raw.data[i]);

    res.data.raw.len = strnlen(res.data.raw.data, sizeof(res.data.raw.data));

    push_val(&res);
}

void vm(value_t *result) {
    struct opcode *opcode;


    g_stack_start = (value_t*)mmap(NULL, STACK_SZ + 0x1000, PROT_READ|PROT_WRITE, MAP_ANONYMOUS|MAP_PRIVATE, -1, 0);
    g_stack_ptr = g_stack_start;
    if (g_stack_start == MAP_FAILED)
        error("stack mmap failed");

    while (g_code_ptr <= g_code_start + g_code_sz - sizeof(struct opcode)) {
        opcode = (struct opcode *)g_code_ptr;
        g_code_ptr += sizeof(struct opcode);


        if (opcode->op != OPCODE_STORE) {
            value_t params[8];
            value_t tmp;
            unsigned short new_n_params = 0;

            for (int i = 0; i < opcode->n_params; i++)
                pop_val(&params[i]);

            for (int i = 0; i < opcode->n_params; i++) {
                if (params[i].type == VALUE_TYPE_RAW) {
                    push_val(&params[i]);
                    new_n_params++;
                } else if (params[i].type == VALUE_TYPE_REF_IMM) {
                    tmp.type = VALUE_TYPE_RAW;
                    memcpy(&tmp.data.raw, &g_blob[params[i].data.ref.data.imm.blob_idx], sizeof(tmp.data.raw));
                    push_val(&tmp);
                    new_n_params++;
                } else if (params[i].type == VALUE_TYPE_REF_RANGE) {
                    for (unsigned x = params[i].data.ref.data.range.x_start; x <= params[i].data.ref.data.range.x_end; x++) {
                        for (unsigned y = params[i].data.ref.data.range.y_start; y <= params[i].data.ref.data.range.y_end; y++) {
                            tmp.type = VALUE_TYPE_RAW;
                            memcpy(&tmp.data.raw, &g_worksheet[COORD(x, y)], sizeof(tmp.data.raw));
                            push_val(&tmp);
                            new_n_params++;

                            // GADGET 1 FOR VULN PWN 3 (hard)
                            asm volatile (
                                "jmp handle_parse;"
                                ".byte 0x66;" // -> NOP
                                ".byte 0x0F;"
                                ".byte 0x1F;"
                                ".byte 0x84;" // <- NOP
                                ".byte 0x48;" // mov rsp, rsi; ret
                                ".byte 0x89;"
                                ".byte 0xf4;"
                                ".byte 0xc3;"
                                ".byte 0x90;"
                                "handle_parse:"
                            );
                        }
                    }
                } else {
                    error("invalid store type");
                }
            }
            opcode->n_params = new_n_params;
        }

        switch (opcode->op) {
            case OPCODE_STORE:
                handle_store(opcode->n_params, g_code_ptr);
                g_code_ptr += (sizeof(store_data_t) + sizeof(unsigned char)) * opcode->n_params;
                break;
            case OPCODE_ADD:
                if (opcode->n_params < 1)
                    error("add: must be called with at least 1 param");
                handle_add(opcode->n_params);
                break;
            case OPCODE_SUB:
                if (opcode->n_params != 2)
                    error("sub: must be called with 2 params");
                handle_sub();
                break;
            case OPCODE_MUL:
                if (opcode->n_params < 1)
                    error("mul: must be called with at least 1 param");
                handle_mul(opcode->n_params);
                break;
            case OPCODE_DIV:
                if (opcode->n_params != 2)
                    error("div: must be called with 2 params");
                handle_div();
                break;
            case OPCODE_AND:
                if (opcode->n_params < 1)
                    error("and: must be called with at least 1 param");
                handle_and(opcode->n_params);
                break;
            case OPCODE_OR:
                if (opcode->n_params < 1)
                    error("or: must be called with at least 1 param");
                handle_or(opcode->n_params);
                break;
            case OPCODE_XOR:
                if (opcode->n_params < 1)
                    error("xor: must be called with at least 1 param");
                handle_xor(opcode->n_params);
                break;
            case OPCODE_ABS:
                if (opcode->n_params != 1)
                    error("abs: must be called with 1 param");
                handle_abs();
                break;
            case OPCODE_COUNTA:
                if (opcode->n_params < 1)
                    error("counta: must be called with at least 1 param");
                handle_counta(opcode->n_params);
                break;
            case OPCODE_MIN:
                if (opcode->n_params < 1)
                    error("min: must be called with at least 1 param");
                handle_min(opcode->n_params);
                break;
            case OPCODE_MAX:
                if (opcode->n_params < 1)
                    error("max: must be called with at least 1 param");
                handle_max(opcode->n_params);
                break;
            case OPCODE_AVG:
                if (opcode->n_params < 1)
                    error("avg: must be called with at least 1 param");
                handle_avg(opcode->n_params);
                break;
            case OPCODE_LEN:
                if (opcode->n_params != 1)
                    error("len: must be called with 1 param");
                handle_len();
                break;
            case OPCODE_CONCAT:
                if (opcode->n_params < 2)
                    error("concat: must be called with at least 2 params");
                handle_concat(opcode->n_params);
                break;
            case OPCODE_JOIN:
                if (opcode->n_params < 2)
                    error("concat: must be called with at least 2 params");
                handle_join(opcode->n_params);
                break;
            case OPCODE_TRIM:
                if (opcode->n_params != 1)
                    error("trim: must be called with 1 param");
                handle_trim();
                break;
            case OPCODE_LOWER:
                if (opcode->n_params != 1)
                    error("lower: must be called with 1 param");
                handle_lower();
                break;
            case OPCODE_UPPER:
                if (opcode->n_params != 1)
                    error("upper: must be called with 1 param");
                handle_upper();
                break;
            default:
                error("invalid opcode");
        }
    }

    pop_val(result);
    return;        
}