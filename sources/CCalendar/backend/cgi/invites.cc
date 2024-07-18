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

	// Make these the same way in all CGI bins that work with a date + auth
	struct {
		char date[16];
		int auth_err;
		// Make sure there's enough space after date[] to avoid messing things
		// up on the stack if the bug is triggered
		char pad[64];
	} stuff;

	memset(stuff.date, 0, sizeof(stuff.date));
	write_response_head();

	const std::string method = cgi.getEnvironment().getRequestMethod();
	if (method != "GET")
		exit_wrong_method(method);

	// This endpoint is authenticated via cookies set by PHP
	stuff.auth_err = auth_user(cgi);

	const char *user  = get_cookie_value(cgi, "user");
	const char *date  = get_param(cgi, "date" , false);
	const char *year  = get_param(cgi, "year" , false);
	const char *month = get_param(cgi, "month", false);
	const char *day   = get_param(cgi, "day"  , false);

	if (date) {
		// We have a date param, use that
		if (validate_date(date) != 0)
			exit_error("Invalid date");

		/* BUG #1: the check on the length of the date argument is wrong and
		 * has a maximum that is too high (sizeof(stuff) instead of
		 * sizeof(stuff.date)). The size passed to memcpy() can therefore exceed
		 * the size of stuff.date[] and canuse an overflow, as long as the
		 * validate_date() check is passed.
		 */
		size_t copy_sz = strlen(date) + 1;
		if (copy_sz > sizeof(stuff))
			copy_sz = sizeof(stuff);

		memcpy(stuff.date, date, copy_sz);
	} else if (year && month && day) {
		// Otherwise take year, month and day
		if (!(year && month && day))
			exit_error("Incomplete date: either provide 'date' or 'year', 'month' and 'day'");

		unsigned y = strtoul(year, NULL, 10);
		unsigned m = strtoul(month, NULL, 10);
		unsigned d = strtoul(day, NULL, 10);

		/* BUG #2 part 2/2: no call to validate_date(), the bug in format_date()
		 * is exploitable and can be used to overwrite the LSB of stuff.auth_err
		 * with 0.
		 */
		format_date(stuff.date, sizeof(stuff.date), y, m, d);
	}

	/* BUG #1 & #2: this should be checked immediately, but the check is delayed
	 * until here. Exploiting either the BUG #1 above or the BUG #2 in
	 * format_date() to overwrite stuff.auth_err results in auth bypass. In case
	 * of BUG #1, the whole value of stuff.auth_err can be overwritten. In case
	 * of BUG #2, the LSB of stuff.auth_err can be overwritten with a '\0'.
	 *
	 * BUG #1 example bypass: date=2025-01-18aaaaaa
	 * BUG #2 example bypass: year=9999&month=99&day=99999999
	 */
	if (stuff.auth_err)
		exit_error("Unauthorized");

	db_open("/var/db/db_invites.sqlite", false);

	if (*stuff.date) {
		// Filter by date
		db_prepare_query("SELECT id, user_from, title, description, date FROM invites WHERE user_to = ? AND date = ?;");
		sqlite3_bind_text(stmt, 1, user, -1, SQLITE_TRANSIENT);
		// The length = 10 parameter here makes sure SQLite will only see the
		// first 10 bytes of stuff.date, so even if a longer date is
		// sent/formatted to exploit the vuln, the query will still succeed (as
		// long as the first 10 chars are a valid and existing date).
		sqlite3_bind_text(stmt, 2, stuff.date, 10, SQLITE_TRANSIENT);
	} else {
		// Get *all* invites
		db_prepare_query("SELECT id, user_from, title, description, date FROM invites WHERE user_to = ?;");
		sqlite3_bind_text(stmt, 1, user, -1, SQLITE_TRANSIENT);
	}

	std::cout << "{\"invites\": [";

	int res;
	bool sep = false;

	while ((res = sqlite3_step(stmt)) != SQLITE_DONE) {
		if (res != SQLITE_ROW) {
			db_log_error("sqlite3_step");
			goto out_error;
		}

		const char *id    = (const char *)sqlite3_column_text(stmt, 0);
		const char *from  = (const char *)sqlite3_column_text(stmt, 1);
		const char *title = (const char *)sqlite3_column_text(stmt, 2);
		const char *descr = (const char *)sqlite3_column_text(stmt, 3);
		const char *date  = (const char *)sqlite3_column_text(stmt, 4);

		if (!id || !from || !title || !descr || !date) {
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
			<< "\", \"from\": \"" << from
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
