#pragma once

#include <sqlite3.h>

extern sqlite3 *db;
extern sqlite3_stmt *stmt;

void db_open(const char *path, bool rw);
void db_close(void);
void db_prepare_query(const char *query);
void db_log_error(const char *msg);
