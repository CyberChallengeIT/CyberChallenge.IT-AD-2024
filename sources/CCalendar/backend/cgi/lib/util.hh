#pragma once

#include <cstdio>
#include <string>

#include <cgicc/Cgicc.h>

void write_response_head(void);

const char *get_cookie_value(const cgicc::Cgicc &cgi, const char *name);
const char *get_param(cgicc::Cgicc &cgi, const char *name, bool required);
int auth_user(const cgicc::Cgicc &cgi);

int validate_str_param(const char *str);
int validate_y_m_d(unsigned y, unsigned m, unsigned d);
int validate_date(const char *date);

void format_date(char *out, size_t n, unsigned y, unsigned m, unsigned d);

char *gen_uuidv7(void);

void log_error(const char *msg);

void exit_wrong_method(const std::string &method);
void exit_error(const char *fmt, ...);
void exit_success(void);
