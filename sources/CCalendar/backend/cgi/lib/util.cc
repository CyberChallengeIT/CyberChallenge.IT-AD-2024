#include <iostream>
#include <chrono>
#include <cstdbool>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <sys/random.h>
#include <vector>

#include <cgicc/Cgicc.h>
#include <cgicc/HTTPContentHeader.h>
#include <crypt.h>

#include "util.hh"
#include "db.hh"

void write_response_head(void) {
	std::cout << cgicc::HTTPContentHeader(std::string("application/json"));
}

const char *get_cookie_value(const cgicc::Cgicc &cgi, const char *name) {
	const std::vector<cgicc::HTTPCookie> &cookies = cgi.getEnvironment().getCookieList();
	for (const cgicc::HTTPCookie& c : cookies) {
		if (c.getName().compare(name) == 0)
			return strdup(cgicc::form_urldecode(c.getValue()).c_str());
	}

	exit_error("Missing '%s' cookie", name);
}

const char *get_param(cgicc::Cgicc &cgi, const char *name, bool required) {
	cgicc::form_iterator it = cgi.getElement(name);
	if (it == cgi.getElements().end()) {
		if (required)
			exit_error("Missing '%s' parameter", name);
		return NULL;
	}

	const char *res = strdup((cgicc::form_urldecode(**it)).c_str());

	// Validate to prevent breaking JSON output and other shenanigans later
	if (validate_str_param(res) != 0)
		exit_error("Parameter '%s' contains invalid characters", name);

	return res;
}

int validate_str_param(const char *str) {
	// Accept only these safe chars to avoid problems. This is a subset of safe
	// characters that can go in JSON strings without being escaped.
	const char *accepted = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789~!@#$%^&*()[]{}_-+=:;,.? ";
	if (strspn(str, accepted) == strlen(str))
		return 0;
	return 1;
}

int validate_y_m_d(unsigned y, unsigned m, unsigned d) {
	if (y < 1970 || y > 9999 || m < 1 || m > 12 || d < 1 || d > 31)
		return 1;
	return 0;
}

int validate_date(const char *date) {
	unsigned y, m, d;

	if (sscanf(date, "%u-%u-%u", &y, &m, &d) != 3)
		return 1;
	return validate_y_m_d(y, m, d);
}

int auth_user(const cgicc::Cgicc &cgi) {
	const char *secret = getenv("CRYPT_SECRET");
	if (!secret)
		exit_error("Internal error");

	const char *user = get_cookie_value(cgi, "user");
	const char *expected_hash = get_cookie_value(cgi, "user_hash");

	// Concatenate user + secret and hash as requested
	char phrase[128];
	strncpy(phrase, user, sizeof(phrase) - 1);
	strncat(phrase, secret, sizeof(phrase) - 1);
	phrase[sizeof(phrase) - 1] = '\0';

	const char *hash = crypt(phrase, expected_hash);
	int res = !hash || strcmp(hash, expected_hash);

	free((void *)expected_hash);
	free((void *)user);
	return res;
}

void format_date(char *out, size_t n, unsigned y, unsigned m, unsigned d) {
	int res = snprintf(out, n, "%04u-%02u-%02u", y, m, d);

	/* BUG #2 part 1/2: snprintf() returns the number of chars that *would have*
	 * been printed if enough space was available. This can higher than |n|.
	 * Trusting the result is wrong, unless the caller has specifically
	 * validated the 3 values passed to this function beforehand.
	 * The date is validated for all endpoints except /invites. Supplying large
	 * values for the year, month and date parameters can cause a relative OOB
	 * write of the '\0' terminator depending on the size of the buffer.
	 */
	out[res] = '\0';
}

char *gen_uuidv7(void) {
	uint8_t *v = (uint8_t *)malloc(16);
	char *res = (char *)malloc(37);

	if (getrandom(v, 16, 0) != 16)
		exit_error("Server out of entropy");

	auto now = std::chrono::system_clock::now();
	auto millis = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()).count();

	v[0] = (millis >> 40) & 0xFF;
	v[1] = (millis >> 32) & 0xFF;
	v[2] = (millis >> 24) & 0xFF;
	v[3] = (millis >> 16) & 0xFF;
	v[4] = (millis >> 8) & 0xFF;
	v[5] = millis & 0xFF;
	v[6] = (v[6] & 0x0F) | 0x70;
	v[8] = (v[8] & 0x3F) | 0x80;

	const char *fmt = "%02x%02x%02x%02x-%02x%02x-%02x%02x-%02x%02x-%02x%02x%02x%02x%02x%02x";
	snprintf(res, 37, fmt, v[0], v[1], v[2], v[3], v[4], v[5], v[6], v[7],
		v[8], v[9], v[10], v[11], v[12], v[13], v[14], v[15]);

	return res;
}

void log_error(const char *msg) {
	std::cerr << msg << std::endl;
}

void exit_wrong_method(const std::string &method) {
	exit_error("Invalid method: %s", method.c_str());
}

__attribute__((format(printf, 1, 2), noreturn))
void exit_error(const char *fmt, ...) {
	va_list args;

	db_close();

	std::cout << "{\"success\": false, \"error\": \"";
	va_start(args, fmt);
	std::vprintf(fmt, args);
	va_end(args);
	std::cout << "\"}\n";

	std::exit(0);
}

__attribute__((noreturn))
void exit_success(void) {
	db_close();
	std::cout << "{\"success\": true}\n";
	std::exit(0);
}
