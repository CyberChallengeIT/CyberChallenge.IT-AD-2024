#!/usr/bin/env python3

from checklib import *
from client import *
from cipher import decrypt

import string
import random
import hashlib

os.makedirs("data", exist_ok=True)

PORT = 1337
alphabet = string.ascii_letters + string.digits

NOT_ALLOWED = "`'{}\\"
sanitezed_alphabet = alphabet
for c in NOT_ALLOWED:
    sanitezed_alphabet = sanitezed_alphabet.replace(c, '')

def get_random_str(len):
    return ''.join(random.choice(alphabet) for i in range(len))

def get_sanitezed_str(len):
    return ''.join(random.choice(sanitezed_alphabet) for i in range(len))

def get_unsafe_str(len):
    s = list(get_random_str(len))
    for _ in range(5):
        n = random.randint(0, len-1)
        s[n] = random.choice(NOT_ALLOWED)
    return ''.join(s)

def sanitize_email(content: bytes):
    for c in NOT_ALLOWED.encode():
        content = content.replace(bytes([c]), b"")
    return content

def random_email():
    return get_random_str(20) + "@cc.it"

def deterministic_data(flag):
    random.seed(flag)
    user1 = (get_random_str(20), get_random_str(20), random_email(), get_random_str(20))
    user2 = (get_random_str(20), get_random_str(20), random_email(), get_random_str(20))

    subject = get_random_str(20)

    random.seed(os.urandom(10))

    return user1, user2, subject


def check_sla(host):
    # Check service functionality
    client = Client(host, PORT)

    try:
        client.connect()
    except Exception as e:
        quit(Status.DOWN, 'Connection failed', str(e))

    email1 = random_email()
    password1 = get_random_str(20)

    try:
        ans = client.register(get_random_str(20), get_random_str(20), email1, password1)
        if ans["result"] == "fail":
            quit(Status.DOWN, 'Registration failed', ans["error"])
        client1_sk = ans["sk"]
        client1_n = client1_sk[0]**2*client1_sk[1]
    except Exception as e:
        quit(Status.DOWN, 'Registration failed', str(e))
    
    try:
        ans = client.logout()
        if ans["result"] == "fail":
            quit(Status.DOWN, 'Logout failed', ans["error"])
    except Exception as e:
        quit(Status.DOWN, 'Logout failed', str(e))
    

    email2 = random_email()
    password2 = get_random_str(20)

    ans = client.register(get_random_str(20), get_random_str(20), email2, password2)
    if ans["result"] == "fail":
        quit(Status.DOWN, 'Registration failed', ans["error"])

    content1 = get_sanitezed_str(random.randint(100, 200))
    subject1 = get_random_str(random.randint(20, 30))

    try:
        ans = client.send_mail(email1, subject1, content1)
        if ans["result"] == "fail":
            quit(Status.DOWN, 'Send email failed', ans["error"])
    except Exception as e:
        quit(Status.DOWN, 'Send email failed', str(e))
    if "answer" not in ans:
        quit(Status.DOWN, 'Answer to email incorrect', 'Answer not in response')
    elif ans["answer"] != f"I received your email with content {content1}":
        quit(Status.DOWN, 'Answer to email incorrect', f'Answer incorrect: {ans["answer"]}')

    try:
        email_id1 = ans["email_id"]
        ans = client.get_encrypted_email(email1, email_id1)
        if ans["result"] == "fail":
            quit(Status.DOWN, 'Cannot retrieve encrypted email', ans["error"])
    except Exception as e:
        quit(Status.DOWN, 'Cannot retrieve encrypted email', str(e))

    try:
        enc_content = bytes.fromhex(ans["content"])
        pk_sig = ans["pk_sig"]
        if pk_sig[0] != client1_n:
            quit(Status.DOWN, 'Incorrect public key', f'Got {pk_sig[0]}, should be {client1_n}')
        dec = decrypt(enc_content, client1_sk).decode()
        if dec != content1:
            quit(Status.DOWN, 'Encrypted mail incorrect', f'Got {dec}, should be {content1}')
    except Exception as e:
        quit(Status.DOWN, 'Encrypted mail incorrect', str(e))

    content2 = get_unsafe_str(random.randint(100, 200))
    subject2 = get_random_str(random.randint(20, 30))

    try:
        ans = client.send_mail(email1, subject2, content2)
        if ans["result"] == "fail":
            quit(Status.DOWN, 'Send email failed', ans["error"])
        email_id2 = ans["email_id"]
    except Exception as e:
        quit(Status.DOWN, 'Send email failed', str(e))

    client.logout()
    try:
        ans = client.login(email1, password1)
        if ans["result"] == "fail":
            quit(Status.DOWN, 'Registration failed', ans["error"])
    except Exception as e:
        quit(Status.DOWN, 'Registration failed', str(e))

    try:
        ans = client.get_folder("inbox")
        if ans["result"] == "fail":
            quit(Status.DOWN, 'Failed to get inbox', ans["error"])
    except Exception as e:
        quit(Status.DOWN, 'Failed to get inbox', str(e))

    try:
        ans = client.get_email("inbox", email_id1)
        if ans["result"] == "fail" or ans["content"] != content1:
            quit(Status.DOWN, 'Cannot retrieve email', str(ans))
    except Exception as e:
        quit(Status.DOWN, 'Cannot retrieve email', str(e))

    sanitized_content = sanitize_email(content2.encode()).decode()
    try:
        ans = client.get_email("inbox", email_id2)
        if ans["result"] == "fail" or ans["content"] != sanitized_content:
            quit(Status.DOWN, 'Sanitization incorrect', str(ans))
    except Exception as e:
        quit(Status.DOWN, 'Sanitization incorrect', str(e))

