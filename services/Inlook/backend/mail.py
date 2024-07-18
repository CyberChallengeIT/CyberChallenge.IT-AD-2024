from uuid import uuid4
import time

from user import *
from cipher import *


NOT_ALLOWED = b"`'{}\\"


def check_email_is_invite(content: bytes):
    lines = content.split(b'\n')
    if (lines[0] == b"=====MAILING LIST INVITE====="
        and lines[1].startswith(b"You are kindly invited to join my mailing list: ")
        and lines[2] == b"=====MAILING LIST INVITE====="):
        return True
    return False

def sanitize_email(content: bytes):
    for c in NOT_ALLOWED:
        content = content.replace(bytes([c]), b"")
    return content

def send_email_to_user(sender_email: str, recipient: User, content: bytes, subject: str, email_id=None, send_answer=True):
    sender = get_user(sender_email)
    if not email_id:
        email_id = str(uuid4())
    timestamp = int(time.time())
    content = sanitize_email(content)
    sender.save_mail("sent", email_id, content, subject, recipient.email, timestamp)
    recipient.save_mail("inbox", email_id, content, subject, sender.email, timestamp)
    if send_answer:
        answer = auto_response(recipient, sender, email_id).hex()
    else:
        answer = ""
    if check_email_is_invite(content):
        name = content.split(b": ")[1].split(b"\n")[0]
        subscribe_to_mailinglist(recipient, name.decode())
    return {"result": "success", "answer": answer, "email_id": email_id}

def send_email_to_mailinglist(sender_email: str, mailinglist_info: dict, content: bytes, subject: str):
    users = mailinglist_info["users"]
    if sender_email not in users:
        return {"result": "fail", "error": "You are not part of this mailing list"}
    users.remove(sender_email)
    email_id = str(uuid4())
    for u in users:
        send_email_to_user(sender_email, get_user(u), content, subject, email_id=email_id, send_answer=False)
    return {"result": "success", "email_id": email_id}

def send_email(sender_email: str, address: str, content: bytes, subject: str):
    if len(content) + len(subject) > 6000:
        return {"result": "fail", "error": "Size too big"}
    is_invite = check_email_is_invite(content)
    recipient = get_user(address)
    if recipient:
        return send_email_to_user(sender_email, recipient, content, subject)
    else:
        if is_invite:
            return {"result": "fail", "error": "Only single users can be invited"}
        else:
            mailinglist_info = get_mailinglist_info(address)
            if mailinglist_info:
                return send_email_to_mailinglist(sender_email, mailinglist_info, content, subject)
            else:
                return {"result": "fail", "error": "Address does not exist"}

def create_mailinglist(user: User, name: str, description: str):
    list_id = sha256(name.encode()).hexdigest()
    list_path = f"data/mailinglists/{list_id}.json"
    if os.path.isfile(list_path) or list_id in os.listdir(DATA_DIR):
        return {"result": "fail", "error": "Address already exists"}
    else:
        created_at = int(time.time())
        with open(list_path, "w") as wf:
            json.dump({
                "name": name,
                "description": description,
                "created_at": created_at,
                "users": [user.email]
            }, wf)
        user.add_mailinglist(name)
        return {"result": "success"}

def get_mailinglists():
    mailinglists = {}
    for list_id in os.listdir("data/mailinglists"):
        with open(f"data/mailinglists/{list_id}") as rf:
            mailinglist_info = json.load(rf)
        mailinglists[list_id.split(".")[0]] = {
            "name": mailinglist_info["name"],
            "description": mailinglist_info["description"]
        }
    
    return {"result": "success", "mailinglists": mailinglists}

def get_user_mailinglists(user: User):
    mailinglists = {}
    for list_id in os.listdir("data/mailinglists"):
        with open(f"data/mailinglists/{list_id}") as rf:
            mailinglist_info = json.load(rf)
        if user.email in mailinglist_info["users"]:
            mailinglists[list_id.split(".")[0]] = {
                "name": mailinglist_info["name"],
                "description": mailinglist_info["description"]
            }
    
    return {"result": "success", "mailinglists": mailinglists}

def get_owned_mailinglists(user: User):
    mailinglists = {}
    owned_mailinglists = json.load(open(f"{user.user_dir}/mailinglists.json"))
    for name in owned_mailinglists:
        list_id = sha256(name.encode()).hexdigest()
        with open(f"data/mailinglists/{list_id}.json") as rf:
            mailinglist_info = json.load(rf)
            mailinglists[list_id] = mailinglist_info
    return {"result": "success", "mailinglists": mailinglists}

def get_mailinglist_info(name: str):
    list_id = sha256(name.encode()).hexdigest()
    list_path = f"data/mailinglists/{list_id}.json"
    if not os.path.isfile(list_path):
        return None
    else:
        with open(f"data/mailinglists/{list_id}.json") as rf:
            mailinglist_info = json.load(rf)
        return mailinglist_info

def get_mailinglist_users(user: User, name: str):
    if not user.check_mailinglist(name):
        return {"result": "fail", "error": "You are not the owner of this mailing list"}
    else:
        mailinglist_info = get_mailinglist_info(name)
        if not mailinglist_info:
            return {"result": "fail", "error": "Mailing list does not exists"}
        else:
            return {"result": "success", "users": mailinglist_info["users"]}
        
def subscribe_to_mailinglist(user: User, name: str):
    mailinglist_info = get_mailinglist_info(name)
    if not mailinglist_info:
        return {"result": "fail", "error": "Mailing list does not exists"}
    else:
        if user.email in mailinglist_info["users"]:
            return {"result": "fail", "error": "You are already part of this mailing list"}
        else:
            mailinglist_info["users"].append(user.email)
            list_id = sha256(name.encode()).hexdigest()
            list_path = f"data/mailinglists/{list_id}.json"
            with open(list_path, "w") as wf:
                json.dump(mailinglist_info, wf)
                return {"result": "success"}

def auto_response(recipient: User, sender: User, email_id: str):
    with open(f"{recipient.user_dir}/inbox/{email_id}", "rb") as rf:
        content = decrypt(rf.read(), recipient.sk)
    answer = encrypt(b"I received your email with content " + content, sender.pk)

    return answer

def get_inbox(user: User):
    inbox_path = f"{user.user_dir}/inbox"
    emails = os.listdir(inbox_path)
    emails.remove("metadata.json")
    with open(f"{inbox_path}/metadata.json") as rf:
        metadata = json.load(rf)
    return {"result": "success", "email_ids": emails, "metadata": metadata}

def get_sent(user: User):
    sent_path = f"{user.user_dir}/sent"
    emails = os.listdir(sent_path)
    emails.remove("metadata.json")
    with open(f"{sent_path}/metadata.json") as rf:
        metadata = json.load(rf)
    return {"result": "success", "email_ids": emails, "metadata": metadata}

def get_email(user: User, folder: str, email_id: str):
    with open(f"{user.user_dir}/{folder}/{email_id}", "rb") as rf:
        content = rf.read()
    sig, pk_sig = sign(user.sk, content)
    return {"result": "success", "content": content.hex(), "sig": sig, "pk_sig": pk_sig}
    
