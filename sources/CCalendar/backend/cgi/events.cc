#include <cstdbool>
#include <cstring>
#include <iostream>
#include <string>

#include <cgicc/Cgicc.h>
#include <sqlite3.h>

#include "lib/db.hh"
#include "lib/util.hh"

int main(void) {
	cgicc::Cgicc cgi;

	write_response_head();

	const std::string method = cgi.getEnvironment().getRequestMethod();
	if (method != "GET")
		exit_wrong_method(method);

	// This endpoint is unauthenticated and only accessible through PHP, so we
	// can trust the user specified as /events/<user>. However as it turns out
	// due to the web bug it will be possible to query this endpoint and request
	// events of arbitrary users.
	const char *user = strdup(cgi.getEnvironment().getPathInfo().c_str());
	if (validate_str_param(user) != 0)
		exit_error("Parameter '/<user>' contains invalid characters");

	db_open("/var/db/db_events.sqlite", false);

	// Get *all* events
	db_prepare_query("SELECT id, title, description, date FROM events WHERE owner = ?;");
	sqlite3_bind_text(stmt, 1, user, -1, SQLITE_TRANSIENT);

	std::cout << "{\"events\": [";

	int res;
	bool sep = false;

	while ((res = sqlite3_step(stmt)) != SQLITE_DONE) {
		if (res != SQLITE_ROW) {
			db_log_error("sqlite3_step");
			goto out_error;
		}

		const char *id    = (const char *)sqlite3_column_text(stmt, 0);
		const char *title = (const char *)sqlite3_column_text(stmt, 1);
		const char *descr = (const char *)sqlite3_column_text(stmt, 2);
		const char *date  = (const char *)sqlite3_column_text(stmt, 3);

		if (!id || !title || !descr || !date) {
			log_error("sqlite3_column_text returned unexpected null column(s)");
			goto out_error;
		}

		// Comma separator only after first obj
		if (sep)
			std::cout << ", ";
		else
			sep = true;

		// Strings in the DB already passed validation so they are safe to
		// output as JSON strings as is.
		std::cout << "{\"id\": \"" << id
			<< "\", \"title\": \"" << title
			<< "\", \"description\": \"" << descr
			<< "\", \"date\": \"" << date << "\"}";
	}

	std::cout << "], \"success\": true}\n";
	goto out;

out_error:
	std::cout << "], \"success\": false, \"error\": \"Internal database query error\"}\n";
out:
	db_close();
	return 0;
}
