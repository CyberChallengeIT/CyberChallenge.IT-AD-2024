# Inlook

| Service     | Inlook                                                                             |
| :---------- | :--------------------------------------------------------------------------------- |
| Authors     | Lorenzo Demeio <@Devrar>, Francesco Felet <@PhiQuadro>, Matteo Protopapa <@matpro> |
| Stores      | 2                                                                                  |
| Categories  | crypto, misc                                                                       |
| Port        | TCP 1337                                                                           |
| FlagIds     | store1: [address, email_id], store2: [mailinglist]                                 |
| Checker     | [store1](/checkers/Inlook-1/checker.py), [store2](/checkers/Inlook-2/checker.py)   |

## Description

This is an encrypted mail service. Users can send/receive emails and ask the server for arbitrary ciphertexts.

Users can also create/subscribe to mailing lists (which members are supposed to be "private" in some sense), send emails to mailing lists and "invite" another user to an existing mailing list, making them join automatically.

At registration, the server generates an asymmetric key pair which is sent back to the client at each login. The public key is used to encrypt (server side) the body of an email, using the Okamoto-Uchiyama cryptosystem on each block of plaintext, much like what one would do with a symmetric block cipher in ECB mode.

Ciphertexts are also bundled with an ElGamal-like signature (which is also computed server side) and the corresponding public key.

Flags are either the body of some encrypted email, or users of some mailing lists.

## Vulnerabilities

### Store 1 (crypto):

#### Vuln 1: Cipher's block length is *a bit* too much

The scheme is supposed to encrypt only plaintexts that are strictly less than $p$, but this is not actually enforced in the service: every block of plaintext that is encrypted is as long as $p$. If we encrypt and decrypt a message $m > p$, we will get $m \pmod{p}$ and can thus decrypt arbitrary ciphertexts.

Luckily, the service implements a "confirmation of receipt" feature which allows an attacker to do just that: when a user sends an email, the server reflects it back to the sender after encrypting and decrypting it with the public (resp. private) key of the recipient; it's sufficient to send `b'\xff'*32` to a victim to be able to break their key. 

(There are actually some details to pay attention to if one wants the attack to be fully reliable, mainly due to block alignment / presence of padding. The interested reader can infer those from the exploit code.)

*Fix:* reduce by 1 the block length.

#### Vuln 2: Signature allows for direct factorization of the modulus

The aforementioned signature being sent when we ask the server for a ciphertext is computed via an algorithm resembling the ElGamal signature scheme, but this time performed modulo $n$ instead of a prime (the same $n$ as the Okamoto-Uchiyama modulus we want to factor).

The order of the multiplicative group of integers modulo $n = p^2q$ is $p\cdot(p-1)\cdot(q-1)$. Here the server is restricting the generator $g$ to the subgroup of order $p-1$: $$g = 2^{p\cdot(q-1)} \pmod{n},$$ but a congruence modulo $n$ is valid modulo $d$, for each $d$ divisor of $n$.

Therefore, if we look at the equation modulo $q$, we obtain $$g = (2^p)^{(q-1)} \equiv 1 \pmod{q}$$ (by Little Fermat's Theorem); if we look at it modulo $p$ though, we obtain $$g = (2^{q-1})^p \equiv 2^{q-1} \not \equiv 1 \pmod{p}.$$

We can thus factor $n$ by simply computing $\gcd(g\_{sig} - 1, n) = q$.

*Fix:* sample $g$ randomly and fix the signature algorithm accordingly (verification needs to hold): the operations which were performed originally modulo $p-1$ must be now performed modulo the multiplicative order of $g$ (or a multiple, i.e. $`p \cdot (p-1) \cdot (q-1)`$).

### Store 2 (misc):

#### Vuln 1: Poor ownership check

Since the check is performed on the file read as a string, users who own a mailing list which name contains the name of another list, result as owners of that list too.

From `user.py`:
```python
def check_mailinglist(self, name):
    with open(f"{self.user_dir}/mailinglists.json") as rf:
        mailinglists = rf.read()
    return name in mailinglists
```

*Fix:* parse the JSON structure in `mailinglists.json` and look for a string in a list rather than for a substring in a string.

#### Vuln 2: Invite an entire mailing list

Sanitization is performed after `check_email_is_invite` has already been called, so an attacker can send an email that does not result as an invite at first, but does after the sanitization. E.g. an invite that starts as ``` `=====MAILING LIST INVITE=====```.

From `mail.py`:
```python
def send_email(sender_email: str, address: str, content: bytes, subject: str):
    ...
    is_invite = check_email_is_invite(content)
    ... # send email
```

```python
def send_email_to_user(sender_email: str, recipient: User, content: bytes, subject: str, email_id=None, send_answer=True):
    ...
    content = sanitize_email(content)
    ...
    if check_email_is_invite(content):
        ...
```

*Fix:* sanitize the email content as the first action, and specifically before the `check_email_is_invite`.

## Exploits

| Store | Exploit                                                                                 |
| :---: | :-------------------------------------------------------------------------------------- |
|   1   | [Inlook-1-block-length.py](/exploits/Inlook/Inlook-1-block-length.py)                   |
|   1   | [Inlook-1-signature-flaw.py](/exploits/Inlook/Inlook-1-signature-flaw.py)               |
|   2   | [Inlook-2-mailinglist-ownership.py](/exploits/Inlook/Inlook-2-mailinglist-ownership.py) |
|   2   | [Inlook-2-mailinglist-invite.py](/exploits/Inlook/Inlook-2-mailinglist-invite.py)       |
