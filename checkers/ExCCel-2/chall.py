import os
import time
from typing import TypedDict, Optional

import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class LoginFirst(TypedDict):
    token: str
    timestamp: int


class LoginSecond(TypedDict):
    nonce: str


class UserLight(TypedDict):
    id: int
    username: str


class User(TypedDict):
    id: Optional[int]


class OptionalUser(User):
    logged: bool


class WorksheetLight(TypedDict):
    id: str
    title: str
    sharable: bool
    owner: UserLight


class Cell(TypedDict):
    x: int
    y: int
    content: str


class EvaluatedCell(Cell):
    evaluated: Optional[str]


class CommentLight(TypedDict):
    id: int


class Comment(CommentLight):
    x: int
    y: int
    created: int
    content: str
    owner: UserLight


class Worksheet(WorksheetLight):
    guests: list[UserLight]
    cells: list[EvaluatedCell]
    comments: list[Comment]


class WorksheetShare(TypedDict):
    token: str


def raise_for_status(r: requests.Response):
    try:
        r.raise_for_status()
    except requests.RequestException as e:
        raise requests.RequestException(r.text, request=e.request, response=e.response)


def derive_key(passwd: str) -> bytes:
    digest = hashes.Hash(hashes.SHA256())
    digest.update(passwd.encode())
    return digest.finalize()


def generate_login_token(passwd: str, timestamp: int) -> tuple[bytes, bytes]:
    nonce = os.urandom(24)
    data = nonce + timestamp.to_bytes(8, 'little')

    iv = os.urandom(16)
    encryptor = Cipher(algorithms.AES256(derive_key(passwd)), modes.CBC(iv)).encryptor()
    ct = encryptor.update(data) + encryptor.finalize()
    return nonce, iv + ct


def verify_login_token(passwd: str, timestamp: int, token: bytes, nonce: bytes):
    decryptor = Cipher(algorithms.AES256(derive_key(passwd)), modes.CBC(token[:16])).decryptor()
    data = decryptor.update(token[16:]) + decryptor.finalize()

    return data[:24] == nonce and data[24:32] == timestamp.to_bytes(8, 'little')


class LoginError(Exception):
    pass

class Challenge:
    host: str
    sess: requests.Session

    def __init__(self, host: str):
        self.host = host
        self.sess = requests.Session()

    def user(self) -> OptionalUser:
        r = self.sess.get(f'http://{self.host}/api/user')
        raise_for_status(r)
        return r.json()

    def login_first(self, username: str) -> LoginFirst:
        r = self.sess.post(f'http://{self.host}/api/login/first', json={'username': username})
        raise_for_status(r)
        return r.json()

    def login_second(self, token: str) -> LoginSecond:
        r = self.sess.post(f'http://{self.host}/api/login/second', json={'token': token})
        raise_for_status(r)
        return r.json()

    def login_third(self, nonce: str) -> User:
        r = self.sess.post(f'http://{self.host}/api/login/third', json={'nonce': nonce})
        raise_for_status(r)
        return r.json()

    def login(self, username: str, password: str) -> User:
        first = self.login_first(username)
        client_nonce, client_token = generate_login_token(password, first['timestamp'])
        second = self.login_second(client_token.hex())

        if not verify_login_token(password, first['timestamp'], bytes.fromhex(first['token']),
                                  bytes.fromhex(second['nonce'])) or second['nonce'] == client_nonce:
            raise LoginError()

        return self.login_third(client_nonce.hex())

    def register(self, username: str, password: str) -> None:
        r = self.sess.post(f'http://{self.host}/api/register', json={'username': username, 'password': password})
        raise_for_status(r)

    def register_and_login(self, username: str, password: str) -> User:
        self.register(username, password)
        return self.login(username, password)

    def logout(self) -> None:
        r = self.sess.post(f'http://{self.host}/api/logout')
        raise_for_status(r)

    def get_worksheets(self) -> list[WorksheetLight]:
        r = self.sess.get(f'http://{self.host}/api/worksheets')
        raise_for_status(r)
        return r.json()

    def get_worksheet(self, worksheet_id: str, timestamp=str(int(time.time() * 1000))) -> Worksheet:
        r = self.sess.get(f'http://{self.host}/api/worksheet/{worksheet_id}?timestamp={timestamp}')
        raise_for_status(r)
        return r.json()

    def create_worksheet(self, title: str, sharable: bool) -> WorksheetLight:
        r = self.sess.post(f'http://{self.host}/api/worksheets', json={'title': title, 'sharable': sharable})
        raise_for_status(r)
        return r.json()

    def share_worksheet(self, worksheet_id: str) -> WorksheetShare:
        r = self.sess.post(f'http://{self.host}/api/worksheet/{worksheet_id}/share')
        raise_for_status(r)
        return r.json()

    def accept_worksheet_invite(self, worksheet_id: str, token: str) -> None:
        r = self.sess.post(f'http://{self.host}/api/worksheet/{worksheet_id}/invite/{token}')
        raise_for_status(r)

    def save_worksheet(self, worksheet_id: str, cells: list[Cell], timestamp=str(int(time.time() * 1000))) -> Worksheet:
        r = self.sess.post(f'http://{self.host}/api/worksheet/{worksheet_id}?timestamp={timestamp}',
                           json={'cells': cells})
        raise_for_status(r)
        return r.json()

    def create_comment(self, worksheet_id: str, x: int, y: int, content: str) -> CommentLight:
        r = self.sess.post(f'http://{self.host}/api/worksheet/{worksheet_id}/comments',
                           json={'x': x, 'y': y, 'content': content})
        raise_for_status(r)
        return r.json()
