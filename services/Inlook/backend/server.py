import json
import os

from user import auth
from mail import *

def recv_cmd():
    try:
        cmd = json.loads(input())
        return cmd
    except:
        exit()

def send_ans(ans):
    print(json.dumps(ans))

if not os.path.isdir(f"{DATA_DIR}/mailinglists"):
    os.mkdir(f"{DATA_DIR}/mailinglists")

while True:
    user = None
    while not user:
        user, ans = auth(recv_cmd())
        send_ans(ans)
        
    while True:
        cmd = recv_cmd()

        if cmd["action"] == "send_email":
            sender_email = user.email
            recipient_email = cmd["recipient"]
            content = bytes.fromhex(cmd["content"])
            subject = cmd["subject"]
            ans = send_email(sender_email, recipient_email, content, subject)
            send_ans(ans)

        if cmd["action"] == "get_inbox":
            ans = get_inbox(user)
            send_ans(ans)

        if cmd["action"] == "get_sent":
            ans = get_sent(user)
            send_ans(ans)

        if cmd["action"] == "get_email":
            email_id = os.path.basename(cmd["email_id"])
            folder = os.path.basename(cmd["folder"])
            ans = get_email(user, folder, email_id)
            send_ans(ans)

        if cmd["action"] == "get_encrypted_email":
            # don't remove this if you don't want to lose SLA
            email_id = os.path.basename(cmd["email_id"])
            email_user = User(cmd["address"])
            ans = get_email(email_user, "inbox", email_id)
            send_ans(ans)

        if cmd["action"] == "get_mailinglists":
            ans = get_mailinglists()
            send_ans(ans)

        if cmd["action"] == "get_user_mailinglists":
            ans = get_user_mailinglists(user)
            send_ans(ans)

        if cmd["action"] == "get_owner_mailinglists":
            ans = get_owned_mailinglists(user)
            send_ans(ans)

        if cmd["action"] == "create_mailinglist":
            ans = create_mailinglist(user, cmd["name"], cmd["description"])
            send_ans(ans)
        
        if cmd["action"] == "get_mailinglist_users":
            ans = get_mailinglist_users(user, cmd["name"])
            send_ans(ans)
        
        if cmd["action"] == "subscribe_to_mailinglist":
            ans = subscribe_to_mailinglist(user, cmd["name"])
            send_ans(ans)

        if cmd["action"] == "logout":
            send_ans({"result": "success"})
            break
    