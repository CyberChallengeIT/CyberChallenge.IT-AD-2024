#!/usr/bin/env python3
import os
os.environ["PWNLIB_NOTERM"] = "1"

from pwn import remote
import json
from cipher import decrypt, verify

import logging
logging.disable()


class Client():
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.connected = False
        self.authenticated = False
        self.sk = None

    def connect(self):
        self.remote = remote(self.host, self.port)
        self.connected = True

    def close(self):
        if self.connected:
            self.remote.close()
            self.connected = False

    def register(self, name, surname, email, password):
        if self.connected:
            self.remote.sendline(json.dumps({"action": "register", "email": email, "password": password, "name": name, "surname": surname}).encode())
            result = json.loads(self.remote.recvline(False).decode())
            if result["result"] == "success":
                self.authenticated = True
                self.sk = result["sk"]
            return result
    
    def login(self, email, password):
        if self.connected:
            self.remote.sendline(json.dumps({"action": "login", "email": email, "password": password}).encode())
            result = json.loads(self.remote.recvline(False).decode())
            if result["result"] == "success":
                self.authenticated = True
                self.sk = result["sk"]
            return result

    def logout(self):
        if self.authenticated:
            self.remote.sendline(json.dumps({"action": "logout"}).encode())
            result = json.loads(self.remote.recvline(False).decode())
            if result["result"] == "success":
                self.authenticated = False
                self.sk = None
            return result
        
    def get_folder(self, folder):
        if self.authenticated:
            self.remote.sendline(json.dumps({"action": f"get_{folder}"}).encode())
            result = json.loads(self.remote.recvline(False).decode())
            return result
        
    def get_email(self, folder, email_id):
        if self.authenticated:
            self.remote.sendline(json.dumps({"action": "get_email", "folder": folder, "email_id": email_id}).encode())
            result = json.loads(self.remote.recvline(False).decode())
            if result["result"] == "success":
                if not verify(result["sig"], result["pk_sig"], bytes.fromhex(result["content"])):
                    result["result"] = "fail"
                    result["error"] = "Signature doesn't verify"
                result["content"] = decrypt(bytes.fromhex(result["content"]), self.sk).decode()
            return result
        
    def get_encrypted_email(self, address, email_id):
        if self.authenticated:
            self.remote.sendline(json.dumps({"action": "get_encrypted_email", "address": address, "email_id": email_id}).encode())
            result = json.loads(self.remote.recvline(False).decode())
            if result["result"] == "success":
                if not verify(result["sig"], result["pk_sig"], bytes.fromhex(result["content"])):
                    result = {"result": "fail", "error": "Signature doesn't verify"}
            return result

    def send_mail(self, recipient, subject, content):
        if self.authenticated:
            self.remote.sendline(json.dumps({"action": "send_email", "recipient": recipient, "content": content.encode().hex(), "subject": subject}).encode())
            result = json.loads(self.remote.recvline(False).decode())
            if result["result"] == "success":
                if "answer" in result:
                    result["answer"] = decrypt(bytes.fromhex(result["answer"]), self.sk).decode()
                else:
                    result["answer"] = ""
            return result
        
    def get_mailinglists(self):
        if self.authenticated:
            self.remote.sendline(json.dumps({"action": "get_mailinglists"}).encode())
            result = json.loads(self.remote.recvline(False).decode())
            return result
        
    def join_mailinglist(self, name):
        if self.authenticated:
            self.remote.sendline(json.dumps({"action": "subscribe_to_mailinglist", "name": name}).encode())
            result = json.loads(self.remote.recvline(False).decode())
            return result
        
    def create_mailinglist(self, name, description):
        if self.authenticated:
            self.remote.sendline(json.dumps({"action": "create_mailinglist", "name": name, "description": description}).encode())
            result = json.loads(self.remote.recvline(False).decode())
            return result
        
    def get_mailinglist_users(self, name):
        if self.authenticated:
            self.remote.sendline(json.dumps({"action": "get_mailinglist_users", "name": name}).encode())
            result = json.loads(self.remote.recvline(False).decode())
            return result
    
    def get_user_mailinglists(self):
        if self.authenticated:
            self.remote.sendline(json.dumps({"action": "get_user_mailinglists"}).encode())
            result = json.loads(self.remote.recvline(False).decode())
            return result
        
    def get_user_owned_mailinglists(self):
        if self.authenticated:
            self.remote.sendline(json.dumps({"action": "get_owner_mailinglists"}).encode())
            result = json.loads(self.remote.recvline(False).decode())
            return result
        
    def get_mailinglist_users(self, name):
        if self.authenticated:
            self.remote.sendline(json.dumps({"action": "get_mailinglist_users", "name": name}).encode())
            result = json.loads(self.remote.recvline(False).decode())
            return result