def put_flag(host, flag):

    try:
        client = Client(host, PORT)
        client.connect()
        user1, user2, subject = deterministic_data(flag)
        client.register(*user1)
        client.logout()
        client.register(*user2)
        ans = client.send_mail(user1[2], subject, flag)
        if ans["result"] == "fail":
            quit(Status.DOWN, 'Cannot set flag', 'Cannot set flag: ' + ans["error"])
        email_id = ans["email_id"]
        # Generate flag_id for the flag, put the flag inside the service
        flag_id = {
            "address": user1[2],
            "email_id": ans["email_id"]
        }
    except Exception as e:
        quit(Status.DOWN, 'Cannot set flag', str(e))

    if 'LOCALHOST' in os.environ:
        print(json.dumps(flag_id))
    else:
        # Post flag id to game server
        try:
            post_flag_id('Inlook-1', team_id, flag_id)  
        except Exception as e:
            quit(Status.ERROR, 'Failed to post flag id', str(e))

        with open(f'data/{hashlib.md5(flag.encode()).hexdigest()}', 'w') as f:
            json.dump({
                'email_id': email_id,
            }, f)

def get_flag(host, flag):

    client = Client(host, PORT)
    client.connect()
    user1, user2, subject = deterministic_data(flag)
    with open(f'data/{hashlib.md5(flag.encode()).hexdigest()}') as f:
        email_id = json.load(f)["email_id"]
    client.login(user1[2], user1[3])
    user1_sk = client.sk
    ans = client.get_email("inbox", email_id)

    if ans["content"] != flag:
        quit(Status.DOWN, 'Cannot get flag', 'Cannot get flag, got ' + ans['content'])
    
    client.logout()

    client.login(user2[2], user2[3])
    ans = client.get_encrypted_email(user1[2], email_id)
    enc_content = bytes.fromhex(ans["content"])
    dec = decrypt(enc_content, user1_sk).decode()

    if dec != flag:
        quit(Status.DOWN, 'Cannot get flag', 'Cannot get flag from encrypted mail')

if __name__ == '__main__':
    data = get_data()
    action = data['action']
    team_id = data['teamId']
    host = '10.60.' + team_id + '.1'

    if 'LOCALHOST' in os.environ:
        host = '127.0.0.1'

    if action == Action.CHECK_SLA.name:
        try:
            check_sla(host)
        except Exception as e:
            quit(Status.DOWN, 'Cannot check SLA', str(e))
    elif action == Action.PUT_FLAG.name:
        flag = data['flag']
        try:
            put_flag(host, flag)
        except Exception as e:
            quit(Status.DOWN, "Cannot put flag", str(e))
    elif action == Action.GET_FLAG.name:
        flag = data['flag']
        try:
            get_flag(host, flag)
        except Exception as e:
            quit(Status.DOWN, "Cannot get flag", str(e))
    else:
        quit(Status.ERROR, 'System error', 'Unknown action: ' + action)

    quit(Status.OK, 'OK')
