import random
from collections import namedtuple
from typing import Optional, List
import json

import requests
requests.packages.urllib3.disable_warnings()


def chance(percentage: int) -> bool:
    return random.randint(1, 100) <= percentage


class ConstraintException(Exception):
    pass


class BackendError(Exception):
    pass


class BackendException(Exception):
    pass


Event = namedtuple('Event', ['id', 'title', 'description', 'year', 'month', 'day'])
Invite = namedtuple('Invite', ['id', 'user_from', 'user_to', 'title', 'description', 'year', 'month', 'day'])


class Challenge:
    host: str
    sess: requests.Session
    username: Optional[str]

    def __init__(self, host: str):
        self.host = host
        self.sess = requests.Session()
        self.sess.headers['User-Agent'] = 'CHECKER'
        self.username = None

    def _check_backend_response(self, req_method: str,
                                resp: requests.Response,
                                expect_error: bool = False):
        try:
            j = resp.json()
        except requests.exceptions.JSONDecodeError as e:
            raise BackendException(f'Invalid JSON: {resp.url=}, {resp.content=}')

        if j.get('success', False):
            if expect_error:
                # Nice error that can be shown in scoreboard
                raise BackendError(f'{req_method} request to {resp.url} '
                    'returned succeess instead of error')
        else:
            if expect_error:
                return j

            err = j.get('error')
            if err is not None:
                # Nice error that can be shown in scoreboard
                raise BackendError(f'{req_method} request to {resp.url} '
                    f'returned error instead of success: {err}')
            else:
                # Something bad happened
                raise BackendException(f'Bad JSON response format: {req_method=}, {resp.url=}, {j=}')

        return j

    def register(self, username: str, password: str):
        r = self.sess.post(f'https://{self.host}/register', data={
            'username': username,
            'password': password},
        verify=False, allow_redirects=False)
        r.raise_for_status()
        if 'alert-danger' in r.text:
            raise ConstraintException(r.text.split('<div class="alert alert-danger" role="alert">')[1].split('</div>')[0].strip())
        return r.text

    def login(self, username: str, password: str):
        r = self.sess.post(f'https://{self.host}/login', data={
            'username': username,
            'password': password
        }, verify=False, allow_redirects=False)
        r.raise_for_status()
        if 'alert-danger' in r.text:
            raise ConstraintException(r.text.split(
                '<div class="alert alert-danger" role="alert">')[1].split('</div>')[0].strip())

        # Remember for later use by caller
        self.username = username
        return r.text

    def get_home(self):
        r = self.sess.get(f'https://{self.host}', verify=False, allow_redirects=False)
        r.raise_for_status()
        return r.text

    def get_events(self) -> List[Event]:
        r = self.sess.get(f'https://{self.host}/', verify=False, allow_redirects=False)
        r.raise_for_status()
        events = json.loads(
            r.text.split('event_data = ')[1].split('</script>')[0].strip()
        )['events']

        res = []
        try:
            for raw_evt in events:
                res.append(Event(
                    raw_evt['id'],
                    raw_evt['title'],
                    raw_evt['description'],
                    raw_evt['year'],
                    raw_evt['month'],
                    raw_evt['day']
                ))
        except ValueError as e:
            raise BackendException(
                f'Bad date in event: {e!r}, {raw_evt=}, {events=}')

        return res

    def create_event(self, title: str, description: str, year: int, month: int, day: int):
        data = {'title': title, 'description': description}

        if chance(50):
            data |= {'year': year, 'month': month, 'day': day}
        else:
            data |= {'date': f'{year:04d}-{month:02d}-{day:02d}'}

        r = self.sess.post(f'https://{self.host}/api/event', data=data,
            verify=False, allow_redirects=False)
        r.raise_for_status()

        j = self._check_backend_response('POST', r)
        return j.get('id')

    def delete_event(self, id: str):
        r = self.sess.delete(f'https://{self.host}/api/event',
                params={'id': id}, verify=False, allow_redirects=False)
        r.raise_for_status()
        self._check_backend_response('DELETE', r)

    def get_invites(self, year: Optional[int] = None,
                    month: Optional[int] = None,
                    day: Optional[int] = None) -> List[Invite]:
        if any(x is not None for x in (year, month, day)):
            assert all(x is not None for x in (year, month, day)), 'get_invites ymd!'
            if chance(50):
                params = {'year': year, 'month': month, 'day': day}
            else:
                params = {'date': f'{year:04d}-{month:02d}-{day:02d}'}
        else:
            params = None

        r = self.sess.get(f'https://{self.host}/api/invites', params=params,
                verify=False, allow_redirects=False)
        r.raise_for_status()
        j = self._check_backend_response('GET', r)

        res = []
        try:
            for raw_inv in j['invites']:
                y, m, d = map(int, raw_inv['date'].split('-'))
                res.append(Invite(
                    raw_inv['id'],
                    raw_inv['from'],
                    self.username,
                    raw_inv['title'],
                    raw_inv['description'],
                    y, m, d
                ))
        except KeyError as e:
            raise BackendException(f'Bad JSON response format: {e!r}, {j=}')
        except ValueError as e:
            raise BackendException(f'Bad date in response: {e!r}, {j=}')

        return res

    def create_invite(self, to: str, title: str, description: str,
                      year: int, month: int, day: int,
                      expect_error: bool = False) -> Optional[str]:
        data = {'to': to, 'title': title, 'description': description}

        if chance(50):
            data |= {'year': year, 'month': month, 'day': day}
        else:
            data |= {'date': f'{year:04d}-{month:02d}-{day:02d}'}

        r = self.sess.post(f'https://{self.host}/api/invite', data=data,
                verify=False, allow_redirects=False)
        r.raise_for_status()

        j = self._check_backend_response('POST', r, expect_error)
        if not expect_error:
            return j.get('id')

    def delete_invite(self, id: str, expect_error: bool = False):
        r = self.sess.delete(f'https://{self.host}/api/invite',
                params={'id': id}, verify=False, allow_redirects=False)
        r.raise_for_status()
        self._check_backend_response('DELETE', r, expect_error)

    def accept_invite(self, id: str, title: str, description: str, year: int, month: int, day: int) -> str:
        self.delete_invite(id)
        self.create_event(title, description, year, month, day)
