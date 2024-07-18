#include <iostream>

#include <sqlite3.h>

#include "db.hh"
#include "util.hh"

sqlite3 *db;
sqlite3_stmt *stmt;

void db_open(const char *path, bool rw) {
	int res;

	if (db)
		return;

	if (rw)
		res = sqlite3_open_v2(path, &db, SQLITE_OPEN_READWRITE, NULL);
	else
		res = sqlite3_open_v2(path, &db, SQLITE_OPEN_READONLY, NULL);

	if (res != SQLITE_OK) {
		db_log_error("sqlite3_open");
		exit_error("Internal database open error");
	}

	if (rw && sqlite3_db_readonly(db, NULL) == 1) {
		log_error("Failed to open DB in read-write mode");
		exit_error("Internal database open error");
	}
}

void db_close(void) {
	if (stmt)
		sqlite3_finalize(stmt);

	if (!db)
		return;

	// Can't really do much in this case. We already operated on the db,
	// returning failure seems pointless.
	if (sqlite3_close_v2(db) != SQLITE_OK)
		db_log_error("sqlite3_close_v2");
}

void db_prepare_query(const char *query) {
	if (stmt) {
		log_error("Preparing multiple queries at once");
		exit_error("Internal prepare query error");
	}

	if (sqlite3_prepare_v2(db, query, -1, &stmt, NULL) != SQLITE_OK) {
		db_log_error("sqlite3_prepare");
		exit_error("Internal prepare query error");
	}
}

void db_log_error(const char *msg) {
	std::cerr << msg << ": " << sqlite3_errmsg(db) << std::endl;
}
