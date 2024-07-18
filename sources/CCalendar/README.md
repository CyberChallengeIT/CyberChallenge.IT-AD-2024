# CCalendar

| Service     | CCalendar                                                                    |
| :---------- | :--------------------------------------------------------------------------- |
| Authors     | Marco Bonelli <@mebeim>, Lorenzo Leonardini <@pianka>                        |
| Stores      | 2                                                                            |
| Categories  | web, pwn                                                                     |
| Port        | HTTPS 8443                                                                   |
| FlagIds     | store1: [event owner username], store2: [invitee username, invite date]      |
| Checkers    | [store1](/checkers/CCalendar-1), [store2](/checkers/CCalendar-2)             |

## Building

Run `make` to build the service and copy all the files necessary for deployment
into [`/services/CCalendar`](/services/CCalendar). The only thing that
is actually built are the C++ programs in [`backend/cgi/`](backend/cgi/), whose
compiled binaries will end up in [`backend/www/cgi-bin`](backend/www/cgi-bin).

Build dependencies: GNU Make, C++ compiler, `libcrypt-dev`, `libcgicc-dev`,
`libsqlite3-dev`.

## Description

The service implements a very simple web calendar where the only implemented
functionalities are registering user accounts, creating simple events for a
given date and sending event invites to other users (by username).

The web interface of the service interacts with a "frontend" server implemented
using Nginx + PHP, which also functions as a reverse-proxy for an internal
"backend" service implemented using Nginx + binary CGI-bin executables.

The internal endpoints implemented by the "backend" server are the following:

- `POST /event`: create an event with a given title, description and date;
- `DELETE /event`: delete an event given its ID;
- `GET /events/<username>`: list events of a user;
- `POST /invite`: create an invite for a given username and with a given title,
   description and date;
- `DELETE /invite`: delete an invite event given its ID;
- `GET /invites`: list invites you have received, optionally filtering by date.

All these endpoints **except `GET /events/<username>`** are reachable through
the "frontend" server (reverse-proxy), which forwards requests for `/api/xxx` to
the "backend" server at `/xxx`. All the endpoints
**except `GET /events/<username>`** are also authenticated through session
cookies set by the PHP server on user login. The endpoint for
`GET /events/<username>` is only internally reachable by the "frontend" PHP
server (requests for `/api/events/<username>` are not forwarded) and thus does
not perform authentication.

The "frontend" PHP server uses a SQLite database to save user
registration data (username and password hash), while the "backend" C++ CGI-bin
server uses a SQLite database to save event and invite details.

### Frontend server (PHP)

The frontend server is written in PHP, and is mainly responsible for serving all
the static files of the web app, and for implementing authentication into the
service.

The PHP frontend allows to signup and login by using a dedicated SQLite database
for storage. The session is validated through the use of a `user_hash` cookie,
created from the sha256 of the username and a secret. Such cookie is used to
authenticate both in frontend and in the API.

The frontend server also provides "server-side rendering" of each user's event
list, by retrieving it from the API and inserting it into the HTML. Because of
the NGINX configuration of the reverse proxy, only the frontend can access this
"event list" endpoint.

### Backend server (C++ CGI binaries)

