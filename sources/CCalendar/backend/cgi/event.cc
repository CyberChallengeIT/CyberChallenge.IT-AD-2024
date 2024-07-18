#include <cstring>
#include <iostream>
#include <string>

#include <cgicc/Cgicc.h>
#include <sqlite3.h>

#include "lib/db.hh"
#include "lib/util.hh"

int main(void) {
	cgicc::Cgicc cgi;

	// Make these the same way in all CGI bins that work with a date + auth
	struct {
		char date[16];
		int auth_err;
		char pad[64];
	} stuff;

	memset(stuff.date, 0, sizeof(stuff.date));
	write_response_head();

	const std::string method = cgi.getEnvironment().getRequestMethod();
	if (method != "POST" && method != "DELETE")
		exit_wrong_method(method);

	// This endpoint is authenticated via cookies set by PHP
	stuff.auth_err = auth_user(cgi);
	const char *owner = get_cookie_value(cgi, "user");
	if (stuff.auth_err)
		exit_error("Unauthorized");

	db_open("/var/db/db_events.sqlite", true);

	if (method == "POST") {
		// Add an event given all its details
		const char *title = get_param(cgi, "title"      , true);
		const char *descr = get_param(cgi, "description", true);
		const char *date  = get_param(cgi, "date"       , false);
		const char *year  = get_param(cgi, "year"       , false);
		const char *month = get_param(cgi, "month"      , false);
		const char *day   = get_param(cgi, "day"        , false);

		if (date) {
			// We have a date param, use that
			if (validate_date(date) != 0)
				exit_error("Invalid date");

			strncpy(stuff.date, date, sizeof(stuff.date));
		} else if (year || month || day) {
			// Otherwise take year, month and day
			if (!(year && month && day))
				exit_error("Incomplete date: either provide 'date' or 'year', 'month' and 'day'");

			unsigned y = strtoul(year, NULL, 10);
			unsigned m = strtoul(month, NULL, 10);
			unsigned d = strtoul(day, NULL, 10);

			// This prevents the bug in format_date()
			if (validate_y_m_d(y, m, d) != 0)
				exit_error("Invalid year or month or day");

			format_date(stuff.date, sizeof(stuff.date), y, m, d);
		}

		const char *event_id = gen_uuidv7();

		db_prepare_query("INSERT INTO events VALUES (?, ?, ?, ?, ?);");
		sqlite3_bind_text(stmt, 1, event_id, 36, SQLITE_TRANSIENT);
		sqlite3_bind_text(stmt, 2, owner, -1, SQLITE_TRANSIENT);
		sqlite3_bind_text(stmt, 3, title, -1, SQLITE_TRANSIENT);
		sqlite3_bind_text(stmt, 4, descr, -1, SQLITE_TRANSIENT);
		sqlite3_bind_text(stmt, 5, stuff.date, 10, SQLITE_TRANSIENT);

		if (sqlite3_step(stmt) != SQLITE_DONE) {
			db_log_error("sqlite3_step");
			exit_error("Internal database query error");
		}

		std::cout << "{\"success\": true, \"id\": \"" << event_id << "\"}\n";
	} else {
		// Delete an event given its ID
		const char *event_id = get_param(cgi, "id", true);

		db_prepare_query("DELETE FROM events WHERE owner = ? AND id = ?;");
		sqlite3_bind_text(stmt, 1, owner, -1, SQLITE_TRANSIENT);
		sqlite3_bind_text(stmt, 2, event_id, -1, SQLITE_TRANSIENT);

		// Will succeed even if the query does not match any existing row
		if (sqlite3_step(stmt) != SQLITE_DONE) {
			db_log_error("sqlite3_step");
			exit_error("Internal database query error");
		}

		// Check if DELETE deleted anything
		if (sqlite3_changes(db) == 0)
			exit_error("No such event");

		std::cout << "{\"success\": true}\n";
	}

	db_close();
	return 0;
}