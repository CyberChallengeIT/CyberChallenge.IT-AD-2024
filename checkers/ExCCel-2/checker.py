#!/usr/bin/env python3
import hashlib
import json
import random
import string
import traceback

from requests import RequestException

from chall import Challenge, LoginError
from checklib import *
from formula import FormulaGenerator


def rand_str(length: int = 10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def nice_logs(logs: list[str], *args: str) -> str:
    if sys.exc_info()[0] is None:
        tb = ''.join(traceback.format_stack())
    else:
        tb = traceback.format_exc()

    logs.insert(0, f'Traceback: {tb}')
    logs += args
    return '\n'.join(logs)


def check_sla_1(host):
    ch = Challenge(f'{host}:8000')

    username, password = rand_str(), rand_str()
    logs = [f'Username: {username}', f'Password: {password}']

    try:
        ch.register(username, password)
    except RequestException:
        quit(Status.DOWN, 'Could not register', nice_logs(logs))

    try:
        u1 = ch.login(username, password)
    except (RequestException, LoginError):
        quit(Status.DOWN, 'Could not login', nice_logs(logs))

    logs += [f'User 1: {u1}']

    if not isinstance(u1['id'], int):
        quit(Status.DOWN, 'Invalid login', nice_logs(logs))

    try:
        u2 = ch.user()
    except RequestException:
        quit(Status.DOWN, 'Could not get user info', nice_logs(logs))

    logs += [f'User 2: {u2}']

    if not isinstance(u2['logged'], bool) or not u2['logged'] or u2['id'] != u1['id']:
        quit(Status.DOWN, 'Invalid user info response', nice_logs(logs))

    try:
        ch.logout()
    except RequestException:
        quit(Status.DOWN, 'Could not logout', nice_logs(logs))


def check_sla_2(host):
    ch = Challenge(f'{host}:8000')

    username, password = rand_str(), rand_str()
    worksheet_title = rand_str()

    logs = [f'Username: {username}', f'Password: {password}', f'Worksheet title: {worksheet_title}']

    try:
        ch.register_and_login(username, password)
    except (RequestException, LoginError):
        quit(Status.DOWN, 'Could not register/login', nice_logs(logs))

    try:
        w1 = ch.create_worksheet(worksheet_title, random.choice([True, False]))
    except RequestException:
        quit(Status.DOWN, 'Could not create worksheet', nice_logs(logs))

    if not isinstance(w1['id'], str) or not isinstance(w1['title'], str):
        quit(Status.DOWN, 'Invalid create worksheet response', nice_logs(logs, f'Worksheet: {w1}'))
    elif w1['title'] != worksheet_title:
        quit(Status.DOWN, 'Wrong worksheet title', nice_logs(logs, f'Worksheet: {w1}'))

    logs += [f'Worksheet: {w1["id"]}']

    if w1['sharable']:
        try:
            ch.share_worksheet(w1['id'])
        except RequestException:
            quit(Status.DOWN, 'Could not share worksheet', nice_logs(logs))

    if random.choices([True, False]):
        try:
            ws = ch.get_worksheets()
        except RequestException:
            quit(Status.DOWN, 'Could not list worksheets', nice_logs(logs))

        if not isinstance(ws, list) or len(ws) != 1 or ws[0]['id'] != w1['id'] or ws[0]['title'] != worksheet_title:
            quit(Status.DOWN, 'Invalid list worksheets response', nice_logs(logs, f'Worksheets: {ws}'))
    else:
        try:
            w1 = ch.get_worksheet(w1['id'])
        except RequestException:
            quit(Status.DOWN, 'Could not get worksheet', nice_logs(logs))

        if w1['title'] != worksheet_title:
            quit(Status.DOWN, 'Wrong worksheet title', nice_logs(logs, f'Worksheet: {w1}'))
        elif not isinstance(w1['cells'], list) or len(w1['cells']) != 0:
            quit(Status.DOWN, 'Wrong worksheet cells', nice_logs(logs, f'Worksheet: {w1}'))


def check_sla_3(host):
    ch = Challenge(f'{host}:8000')

    username, password = rand_str(), rand_str()
    worksheet_title = rand_str()

    logs = [f'Username: {username}', f'Password: {password}', f'Worksheet title: {worksheet_title}']

    try:
        ch.register_and_login(username, password)
    except (RequestException, LoginError):
        quit(Status.DOWN, 'Could not register/login', nice_logs(logs))

    try:
        w1 = ch.create_worksheet(worksheet_title, False)
    except RequestException:
        quit(Status.DOWN, 'Could not create worksheet', nice_logs(logs))

    logs += [f'Worksheet: {w1["id"]}']

    # verify formulas works
    formula_generator = FormulaGenerator()

    for _ in range(random.randrange(1, 5)):
        formula_generator.generate_text()

    for _ in range(random.randrange(1, 5)):
        formula_generator.generate_formula()

    for _ in range(random.randrange(1, 5)):
        formula_generator.generate_special_formula()

    formula_generator.finalize()

    logs += [f'Generator cells: {formula_generator.cells}']

    try:
        w1 = ch.save_worksheet(w1['id'], list(map(lambda x: x[0], formula_generator.cells)))
    except RequestException:
        quit(Status.DOWN, 'Could not save worksheet', nice_logs(logs))

    logs += [f'Worksheet: {w1}']

    if w1['title'] != worksheet_title:
        quit(Status.DOWN, 'Wrong worksheet title', nice_logs(logs))
    elif not isinstance(w1['cells'], list) or len(w1['cells']) != len(formula_generator.cells):
        quit(Status.DOWN, 'Wrong worksheet cells', nice_logs(logs))

    for c, ec in formula_generator.cells:
        try:
            cc = next(filter(lambda x: x['x'] == c['x'] and x['y'] == c['y'], w1['cells']))
        except StopIteration:
            quit(Status.DOWN, 'Worksheet cell not found', nice_logs(logs, f'Worksheet cell: {c}'))

        if cc['content'] != c['content']:
            quit(Status.DOWN, 'Wrong worksheet cell', nice_logs(logs, f'Cell content: {c} != {cc}'))

        if ec is not None and ec.encode().hex() != cc['evaluated']:
            quit(Status.DOWN, 'Wrong worksheet cell', nice_logs(logs, f'Cell evaluated: {ec} != {cc}'))


def check_sla_4(host):
    ch = Challenge(f'{host}:8000')

    username, password = rand_str(), rand_str()
    worksheet_title = rand_str()

    logs = [f'Username: {username}', f'Password: {password}', f'Worksheet title: {worksheet_title}']

    try:
        ch.register_and_login(username, password)
    except (RequestException, LoginError):
        quit(Status.DOWN, 'Could not register/login', nice_logs(logs))

    try:
        w1 = ch.create_worksheet(worksheet_title, False)
    except RequestException:
        quit(Status.DOWN, 'Could not create worksheet', nice_logs(logs))

    logs += [f'Worksheet: {w1["id"]}']

    comment_x, comment_y = random.randrange(0, 64), random.randrange(0, 64)
    comment_content = rand_str()

    logs += [f'Comment: {comment_x} {comment_y} {comment_content}']

    try:
        c1 = ch.create_comment(w1['id'], comment_x, comment_y, comment_content)
    except RequestException:
        quit(Status.DOWN, 'Could not create worksheet comment', nice_logs(logs))

    logs += [f'Comment: {c1["id"]}']

    try:
        w1 = ch.get_worksheet(w1['id'])
    except RequestException:
        quit(Status.DOWN, 'Could not get worksheet', nice_logs(logs))

    if w1['title'] != worksheet_title:
        quit(Status.DOWN, 'Wrong worksheet title', nice_logs(logs, f'Worksheet: {w1}'))
    elif not isinstance(w1['comments'], list) or len(w1['comments']) != 1:
        quit(Status.DOWN, 'Wrong worksheet comments', nice_logs(logs, f'Worksheet comments: {w1["comments"]}'))
    elif (w1['comments'][0]['id'] != c1['id'] or w1['comments'][0]['x'] != comment_x or
          w1['comments'][0]['y'] != comment_y or w1['comments'][0]['content'] != comment_content or
          w1['comments'][0]['owner']['username'] != username):
        quit(Status.DOWN, 'Wrong worksheet comment', nice_logs(logs, f'Worksheet comments: {w1["comments"]}'))


def check_sla_5(host):
    ch1, ch2 = Challenge(f'{host}:8000'), Challenge(f'{host}:8000')

    username1, password1 = rand_str(), rand_str()
    username2, password2 = rand_str(), rand_str()

    worksheet_title = rand_str()

    logs = [f'Username 1: {username1}', f'Password 1: {password1}',
            f'Username 2: {username2}', f'Password 2: {password2}',
            f'Worksheet title: {worksheet_title}']

    try:
        ch1.register_and_login(username1, password1)
    except (RequestException, LoginError):
        quit(Status.DOWN, 'Could not register/login', nice_logs(logs))

    try:
        w1 = ch1.create_worksheet(worksheet_title, True)
    except RequestException:
        quit(Status.DOWN, 'Could not create worksheet', nice_logs(logs))

    formula_generator = FormulaGenerator()
    if random.choice([True, False]):
        for _ in range(random.randrange(1, 3)):
            formula_generator.generate_text()

        for _ in range(random.randrange(1, 3)):
            formula_generator.generate_formula()

        for _ in range(random.randrange(1, 3)):
            formula_generator.generate_special_formula()

        formula_generator.finalize()

    logs += [f'Generator cells: {formula_generator.cells}']

    try:
        w1 = ch1.save_worksheet(w1['id'], list(map(lambda x: x[0], formula_generator.cells)))
    except RequestException:
        quit(Status.DOWN, 'Could not save worksheet', nice_logs(logs))

    logs += [f'Worksheet 1: {w1["id"]}']

    comments = []
    for _ in range(random.randrange(1, 5)):
        comment_x, comment_y, comment_content = random.randrange(0, 64), random.randrange(0, 64), rand_str()
        comments.append((comment_x, comment_y, comment_content))

        try:
            ch1.create_comment(w1['id'], comment_x, comment_y, comment_content)
        except RequestException:
            quit(Status.DOWN, 'Could not create worksheet comment', nice_logs(logs))

    logs += [f'Comments 1: {comments}']

    try:
        ch2.register_and_login(username2, password2)
    except (RequestException, LoginError):
        quit(Status.DOWN, 'Could not register/login', nice_logs(logs))

    try:
        s1 = ch1.share_worksheet(w1['id'])
    except RequestException:
        quit(Status.DOWN, 'Could not share worksheet', nice_logs(logs))

    logs += [f'Share: {s1["token"]}']

    try:
        ch2.accept_worksheet_invite(w1['id'], s1['token'])
    except RequestException:
        quit(Status.DOWN, 'Could not accept worksheet invite', nice_logs(logs))

    for _ in range(random.randrange(1, 5)):
        comment_x, comment_y, comment_content = random.randrange(0, 64), random.randrange(0, 64), rand_str()
        comments.append((comment_x, comment_y, comment_content))

        try:
            ch2.create_comment(w1['id'], comment_x, comment_y, comment_content)
        except RequestException:
            quit(Status.DOWN, 'Could not create worksheet comment', nice_logs(logs))

    logs += [f'Comments 2: {comments}']

    try:
        w2 = ch2.get_worksheet(w1['id'])
    except RequestException:
        quit(Status.DOWN, 'Could not get worksheet', nice_logs(logs))

    logs += [f'Worksheet 2: {w2}']

    if w1['title'] != w2['title'] or w2['title'] != worksheet_title:
        quit(Status.DOWN, 'Wrong worksheet title', nice_logs(logs))

    for c, ec in formula_generator.cells:
        try:
            cc = next(filter(lambda wc: wc['x'] == c['x'] and wc['y'] == c['y'], w2['cells']))
        except StopIteration:
            quit(Status.DOWN, 'Worksheet cell not found', nice_logs(logs, f'Worksheet cell: {c}'))

        if cc['content'] != c['content']:
            quit(Status.DOWN, 'Wrong worksheet cell', nice_logs(logs, f'Cell content: {c} != {cc}'))

        if ec is not None and ec.encode().hex() != cc['evaluated']:
            quit(Status.DOWN, 'Wrong worksheet cell', nice_logs(logs, f'Cell evaluated: {ec} != {cc}'))

    for c in comments:
        try:
            next(filter(lambda x: x['x'] == c[0] and x['y'] == c[1] and x['content'] == c[2], w2['comments']))
        except StopIteration:
            quit(Status.DOWN, 'Worksheet comment not found', nice_logs(logs, f'Worksheet cell: {c}'))


def check_sla(host):
    checks = [check_sla_1, check_sla_2, check_sla_3, check_sla_4, check_sla_5]
    for check in random.choices(checks, k=random.randrange(2, len(checks))):
        check(host)


def put_flag(host, flag):
    ch = Challenge(f'{host}:8000')

    username, password = rand_str(), rand_str()
    worksheet_title = rand_str()
    cell_x, cell_y = random.randrange(0, 64), random.randrange(0, 64)

    logs = [f'Username: {username}', f'Password: {password}', f'Worksheet title: {worksheet_title}',
            f'Cell: {cell_x} {cell_y}', f'Flag: {flag}']

    try:
        ch.register_and_login(username, password)
    except (RequestException, LoginError):
        quit(Status.DOWN, 'Could not register/login', nice_logs(logs))

    try:
        w = ch.create_worksheet(worksheet_title, True)
    except RequestException:
        quit(Status.DOWN, 'Could not create worksheet', nice_logs(logs))

    logs += [f'Worksheet: {w["id"]}']

    try:
        ch.create_comment(w['id'], cell_x, cell_y, flag)
    except RequestException:
        quit(Status.DOWN, 'Could not create comment', nice_logs(logs))

    # Post flag id to game server
    try:
        post_flag_id('ExCCel-2', team_id, {'worksheet_id' : w['id'], 'owner_name' : username})
    except Exception:
        quit(Status.ERROR, 'Failed to post flag id', nice_logs(logs))

    with open(f'data/{hashlib.md5(flag.encode()).hexdigest()}', 'w') as f:
        json.dump({
            'username': username,
            'password': password,
            'worksheet_id': w['id'],
            'cell_x': cell_x,
            'cell_y': cell_y
        }, f)


def get_flag(host, flag):
    ch = Challenge(f'{host}:8000')

    with open(f'data/{hashlib.md5(flag.encode()).hexdigest()}', 'r') as f:
        flag_data = json.load(f)

    logs = [f'Flag data: {flag_data}']

    try:
        ch.login(flag_data['username'], flag_data['password'])
    except (RequestException, LoginError):
        quit(Status.DOWN, 'Could not login', nice_logs(logs))

    try:
        w = ch.get_worksheet(flag_data['worksheet_id'])
    except RequestException:
        quit(Status.DOWN, 'Could not get worksheet', nice_logs(logs))

    for comment in w['comments']:
        if comment['x'] == flag_data['cell_x'] and comment['y'] == flag_data['cell_y'] and comment['content'] == flag:
            break
    else:
        quit(Status.DOWN, 'Could not find flag in comments', nice_logs(logs, f'Comments: {w["comments"]}'))


if __name__ == '__main__':
    data = get_data()
    action = data['action']
    team_id = data['teamId']
    host = '10.60.' + team_id + '.1'

    if action == Action.CHECK_SLA.name:
        try:
            check_sla(host)
        except Exception:
            quit(Status.DOWN, 'Cannot check SLA', traceback.format_exc())
    elif action == Action.PUT_FLAG.name:
        flag = data['flag']
        try:
            put_flag(host, flag)
        except Exception:
            quit(Status.DOWN, "Cannot put flag", traceback.format_exc())
    elif action == Action.GET_FLAG.name:
        flag = data['flag']
        try:
            get_flag(host, flag)
        except Exception:
            quit(Status.DOWN, "Cannot get flag", traceback.format_exc())
    else:
        quit(Status.ERROR, 'System error', 'Unknown action: ' + action)

    quit(Status.OK, 'OK')
