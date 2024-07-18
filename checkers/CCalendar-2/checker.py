#!/usr/bin/env python3

from checklib import *
import random
import os
import string
from traceback import print_exc
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, Union

from chall import Challenge, Invite, ConstraintException, BackendError


def rand_str(length: int = 10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def rand_username():
    choice = random.randint(0, 2)
    if choice == 0:
        return ''.join(random.choices(string.ascii_letters, k=random.randint(6, 9))) \
            + ''.join(random.choices(string.digits, k=random.randint(2, 5)))
    elif choice == 1:
        return ''.join(random.choices(string.ascii_letters + string.digits,
            k=random.randint(8, 13)))
    else:
        return ''.join(random.choices(string.ascii_letters, k=random.randint(8, 13)))


def rand_password():
    return ''.join(random.choices(string.ascii_letters + string.digits,
        k=random.randint(8, 13)))


def rand_future_date(max_days_in_future: int = 3650):
    return datetime.now() + timedelta(days=random.randint(0, max_days_in_future))


def rand_range_iter(mmin: int, mmax: int) -> range:
    return range(random.randint(mmin, mmax))


def chance(percentage: int) -> bool:
    return random.randint(1, 100) <= percentage


def send_rand_invite(from_client: Challenge,
                     to_username: str,
                     dry_run: bool=False,
                     bad_date: bool=False,
                     bad_chars: bool=False,
                     expect_error: bool=False) -> Optional[Invite]:
    if bad_date or bad_chars:
        assert expect_error, 'Bad chars/date but not expecting an error? BRUH'

    title = rand_str(random.randint(10, 250))
    descr = rand_str(random.randint(10, 250))

    if bad_chars:
        chars = ''.join(random.choices('/=`|\t', k=random.randint(1, 3)))

        if chance(50):
            i = random.randint(0, len(title) - 1)
            title = title[:i] + chars + title[i:]
        else:
            i = random.randint(0, len(title) - 1)
            descr = descr[:i] + chars + descr[i:]

    d = rand_future_date()
    details = [title, descr, d.year, d.month, d.day]

    if bad_date:
        # Generate a bad year OR month OR day
        ibad = random.randint(2, 4)
        if ibad == 2:
            vbad = random.randint(0, 1969)
        elif ibad == 3:
            vbad = random.randint(13, 99)
        else:
            vbad = random.randint(32, 99)

        details[ibad] = vbad

    # For get_flag()
    if dry_run:
        return

    inv_id = from_client.create_invite(to_username, *details, expect_error=expect_error)
    if not expect_error:
        return Invite(inv_id, from_client.username, to_username, *details)


def register_and_login(host: str, username: Optional[str]=None,
                       password: Optional[str]=None) -> Challenge:
    c = Challenge(f'{host}:8443')

    if username is None:
        username = rand_username()
    if password is None:
        password = rand_password()

    # Register
    try:
        c.register(username, password)
    except ConstraintException as e:
        quit(Status.DOWN, 'Could not register', 'error while registering: ' + str(e))
    except Exception as e:
        quit(Status.DOWN, 'Could not register', str(e))

    # Login
    try:
        c.login(username, password)
    except ConstraintException as e:
        quit(Status.DOWN, 'Could not login', 'error while logging in: ' + str(e))
    except Exception as e:
        quit(Status.DOWN, 'Could not login', str(e))

    return c


def get_flag_data(flag) -> Tuple[Tuple[str,str],Tuple[str,str],datetime]:
    random.seed(flag)
    usernames = (rand_username(), rand_username())
    passwords = (rand_password(), rand_password())

    invite_date = rand_future_date()
    if invite_date.day < 10:
        dmax = 28 if invite_date.month == 2 else (30 if invite_date.month in (4, 6, 9, 11) else 31)
        delta_min = 10 - invite_date.day
        delta_max = dmax - invite_date.day
        invite_date += timedelta(days=random.randint(delta_min, delta_max))

    assert invite_date.day >= 10, f'Bad flag invite day: {invite_date.day}'

    # Do not reset random.seed(), it's needed by the caller
    return usernames, passwords, invite_date


def check_sla(host: str):
    # Make things reproducible
    rnd_seed = os.getenv('RND_SEED', os.urandom(8).hex())
    print(f'SLA {rnd_seed=}', file=sys.stderr)
    random.seed(rnd_seed)

    try:
        # Login/register checks same as store 1
        ch1 = Challenge(f'{host}:8443')

        # Check registration
        username, password = rand_username(), rand_password()
        try:
            ch1.register(username, password)
        except ConstraintException as e:
            quit(Status.DOWN, 'Could not register',
                'error while registering: ' + repr(e))
        except Exception as e:
            quit(Status.DOWN, 'Could not register', repr(e))

        # Randomly check you cannot register same user twice
        if random.randint(0, 2) == 0:
            try:
                ch1.register(username, password)
                quit(Status.DOWN, 'Could not register',
                    'no unique check failed for the registration process')
            except ConstraintException as e:
                pass
            except Exception as e:
                quit(Status.DOWN, 'Could not register', repr(e))

        # Randomly check login works as intended
        if random.randint(0, 1):
            try:
                ch1.login(username if chance(50) else rand_username(), rand_password())
                quit(Status.DOWN, 'Wrong login',
                    'login went through with the wrong password')
            except ConstraintException as e:
                pass
            except Exception as e:
                quit(Status.DOWN, 'Could not login', repr(e))

        # Check login
        try:
            r = ch1.login(username, password)
            r = ch1.get_home()

            if not f'Welcome back, {username}' in r:
                quit(Status.DOWN, 'Could not login',
                    'no welcome message after login')
        except ConstraintException as e:
            quit(Status.DOWN, 'Could not login',
                'error while logging in: ' + repr(e))
        except Exception as e:
            quit(Status.DOWN, 'Could not login', 'x' + repr(e))

        # Actual store 2 checks (reuse ch1 client)
        clients = [ch1, register_and_login(host)]
        invites_to: Dict[Challenge,Tuple[str,Invite]] = {clients[0]: [], clients[1]: []}
        invites_from: Dict[Challenge,Tuple[str,Invite]] = {clients[0]: [], clients[1]: []}
        invites_by_id: Dict[str,Invite] = {}
        plan: Tuple[Challenge,Union[Challenge,str],bool,bool] = []

        # Some invites between the two users
        for _ in rand_range_iter(1, 16):
            random.shuffle(clients)
            plan.append((*clients, False, False))

        # Some invites to random and possibly non-existing users (these will not
        # be retrievable in the future)
        for _ in rand_range_iter(1, 4):
            plan.append((random.choice(clients), rand_username(), False, False))

        # Some invites to oneself (that should fail)
        for _ in rand_range_iter(1, 2):
            plan.append((random.choice(clients), None, False, False))

        # Some invites with invalid date or bad chars (that should fail)
        for _ in rand_range_iter(1, 2):
            random.shuffle(clients)
            v = random.randint(1, 3)
            plan.append((*clients, bool(v & 1), bool(v & 2)))

        random.shuffle(plan)

        for sender, receiver, bad_date, bad_chars in plan:
            if bad_date or bad_chars:
                # Clients inviting each other with bad date or bad chars in
                # params
                send_rand_invite(sender, sender.username,
                    bad_date=bad_date, bad_chars=bad_chars, expect_error=True)
            elif receiver is None:
                # Client inviting itself
                send_rand_invite(sender, sender.username, expect_error=True)
            elif isinstance(receiver, Challenge):
                # Clients inviting each other
                inv = send_rand_invite(sender, receiver.username)
                invites_by_id[inv.id] = inv
                invites_from[sender].append(inv)
                invites_to[receiver].append(inv)
            else:
                # Client inviting a random username
                assert isinstance(receiver, str), f'Sending invite to WHAT? {receiver=}'
                inv = send_rand_invite(sender, receiver)
                invites_from[sender].append(inv)

        # Check that all invites with to= one of the two users (and not a random
        # non-existing username) can now be correctly retrieved
        server_invites = clients[0].get_invites() + clients[1].get_invites()
        for s_inv in server_invites:
            inv = invites_by_id.get(s_inv.id)

            if inv is None:
                quit(Status.DOWN, 'Sent invite was lost',
                    'Lost invite\n'
                    f'Exists only on server: {s_inv=}\n{invites_by_id=}')

            if inv != s_inv:
                quit(Status.DOWN, 'Sent invite was modified',
                    f'Modified invite\n{inv=}\nVS\n{s_inv=}\n{invites_by_id=}')

        # Also check filtering by date
        it = iter(invites_by_id.values())
        for _ in rand_range_iter(1, len(invites_by_id)):
            inv = next(it)

            if inv.user_to == clients[0].username:
                server_invites = clients[0].get_invites(inv.year, inv.month, inv.day)
            else:
                server_invites = clients[1].get_invites(inv.year, inv.month, inv.day)

            for s_inv in server_invites:
                if s_inv.id == inv.id:
                    break
            else:
                quit(Status.DOWN, 'Sent invite was lost',
                    'Lost invite (filter by date)\n'
                    f'Does not exist on server: {inv=}\n{invites_by_id=}')

            if inv != s_inv:
                quit(Status.DOWN, 'Sent invite was modified',
                    'Modified invite (filter by date)\n'
                    f'{inv=}\nVS\n{s_inv=}\n\n{invites_by_id=}')

        handled_invites = set()
        accepted_invites = []

        # Randomly accept/decline some of the received invites
        for client, received in invites_to.items():
            if not received:
                continue

            random.shuffle(received)
            for _ in range(random.randint(1, len(received))):
                inv = received.pop()
                handled_invites.add(inv)

                if chance(50):
                    accepted_invites.append(inv)
                    client.accept_invite(inv.id, inv.title, inv.description,
                        inv.year, inv.month, inv.day)
                else:
                    client.delete_invite(inv.id)

        # Eandomly delete some of the sent invites and also implicitly check
        # that deleting an already-deleted invite correctly returns error
        for client, sent in invites_from.items():
            if not sent:
                continue

            random.shuffle(sent)
            for _ in rand_range_iter(1, len(sent)):
                client.delete_invite(inv.id, expect_error=inv in handled_invites)
                handled_invites.add(inv.id)

        # Aheck that all handled invites were removed
        server_invites = clients[0].get_invites() + clients[1].get_invites()
        for s_inv in server_invites:
            if s_inv.id in handled_invites:
                quit(Status.DOWN, 'Deleted invite still present',
                    f'Immortal invite\n{s_inv=}\n{handled_invites=}\n'
                    f'{server_invites=}\n{invites_by_id=}')

        # Check that accepted invites are now events
        events = clients[0].get_events() + clients[1].get_events()
        for inv in accepted_invites:
            for evt in events:
                if evt[1:] == inv[3:]:
                    break
            else:
                quit(Status.DOWN, 'Event from accepted invite was lost',
                    f'Ghost invite\n{inv=}\n{accepted_invites=}\n'
                    f'{events=}\n{invites_by_id=}')
    except BackendError as e:
        # This one can be shown in scoreboard
        quit(Status.DOWN, str(e), repr(e))
    except AssertionError as e:
        # This is definitely our fault!
        quit(Status.ERROR, 'Checker internal error', repr(e))
    except Exception as e:
        # Could technically also be our fault, but treat it as a SLA fail
        print_exc(file=sys.stderr)
        quit(Status.DOWN, 'SLA check failed', repr(e))

    # All good!
    quit(Status.OK, 'OK')


def put_flag(host, team_id, flag):
    try:
        usernames, passwords, inv_date = get_flag_data(flag)
        assert inv_date.day >= 10, f'Bad flag date? {inv_date=}'

        clients = [
            register_and_login(host, usernames[0], passwords[0]),
            register_and_login(host, usernames[1], passwords[1])
        ]
        assert clients[0].username == usernames[0], f'Username mismatch: {clients[0].username=} VS {usernames[0]=}'
        assert clients[1].username == usernames[1], f'Username mismatch: {clients[1].username=} VS {usernames[1]=}'

        random.shuffle(clients)
        flag_sender, flag_receiver = clients

        # Send some random invites, possibly to random non-existing usernames too
        for _ in rand_range_iter(0, 8):
            random.shuffle(clients)

            if chance(50):
                send_rand_invite(clients[0], rand_username())
            else:
                send_rand_invite(clients[0], clients[1].username)

        # Send flag
        inv_title = rand_str(random.randint(10, 250))
        flag_sender.create_invite(flag_receiver.username, inv_title, flag,
            inv_date.year, inv_date.month, inv_date.day)

        # Send more random invites, possibly to random non-existing usernames too
        for _ in rand_range_iter(0, 8):
            random.shuffle(clients)

            if chance(50):
                send_rand_invite(clients[0], rand_username())
            else:
                send_rand_invite(clients[0], clients[1].username)

        # Post flag ID to game server
        try:
            post_flag_id('CCalendar-2', team_id, {
                'username': flag_receiver.username,
                'date': inv_date.strftime('%Y-%m-%d')
            })
        except Exception as e:
            # Our fault
            print_exc(file=sys.stderr)
            quit(Status.ERROR, 'Failed to post flag ID', repr(e))
    except Exception as e:
        # Could technically also be our fault
        print_exc(file=sys.stderr)
        quit(Status.DOWN, 'PUT FLAG check failed', repr(e))

    quit(Status.OK, 'OK')


def get_flag(host, flag):
    try:
        usernames, passwords, inv_date = get_flag_data(flag)
        assert inv_date.day >= 10, f'Bad flag date? {inv_date=}'

        clients = [Challenge(f'{host}:8443'), Challenge(f'{host}:8443')]
        clients[0].login(usernames[0], passwords[0])
        clients[1].login(usernames[1], passwords[1])
        assert clients[0].username == usernames[0], f'Username mismatch: {clients[0].username=} VS {usernames[0]=}'
        assert clients[1].username == usernames[1], f'Username mismatch: {clients[1].username=} VS {usernames[1]=}'

        random.shuffle(clients)
        flag_receiver = clients[1]

        # retrieve all invites and look for flag
        invs = flag_receiver.get_invites()
        if not invs:
            quit(Status.DOWN, 'Could not retrieve flag', 'No invites present')

        for inv in invs:
            if inv.description == flag:
                break
        else:
            quit(Status.DOWN, 'Could not retrieve flag',
                'Flag not in any invite description')

        # Also retrieve invites filterind by date and look for flag
        invs = flag_receiver.get_invites(
            inv_date.year, inv_date.month, inv_date.day)
        if not invs:
            quit(Status.DOWN, 'Could not retrieve flag',
                'No invites present (filter by date)')

        for inv in invs:
            if inv.description == flag:
                break
        else:
            quit(Status.DOWN, 'Could not retrieve flag',
                'Flag not in any invite description (filter by date)')
    except Exception as e:
        # Could technically also be our fault
        print_exc(file=sys.stderr)
        quit(Status.DOWN, 'GET FLAG check failed', repr(e))

    quit(Status.OK, 'OK')


if __name__ == '__main__':
    data = get_data()
    action = data['action']
    team_id = data['teamId']
    host = 'localhost' if 'LOCALHOST' in os.environ else '10.60.' + team_id + '.1'

    if action == Action.CHECK_SLA.name:
        try:
            check_sla(host)
        except Exception as e:
            quit(Status.DOWN, 'Cannot check SLA', repr(e))
    elif action == Action.PUT_FLAG.name:
        flag = data['flag']
        try:
            put_flag(host, team_id, flag)
        except Exception as e:
            quit(Status.DOWN, "Cannot put flag", repr(e))
    elif action == Action.GET_FLAG.name:
        flag = data['flag']
        try:
            get_flag(host, flag)
        except Exception as e:
            quit(Status.DOWN, "Cannot get flag", repr(e))
    else:
        # Most likely our fault
        print_exc(file=sys.stderr)
        quit(Status.ERROR, 'System error', 'Unknown action: ' + action)

    quit(Status.OK)