The backend server implements the 4 endpoints as 4 different C++ programs,
compiled to x86_64 ELF binaries that are then invoked through CGI (Nginx
`fastcgi_pass` + `fcgiwrap`). These binaries use the
[Cgicc](https://www.gnu.org/software/cgicc/index.html) library that implements
the CGI protocol to conveniently retireve request parameters + cookies and
easily write responses.

The backend server manages two SQLite databases using the
[SQLite C interface](https://www.sqlite.org/cintro.html) provided by
`libsqlite3`:

- Events database at `backend/db/db_events.sqlite`, with schema
  [`backend/db/schema_events.sql`](backend/db/schema_events.sql). This DB is
  accessed in read-only mode from [`events.cc`](backend/cgi/events.cc)
  (`GET /events` endpoint) and in read-write mode from
  [`event.cc`](backend/cgi/event.cc) (`POST /event`, `DELETE /event`).

- Invites database at `backend/db/db_invites.sqlite`, with schema
  [`backend/db/schema_invites.sql`](backend/db/schema_invites.sql). This DB is
  accessed in read-only mode from [`invites.cc`](backend/cgi/invites.cc)
  (`GET /invites` endpoint) and in read-write mode from
  [`invite.cc`](backend/cgi/invite.cc) (`POST /invite`, `DELETE /invite`).


## Vulnerabilities

The service includes two intended vulnerabilities for each flag store.

### Store 1 (web)

#### Vuln 1: SSRF

For some weird reason, static files are not handled by NGINX as usual, but are
managed by PHP itself. The internal custom PHP router checks if the pathname
starts with `/static/` and, if that's true, serves the requested file:

```php
if (str_starts_with($request->path, '/static/')) {
    $response = new StaticFile($request);
}
```
```php
$content = file_get_contents(substr($this->request->path, 8));
header("Content-Type: $this->mime_type");

die($content !== false ? $content : throw new Exception());
```

However, since there is no check on the fact that we are requesting a file
relative to the current working directory, this code can present a problem if we
perform a request to the path `/static//etc/passwd`: PHP will read and serve the
file `/etc/passwd`.

Even worse, we can request the path `/static/http://example.com` to trigger a
Server Side Request Forgery (SSRF) attack. This can be exploited to access the
internal API endpoint used to retrieve all the events for a specific username:
`/static/http://api/events/[username]`

**Patching**

This vulnerability can be patched in various different ways. The real proper one
would be to stop this nonsense and make NGINX serve static files, as it should:

```nginx
location /static/ {
    alias /app/web/;
}

location ~ \.php$ {
    deny all;
}
```

While the second rule is not necessary, it is a nice to have in order to avoid
leaking any other patch we make on our service.

Another possible fix, maybe faster to come up with, is to blacklist "http" from
the filenames we allow to request:

```php
if (str_contains(strtolower($this->request->path), 'http')) {
    die('nope');
}
$content = file_get_contents(substr($this->request->path, 8));
header("Content-Type: $this->mime_type");
```

Generally speaking, there can be other different possible patches, but these two
cover both the "naive" and the "professional" approaches.

#### Vuln 2: Path traversal

To understand this vulnerability, we need to start from the piece of code that
requests the list of events from the backend API:

```php
json_decode(file_get_contents('http://api/events/' . $request->user));
```

If we could control the username arbitrarily, for example by having the username
`pianka/../mebeim`, we could potentially perform a path traversal attack and
retrieve the events for any other user: `http://api/events/pianka/../mebeim` ->
`http://api/events/mebeim`

Fortunately, there are checks on which characters can be used in the username:

```php
if (preg_match('/^.*[^a-zA-Z0-9].*$/', $request->form['username']))
    $this->throw_error('username cannot contain special chars');
```

Unfortunately, in PHP this regex is broken and can be bypassed by using some
newlines: a username like `pianka\n!!!!!\n` would not trigger any error.

What happens if we have some newlines in our username, though? Can we make a
request to `http://api/events/pianka\n!!!!!\n`? Not really, but luckily for us
the PHP URL parser replaces any non-printable character with an underscore. So,
the request above would really be `http://api/events/pianka_!!!!!_`.

We are almost there, let's try to create a user named `pianka\n/../mebeim\n_`:
we are now requesting `http://api/events/pianka_/../mebeim__`. We only need to
remove the final useless chars, and we can do that with the `#` character, that
marks the start of the URL fragment, which, by spec, is not sent in the request.

So, the final attack consists in creating the user `pianka\n/../mebeim#\n_` (the
final char is necessary to prevent stripping the second newline), which would
result in a request to `http://api/events/pianka_/../mebeim`. We now have access
to all mebeim's events :)

**Patching**

Patching here is really easy, and can be done by changing the regex to a
non-vulnerable one:

```php
if (!preg_match('/^[a-zA-Z0-9]$/', $request->form['username']))
    $this->throw_error('username cannot contain special chars');
```


### Store 2 (pwn)

#### Vuln 1: TOCTTOU + buffer overflow via memcpy() ⇒ auth bypass

The backend server endpoint
[`/services/CCalendar/backend/www/cgi-bin/intives.cgi`](/services/CCalendar/backend/www/cgi-bin/invites.cgi)
implemented at [`backend/cgi/intives.cc`](backend/cgi/invites.cc) implements a
filter-by-date functionality that allows querying invites for a given date.

User authentication has a common implementation for all backend CGI binaries at
implemented at [`backend/cgi/lib/util.cc`](backend/cgi/lib/util.cc), function
`auth_user()`. This simple function that checks if the
[`crypt`](https://manned.org/man/arch/crypt.5) hash of the `user` cookie is
equal to the hash specified in the `user_hash` cookie, using the latter to also
choose the hash type and salt. The function returns `0` in case of successful
authentication (hash matches) or non-zero otherwise.

The `main()` function (in `invites.cc`) initially calls `auth_user()` and saves
its return value on the stack. Then, if present, validates the date passed in
the `date=` GET parameter using the `validate_date()` function
([`backend/cgi/lib/util.cc`](backend/chi/lib/util.cc)). If validation passes,
the date is copied on a buffer on the stack that sits *right before* the saved
`auth_user()` return value.

Here's a snippet of the source code reconstructed by the IDA Freeware x86_64
decompiler:

```c
int __fastcall main(int argc, const char **argv, const char **envp)
{
    // ...
    char *date;         // [rsp+28h] [rbp-448h]
    // ...
    char date_copy[16]; // [rsp+90h] [rbp-3E0h] BYREF
    int auth_result;    // [rsp+A0h] [rbp-3D0h]

    // ...
    auth_result = auth_user((const cgicc::Cgicc *)v34);  /*** 1 ***/
    // ...
    date = get_param((cgicc::Cgicc *)v34, "date", 0);
    // ...

    if ( date )
    {
        if ( validate_date(date) )
            exit_error("Invalid date");
        n = strlen(date) + 1;
        if ( n > 84 )                                    /*** 2 ***/
            n = 84LL;
        memcpy(date_copy, date, n);                      /*** 3 ***/
    } else {
        // ...
    }

    if ( auth_result )                                   /*** 4 ***/
        exit_error("Unauthorized");

    // Proceed with quering the database and returning data...
}
```

The copy of the `date` parameter into the local stack buffer `date_copy` is
performed at ***(3)*** using `strlen()` of the original + `memcpy()`, with a
size capped at 84 bytes at ***(2)***. This can easily exceed the size of the
local `date_copy[]` buffer causing a buffer overflow and overwriting the value
of `auth_result`
**after it is calculated at *(1)*, but before it is checked at *(4)***.

The time-of-check to time-of-use (TOCTTOU) issue with `auth_result` combined
with the buffer overflow can therefore be exploited to perform an authentication
bypass.

The date validation is pretty simple to pass:

```c
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
```

The `date` parameter must simply start with 3 integers separated by dash (`-`)
that are within certain ranges. It can however continue with arbitrary
characters as `sscanf()` for the `%u` format specifier will stop at the first
non-digit character.

Supplying a date of the form `YYYY-MM-DDxxxxxx` (for example `2025-01-01AAAAAA`)
will therefore cause a buffer overflow of one byte and overwrite the
least-significant byte of `auth_res` with `\0` before it is checked, effectively
bypassing the authentication completely.

Right after this, the query performed through `sqlite3_prepare_v2()` plus
`sqlite3_bind_text()` always takes *exactly 10 bytes* from `date_copy`:

```c
if (*date_copy) {
    db_prepare_query("SELECT id, user_from, title, description, date FROM invites WHERE user_to = ? AND date = ?;");
    sqlite3_bind_text(stmt, 1, user, -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 2, date_copy, 10, SQLITE_TRANSIENT);
} else {
    // ...
}
// Iterate and return all the matched rows ...
```

This effectively still performs a correct query and allows to access the invites
of any user knowing the username and the invite date.

**Patching**

Patching this vulnerability is rather simple: making the constants used to check
the `date` length smaller, from `84` (`0x54`) to `16` (`0x10`) (or any value
between `16` and `10`).

The code:

```c
        n = strlen(date) + 1;
        if ( n > 84 )
            n = 84LL;
        memcpy(date_copy, date, n);
```

Is compiled as (output from `objdump -M intel -d invites.cgi`):

```none
4057: 48 83 bd a8 fb ff ff    cmp    QWORD PTR [rbp-0x458],0x54
405e: 54
405f: 76 0b                   jbe    406c <main+0x1d3>
4061: 48 c7 85 a8 fb ff ff    mov    QWORD PTR [rbp-0x458],0x54
4068: 54 00 00 00
...
```

And can be patched as follows only changing 2 bytes:

```diff
-4057: 48 83 bd a8 fb ff ff    cmp    QWORD PTR [rbp-0x458],0x54
-405e: 54
+4057: 48 83 bd a8 fb ff ff    cmp    QWORD PTR [rbp-0x458],0x10
+405e: 10
 405f: 76 0b                   jbe    406c <main+0x1d3>
-4061: 48 c7 85 a8 fb ff ff    mov    QWORD PTR [rbp-0x458],0x54
-4068: 54 00 00 00
+4061: 48 c7 85 a8 fb ff ff    mov    QWORD PTR [rbp-0x458],0x10
+4068: 10 00 00 00
```

#### Vuln 2: TOCTTOU + OOB access via snprintf() retval ⇒ auth bypass

The same TOCTTOU issue explained in the previous section can be abused again
together with a second bug resulting in another authentication bypass.

In case the `date` GET parameter is not supplied, the `year`, `month` and
`day` parameters can be supplied instead. If supplied, they are converted to
`unsigned int` using `strtoul()` and joined together to create a string of the
form `YYYY-MM-DD` that is then used to query the database exactly as explained
in the previous section.

While the two CGI binaries that also support these parameters
([`invite.cc`](backend/chi/invite.cc)), [`event.cc`](backend/chi/event.cc))
validate the values using the `validate_y_m_d()` function (shown above),
*this endpoint ([`invite.cc`](backend/chi/invite.cc)) does not perform any bound check on these values*
and allows arbitrarily large values to pass through. The `format_date()`
function from `utils.cc` is then used to convert the parameters to a string
representing the date:

```c
void format_date(char *out, size_t n, unsigned y, unsigned m, unsigned d) {
    int res = snprintf(out, n, "%04u-%02u-%02u", y, m, d);
    out[res] = '\0';
}
```

As can be seen from the above code, after trying to format the date into a
string of the form `YYYY-MM-DD`, the return value from `snprintf()` is used to
index the output buffer and add a NUL terminator (`\0`). This is problematic
because of the peculiar behavior of `snprintf()` when the passed size is not
enough to output the entire string.

From [`man 3 snprintf`](https://manned.org/man/snprintf.3):

> If the output was truncated due to this limit, then the return value is the
> number of characters (excluding the terminating null byte) which would have
> been written to the final string if enough space had been available. Thus, a
> return value of size or more means that the output was truncated.

The `main()` function performs the following call to `format_date()`
**without checking the values of its parameters**:

```c
char date_copy[16];
// ...
format_date(date_copy, 16, y, m, d);
```

Therefore, if the values of `y`, `m` and `d` are large enough, `snprintf()` will
write 16 bytes into `date_copy[]`, but then return a value higher than or equal
to 16. Given that this value is then used to index the array and add a NUL
terminator,
**this results in an out-of-bounds write of a `0` byte past the end of the array**.

Here's another snippet of the source code reconstructed by the IDA Freeware
x86_64 decompiler:

```c
int __fastcall main(int argc, const char **argv, const char **envp)
{
    char *date;         // [rsp+28h] [rbp-448h]
    char *year;         // [rsp+30h] [rbp-440h]
    char *month;        // [rsp+38h] [rbp-438h]
    char *day;          // [rsp+40h] [rbp-430h]
    // ...
    char date_copy[16]; // [rsp+90h] [rbp-3E0h] BYREF
    int auth_result;    // [rsp+A0h] [rbp-3D0h]
    // ...

    auth_result  = auth_user((const cgicc::Cgicc *)v34); /*** 1 ***/
    // ...
    date  = get_param((cgicc::Cgicc *)v34, "date", 0);
    year  = get_param((cgicc::Cgicc *)v34, "year", 0);
    month = get_param((cgicc::Cgicc *)v34, "month", 0);
    day   = get_param((cgicc::Cgicc *)v34, "day", 0);

    if ( date )
    {
        // ...
    }
    else if ( year && month && day )
    {
        y = strtoul(year, 0LL, 10);
        m = strtoul(month, 0LL, 10);
        d = strtoul(day, 0LL, 10);
        format_date(date_copy, 0x10uLL, y, m, d);        /*** 2 ***/
    }

    if ( auth_result )                                   /*** 3 ***/
        exit_error("Unauthorized");

    // Proceed with quering the database and returning data...
}
```

The parsing of the `y`, `m` and `d` integers is performed at ***(2)*** using
`format_date()`, with values that can potentially be as large as `UINT_MAX`.
Because of the buggy `format_date()` implementation, this can cause an OOB write
of a single `0` byte and change the value of the `auth_result` variable
**after it is calculated at *(1)*, but before it is checked at *(3)***.

The time-of-check to time-of-use (TOCTTOU) issue with `auth_result` combined
with the buffer overflow can therefore be exploited to perform an authentication
bypass. Supplying a `day` parameter that is 8 digits long will trigger the OOB
write and overwrite the least-significant byte of `auth_res` with `\0` before it
is checked, effectively bypassing the authentication completely.

A small caveat is that 10 bytes are still read from `date_copy[]` when
performing the query and returning its results, so only dates with a day that is
higher than or equal to `10` can both trigger the OOB plus successfully filter
the correct date value. For example, `year=2025&month=10&day=04999999` does not
work because `day` will become `4999999` when converted to `unsigned int`, and
the SQL query will be `WHERE date = "2025-10-49"`. On the other hand, passing
`year=2025&month=10&day=14999999` will parse the `day` as `14999999` when
converted to `unsigned int`, and the SQL query will be
`WHERE date = "2025-10-14"`, successfully querying the invites of an arbitrary
user for October 14, 2025. [The checker](/checkers/CCalendar-2/checker.py) is
aware of this and therefore only puts flags in invites with dates that have a
day higher than or equal to 10.

**Patching**

The `format_date()` function:

```c
void format_date(char *out, size_t n, unsigned y, unsigned m, unsigned d) {
    int res = snprintf(out, n, "%04u-%02u-%02u", y, m, d);
    out[res] = '\0';
}
```

Is compiled as (output from `objdump -M intel --demangle -d invites.cgi`):

```none
000000000000504b <format_date(char*, unsigned long, unsigned int, unsigned int, unsigned int)>:
    504b:       f3 0f 1e fa             endbr64
    504f:       55                      push   rbp
    5050:       48 89 e5                mov    rbp,rsp
    5053:       48 83 ec 30             sub    rsp,0x30
    5057:       48 89 7d e8             mov    QWORD PTR [rbp-0x18],rdi
    505b:       48 89 75 e0             mov    QWORD PTR [rbp-0x20],rsi
    505f:       89 55 dc                mov    DWORD PTR [rbp-0x24],edx
    5062:       89 4d d8                mov    DWORD PTR [rbp-0x28],ecx
    5065:       44 89 45 d4             mov    DWORD PTR [rbp-0x2c],r8d
    5069:       8b 7d d4                mov    edi,DWORD PTR [rbp-0x2c]
    506c:       8b 4d d8                mov    ecx,DWORD PTR [rbp-0x28]
    506f:       8b 55 dc                mov    edx,DWORD PTR [rbp-0x24]
    5072:       48 8b 75 e0             mov    rsi,QWORD PTR [rbp-0x20]
    5076:       48 8b 45 e8             mov    rax,QWORD PTR [rbp-0x18]
    507a:       41 89 f9                mov    r9d,edi
    507d:       41 89 c8                mov    r8d,ecx
    5080:       89 d1                   mov    ecx,edx
    5082:       48 8d 15 5b d2 ff ff    lea    rdx,[rip+0xffffffffffffd25b]
    5089:       48 89 c7                mov    rdi,rax
    508c:       b8 00 00 00 00          mov    eax,0x0
    5091:       e8 aa 12 00 00          call   6340 <_fini+0x760>
    5096:       89 45 fc                mov    DWORD PTR [rbp-0x4],eax
    5099:       8b 45 fc                mov    eax,DWORD PTR [rbp-0x4]
    509c:       48 63 d0                movsxd rdx,eax
    509f:       48 8b 45 e8             mov    rax,QWORD PTR [rbp-0x18]
    50a3:       48 01 d0                add    rax,rdx
    50a6:       c6 00 00                mov    BYTE PTR [rax],0x0
    50a9:       90                      nop
    50aa:       c9                      leave
    50ab:       c3                      ret
```

The return value of `snprintf()` is moved first on the stack and then into `rdx`
with the following instructions:

```none
    5096:       89 45 fc                mov    DWORD PTR [rbp-0x4],eax
    5099:       8b 45 fc                mov    eax,DWORD PTR [rbp-0x4]
    509c:       48 63 d0                movsxd rdx,eax
```

Changing the above instructions with a `mov edx,10` plus some `nop`s for padding
will result in always writing the NUL terminator (`\0`) at `out[10]` and
effectively eliminates the vulnerability without altering the service
functionality:

The code above can be patched as follows only changing 9 bytes:

```diff
     5089:       48 89 c7                mov    rdi,rax
     508c:       b8 00 00 00 00          mov    eax,0x0
     5091:       e8 aa 12 00 00          call   6340 <_fini+0x760>
-    5096:       89 45 fc                mov    DWORD PTR [rbp-0x4],eax
-    5099:       8b 45 fc                mov    eax,DWORD PTR [rbp-0x4]
-    509c:       48 63 d0                movsxd rdx,eax
+    5096:       ba 0a 00 00 00          mov    edx,0xa
+    509b:       90                      nop
+    509c:       90                      nop
+    509d:       90                      nop
+    509e:       90                      nop
     509f:       48 8b 45 e8             mov    rax,QWORD PTR [rbp-0x18]
     50a3:       48 01 d0                add    rax,rdx
     50a6:       c6 00 00                mov    BYTE PTR [rax],0x0
```

## Exploits

See [the readme in the exploits directory](/exploits/CCalendar/README.md)
for more information on the exploits!

| Store | Exploit                                                                             |
| :---: | :---------------------------------------------------------------------------------- |
|   1   | [CCalendar-1-static.py](/exploits/CCalendar/CCalendar-1-static.py)                   |
|   1   | [CCalendar-1-user-injection.py](/exploits/CCalendar/CCalendar-1-user-injection.py)   |
|   2   | [CCalendar-2-memcpy-bof.py](/exploits/CCalendar/CCalendar-2-memcpy-bof.py)           |
|   2   | [CCalendar-2-snprintf-retval.py](/exploits/CCalendar/CCalendar-2-snprintf-retval.py) |
