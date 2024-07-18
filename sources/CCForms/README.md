# CCForms

| Service     | CCForms                                                                            |
| :---------- | :--------------------------------------------------------------------------------- |
| Authors     | Stefano Alberto <@Xato>, Giovanni Minotti <@Giotino>                               |
| Stores      | 2                                                                                  |
| Categories  | misc, web                                                                          |
| Ports       | HTTP 3000, HTTP 3001                                                               |
| FlagIds     | store1: [user_id, form_i], store2: [answer_id, form_id]                            |
| Checker     | [store1](/checkers/CCForms-1/checker.py), [store2](/checkers/CCForms-2/checker.py) |

## Description

This service lets you create forms with multiple questions and collect answers.
The frontend is a React application that uses the backend APIs to retrieve and store forms and answers.

Flags are stored in the private notes of a form for the first flagstore, and in the answer to a form for the second flagstore.

## Vulnerabilities

### Store 1 (misc): 

#### Vuln 1: Form inclusion

The "embedded" question type allows users to embed another form within a new form.
The application doesn't check the ownership of the embedded form, so users can embed forms created by other users, exposing the private notes.

To exploit this vulnerability, you must create a new form with a question that includes the form with the flag.
Retrieving the new form will give you the questions and notes from the embedded form, exposing the flag.

The patch requires to check the ownership of the form that users are trying to include, so that they can only include notes from forms that they own.


#### Vuln 2: Weak JWT secret

The application authenticates users with JWTs, the secret used to sign the tokens is generated in the `deploy.sh` script.

```bash
if [ ! -f .env ]; then
    echo -n "JWT_SECRET=" > .env
    echo $RANDOM | md5sum >> .env
fi
```

The `$RANDOM` variable used to generate the secret is insecure because it returns a random integer in the range 0 - 32767.

To exploit this vulnerability you can locally bruteforce the 32768 possible key values, then you can sign yourself valid JWT tokens for any user.
By using the `user_id` given as flagid you can easily spoof the JWT tokens needed to get the flag.

To patch this vulnerability you can simply change the `JWT_SECRET` variable to a strong random value. 

#### Vuln 3: Information leak in errors

When the backend server throws an error, the message returned contains a lot of information.
In particular, the server's environment variables are also returned to the client.

This is dangerous because the `JWT_SECRET` variable is stored in the environment and will be leaked in the error.

```js
// Catch errors
app.use((error, _req, res, _next) => {
  console.error(error);
  if (error instanceof HttpError) {
    res.status(error.code);
    res.json({ err: error.message });
  } else {
    res.status(500);
    res.json({
      message: error.message,
      stack: error.stack,
      env: process.env
    });
  }
});
```

To exploit this vulnerability, you need to trigger an error in the API server, then use `JWT_SECRET` to generate arbitrary JWT tokens and get the flag.

An easy way to trigger an error is to send a POST request with malformed JSON.

*Fix*: you need to remove the env variable from the returned error.

### Store 2 (web): 

#### Vuln 1: IDOR

Answers can be retrieved from the `/form/:id/answers` endpoint and should only be visible to the owner of the form.

However, the endpoint doesn't enforce authorization, so anyone can retrieve the answers to a form without being the owner.

To exploit the vulnerability, you can make a GET HTTP request to the `/form/:id/answers` endpoint and get all the responses, including the flag.

*Fix*: adding authorization checks on the vulnerable endpoint.

#### Vuln 2: SQL injection

Some questions allows users to upload files to the server. These files are stored in the database using a "sequelize.literal".

```js
for (const file of files) {
    await Files.create({
        id: file.id,
        name: file.name,
        content: sequelize.literal(`decode('${file.content}', 'base64')`)
    });
}
```
This is done to use the "decode" function offered by the database to convert the base64 content of the file to a blob before storing it in the database.
This approach is vulnerable to SQL injection because it explicitly overrides the protection provided by the ORM library.

To exploit this vulnerability, you can exploit the SQL injection to modify the query to include data from the database in the contents of the uploaded file.
You can then retrieve the file and read the leaked data.

The following payload allows you to include the contents of a specific response in the uploaded file.

```
' || (SELECT string_agg(answer, ',') FROM \"Answers\" WHERE id='ANSWER_ID_TO_LEAK'),'escape')) -- 
```

*Fix*: you need to remove the SQL injection, for example, by removing the use of `sequelize.literal` and decoding the contents of the file before querying the database.


## Exploits

| Store | Exploit                                                             |
| :---: | :------------------------------------------------------------------ |
|   1   | [CCForms-1-include.py](/exploits/CCForms/CCForms-1-include.py)      |
|   1   | [CCForms-1-jwtsecret.py](/exploits/CCForms/CCForms-1-jwtsecret.py)  |
|   1   | [CCForms-1-leakenv.py](/exploits/CCForms/CCForms-1-leakenv.py)      |
|   2   | [CCForms-2-idor.py](/exploits/CCForms/CCForms-2-idor.py)            |
|   2   | [CCForms-2-sqli.py](/exploits/CCForms/CCForms-2-sqli.py)            |
