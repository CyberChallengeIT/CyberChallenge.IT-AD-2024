from hashlib import sha256
import os
import json

from cipher import *

DATA_DIR = "./data"
FOLDERS = ["inbox", "sent"]

class User:
    def __init__(self, email):
        self.email = email
        self.id = sha256(email.encode()).hexdigest()
        self.user_dir = f"{DATA_DIR}/{self.id}"
        self.load_keys()

    def init_folders(self):
        for folder in FOLDERS:
            os.mkdir(f"{self.user_dir}/{folder}")
            with open(f"{self.user_dir}/{folder}/metadata.json", "w") as wf:
                wf.write(json.dumps({}))
        with open(f"{self.user_dir}/mailinglists.json", "w") as wf:
            json.dump([], wf)

    def load_keys(self):
        if not os.path.isfile(f"{self.user_dir}/sk.txt"):
            self.sk, self.pk = gen_key()
            with open(f"{self.user_dir}/sk.txt", "w") as wf:
                json.dump(self.sk, wf)
            with open(f"{self.user_dir}/pk.txt", "w") as wf:
                json.dump(self.pk, wf)
        else:
            with open(f"{self.user_dir}/sk.txt") as rf:
                self.sk = json.load(rf)
            with open(f"{self.user_dir}/pk.txt") as rf:
                self.pk = json.load(rf)

    def save_mail(self, folder, email_id, content, subject, other, timestamp):
        with open(f"{self.user_dir}/{folder}/{email_id}", "wb") as wf:
            wf.write(encrypt(content, self.pk))
        with open(f"{self.user_dir}/{folder}/metadata.json") as rf:
            metadata = json.load(rf)
        metadata[email_id] = {
            "timestamp": timestamp,
            "subject": subject,
        }
        if folder == "inbox":
            metadata[email_id]["sender"] = other
            metadata[email_id]["recipient"] = self.email
        elif folder == "sent":
            metadata[email_id]["recipient"] = other
            metadata[email_id]["sender"] = self.email
        with open(f"{self.user_dir}/{folder}/metadata.json", "w") as wf:
            json.dump(metadata, wf)

    def add_mailinglist(self, name):
        with open(f"{self.user_dir}/mailinglists.json") as rf:
            mailinglists = json.load(rf)
        with open(f"{self.user_dir}/mailinglists.json", "w") as wf:
            json.dump(mailinglists + [name], wf)

    def check_mailinglist(self, name):
        with open(f"{self.user_dir}/mailinglists.json") as rf:
            mailinglists = rf.read()
        return name in mailinglists
        

def get_user(email: str):
    id = sha256(email.encode()).hexdigest()
    user_dir = f"{DATA_DIR}/{id}"
    if not os.path.isdir(user_dir):
        return None
    else:
        user = User(email)
        return user

def login(email: str, password: str):
    user = get_user(email)
    if not user:
        return None, {"result": "fail", "error": "Wrong email or password"}
    else:
        with open(f"{user.user_dir}/info.json") as rf:
            info = json.load(rf)
            if not password == info["password"]:
                return None, {"result": "fail", "error": "Wrong email or password"}
            else:
                return user, {"result": "success", "name": info["name"], "surname": info["surname"], "sk": user.sk}

def register(email: str, password: str, name: str, surname: str):
    id = sha256(email.encode()).hexdigest()
    if id in os.listdir(DATA_DIR) or f"{id}.json" in os.listdir(f"{DATA_DIR}/mailinglists"):
        return None, {"result": "fail", "error": "Address already exists"}
    else:
        user_dir = f"{DATA_DIR}/{id}"
        os.mkdir(user_dir)
        with open(f"{user_dir}/info.json", "w") as wf:
            wf.write(json.dumps({"password": password, "name": name, "surname": surname}))
        user = User(email)
        user.init_folders()
        return user, {"result": "success", "name": name, "surname": surname, "sk": user.sk}

def auth(cmd: dict):
    if cmd["action"] == "login":
        return login(cmd["email"], cmd["password"])
    elif cmd["action"] == "register":
        return register(cmd["email"], cmd["password"], cmd["name"], cmd["surname"])
    else:
        return None, {"result": "fail", "error": "Invalid action"}
