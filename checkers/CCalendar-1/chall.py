import json
import random

import requests
requests.packages.urllib3.disable_warnings()


class ConstraintException(Exception):
    pass


class Challenge:
    host: str
    sess: requests.Session

    def __init__(self, host: str):
        self.host = host
        self.sess = requests.Session()
        self.sess.headers['User-Agent'] = 'CHECKER'

    def check_static_file(self, file_name :str):
        r = self.sess.get(f'https://{self.host}/static/{file_name}', verify=False, allow_redirects=False)
        r.raise_for_status()
        if len(r.content) < 5:
            raise Exception('No file')

    def register(self, username: str, password: str):
        r = self.sess.post(f'https://{self.host}/register', data={
            'username': username,
            'password': password
        }, verify=False, allow_redirects=False)
        r.raise_for_status()
        if 'alert-danger' in r.text:
            raise ConstraintException(r.text.split(
                '<div class="alert alert-danger" role="alert">')[1].split('</div>')[0].strip())
        return r.text

    def login(self, username: str, password: str):
        r = self.sess.post(f'https://{self.host}/login',
                           data={'username': username, 'password': password}, verify=False, allow_redirects=False)
        r.raise_for_status()
        if 'alert-danger' in r.text:
            raise ConstraintException(r.text.split('<div class="alert alert-danger" role="alert">')[1].split('</div>')[0].strip())
        return r.text

    def get_home(self):
        r = self.sess.get(f'https://{self.host}', verify=False, allow_redirects=False)
        r.raise_for_status()
        return r.text

    def get_events(self):
        r = self.sess.get(f'https://{self.host}/', verify=False, allow_redirects=False)
        r.raise_for_status()
        events = json.loads(r.text.split('event_data = ')[1].split('</script>')[0].strip())['events']
        return events

    def create_event(self, title: str, description: str, year: int, month: int, day: int):
        data = {'title': title, 'description': description}

        if random.randint(0, 1):
            data |= {'year': year, 'month': month, 'day': day}
        else:
            data |= {'date': f'{year:04d}-{month:02d}-{day:02d}'}

        r = self.sess.post(f'https://{self.host}/api/event', data=data,
                verify=False, allow_redirects=False)
        r.raise_for_status()
        data = r.json()
        if not data['success']:
            raise Exception(data['error'])
        return data

    def delete_event(self, id: str):
        r = self.sess.delete(
            f'https://{self.host}/api/event?id={id}', verify=False, allow_redirects=False)
        r.raise_for_status()
        data = r.json()
        if not data['success']:
            raise Exception(data['error'])
        return data
