#!/usr/bin/env python3

from checklib import *
import random
import os
import string
from chall import Challenge, ConstraintException
import uuid
import re


def rand_str(length: int = 10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def rand_username():
    choice = random.randint(0, 2)
    if choice == 0:
        return ''.join(random.choices(string.ascii_letters, k=random.randint(
            6, 9))) + ''.join(random.choices(string.digits, k=random.randint(2, 5)))
    elif choice == 1:
        return ''.join(random.choices(
            string.ascii_letters + string.digits, k=random.randint(8, 13)))
    else:
        return ''.join(random.choices(string.ascii_letters, k=random.randint(8, 13)))


def rand_password():
    return ''.join(random.choices(string.ascii_letters +
                                  string.digits, k=random.randint(8, 13)))


def get_flag_data(flag):
    random.seed(flag)
    username = rand_username()
    password = rand_password()
    random.seed(os.urandom(8))
    return username, password


def check_sla(host):
    try:
        ch1 = Challenge(f'{host}:8443')

        ch2 = Challenge(f'{host}:8443')
        r = ch2.get_home()

        try:
            static_files = re.findall('"/static/(.+)"', r)
            assert 'css/style.css' in static_files and 'js/jquery.min.js' in static_files and \
                'js/popper.js' in static_files and 'js/bootstrap.min.js' in static_files
            for f in static_files:
                ch1.check_static_file(f)
        except Exception as e:
            quit(Status.DOWN, 'Missing website features', 'Failed to check the presence of static files')


        # check registration
        username, password = rand_username(), rand_password()
        try:
            ch1.register(username, password)
        except ConstraintException as e:
            quit(Status.DOWN, 'Could not register',
                 'error while registering: ' + str(e))
        except Exception as e:
            quit(Status.DOWN, 'Could not register', str(e))

        # randomly check you cannot register same user twice
        if random.randint(0, 2) == 0:
            try:
                ch1.register(username, password)
                quit(Status.DOWN, 'Could not register',
                     'no unique check failed for the registration process')
            except ConstraintException as e:
                pass
            except Exception as e:
                quit(Status.DOWN, 'Could not register', str(e))

        # randomly check login works as intended
        if random.randint(0, 1):
            try:
                ch1.login(username if random.randint(0, 1)
                          else rand_username(), rand_password())
                quit(Status.DOWN, 'Wrong login',
                     'login went through with the wrong password')
            except ConstraintException as e:
                pass
            except Exception as e:
                quit(Status.DOWN, 'Could not login', str(e))

        # check login
        try:
            r = ch1.login(username, password)
            r = ch1.get_home()

            if not f'Welcome back, {username}' in r:
                quit(Status.DOWN, 'Could not login',
                     'no welcome message after login')
        except ConstraintException as e:
            quit(Status.DOWN, 'Could not login',
                 'error while logging in: ' + str(e))
        except Exception as e:
            quit(Status.DOWN, 'Could not login', str(e))

        # randomly check static files other there as well
        if random.randint(0,10) <= 3:
            ch3 = Challenge(f'{host}:8443')
            other_username, other_password = rand_username(), rand_password()
            ch3.register(other_username, other_password)
            ch3.login(other_username, other_password)

            r = ch3.get_home()

            try:
                static_files = re.findall('"/static/(.+)"', r)
                assert 'css/style.css' in static_files and 'js/jquery.min.js' in static_files and \
                    'js/popper.js' in static_files and 'js/bootstrap.min.js' in static_files and \
                    'js/main.js' in static_files
                for f in static_files:
                    ch1.check_static_file(f)
            except Exception as e:
                quit(Status.DOWN, 'Missing website features', 'Failed to check the presence of static files')

        # check get events
        try:
            events = ch1.get_events()
        except Exception as e:
            quit(Status.DOWN, 'Could not get events', str(e))

        if not len(events) == 0:
            quit(Status.DOWN, 'Could not get events',
                 'new user has some events???')

        # check create event
        title = rand_str(random.randint(10, 20))
        description = rand_str(random.randint(30, 40))
        year = 2024
        month = random.randint(7, 12)
        day = random.randint(1, 28)
        try:
            ch1.create_event(title, description, year, month, day)
        except Exception as e:
            quit(Status.DOWN, 'Could not create event', str(e))

        # retrieve the newly created event
        try:
            events = ch1.get_events()
        except Exception as e:
            quit(Status.DOWN, 'Could not get events', str(e))

        if not len(events) == 1:
            quit(Status.DOWN, 'Could not create event',
                 'new event is not in list')

        event = events[0]
        if event['title'] != title \
                or event['description'] != description \
                or event['year'] != year \
                or event['month'] != month \
                or event['day'] != day:
            quit(Status.DOWN, 'Could not create event', 'new event data is wrong')

        # randomly create multiple events
        event_num = 0
        if random.randint(0, 10) <= 3:
            event_num = random.randint(1, 4)
            for _ in range(event_num):
                title = rand_str(random.randint(10, 20))
                description = rand_str(random.randint(30, 40))
                year = 2024
                month = random.randint(7, 12)
                day = random.randint(1, 28)
                try:
                    ch1.create_event(title, description, year, month, day)
                except Exception as e:
                    quit(Status.DOWN, 'Could not create event', str(e))

            # retrieve the newly created event
            try:
                events = ch1.get_events()
            except Exception as e:
                quit(Status.DOWN, 'Could not get events', str(e))

            if not len(events) == 1 + event_num:
                quit(Status.DOWN, 'Could not create event',
                     'new event is not in list')

        #  randomly test event deletion
        if random.randint(0, 1):
            # randomly test deletion of non-existent event
            if random.randint(0, 2) == 0:
                try:
                    ch1.delete_event(str(uuid.uuid4()))
                    quit(Status.DOWN, 'Could not delete event',
                         'we managed to delete a non-existent event???')
                except Exception as e:
                    pass

            #  delete the event
            to_delete = random.randint(0, event_num)
            to_delete = events[to_delete]

            try:
                ch1.delete_event(to_delete['id'])
            except Exception as e:
                quit(Status.DOWN, 'Could not delete event', str(e))

            # get new event list
            try:
                new_events = ch1.get_events()
            except Exception as e:
                quit(Status.DOWN, 'Could not get events', str(e))

            #  verify events integrity
            if not len(new_events) == event_num:
                quit(Status.DOWN, 'Could not delete event',
                     'event was not deleted')

            old_events = [x['id'] for x in events]
            new_events = [x['id'] for x in new_events]

            for e in new_events:
                if not e in old_events:
                    quit(Status.DOWN, 'Could not delete event',
                         'where did this event come from??')

            if to_delete['id'] in new_events:
                quit(Status.DOWN, 'Could not delete event',
                     'event wasn\'t actually deleted??')

    except Exception as e:
        quit(Status.DOWN, 'SLA check failed', str(e))

    quit(Status.OK, 'OK')


def put_flag(host, team_id, flag):
    try:
        ch1 = Challenge(f'{host}:8443')

        username, password = get_flag_data(flag)

        # register
        try:
            ch1.register(username, password)
        except ConstraintException as e:
            quit(Status.DOWN, 'Could not register',
                 'error while registering: ' + str(e))
        except Exception as e:
            quit(Status.DOWN, 'Could not register',
                 'exception while registering ' + str(e))

        # login
        try:
            ch1.login(username, password)
        except ConstraintException as e:
            quit(Status.DOWN, 'Could not login',
                 'error while logging in: ' + str(e))
        except Exception as e:
            quit(Status.DOWN, 'Could not login', 'exception login ' + str(e))

        before_event_num = 0
        # randomly create multiple events
        if random.randint(0, 10) <= 3:
            before_event_num = random.randint(1, 4)
            for _ in range(before_event_num):
                title = rand_str(random.randint(10, 20))
                description = rand_str(random.randint(30, 40))
                year = 2024
                month = random.randint(7, 12)
                day = random.randint(1, 28)
                try:
                    ch1.create_event(title, description, year, month, day)
                except Exception as e:
                    quit(Status.DOWN, 'Could not insert flag', str(e))

            # retrieve the newly created event
            try:
                events = ch1.get_events()
            except Exception as e:
                quit(Status.DOWN, 'Could not insert flag', str(e))

            if not len(events) == before_event_num:
                quit(Status.DOWN, 'Could not insert flag',
                     'new event is not in list')

        # create event
        title = rand_str(random.randint(10, 20))
        description = flag
        year = 2024
        month = random.randint(7, 12)
        day = random.randint(1, 28)
        try:
            ch1.create_event(title, description, year, month, day)
        except Exception as e:
            quit(Status.DOWN, 'Could not insert flag',
                 'exception create event ' + str(e))

        after_event_num = 0
        # randomly create multiple events
        if random.randint(0, 10) <= 3:
            after_event_num = random.randint(1, 4)
            for _ in range(after_event_num):
                title = rand_str(random.randint(10, 20))
                description = rand_str(random.randint(30, 40))
                year = 2024
                month = random.randint(7, 12)
                day = random.randint(1, 28)
                try:
                    ch1.create_event(title, description, year, month, day)
                except Exception as e:
                    quit(Status.DOWN, 'Could not insert flag', str(e))

            # retrieve the newly created event
            try:
                events = ch1.get_events()
            except Exception as e:
                quit(Status.DOWN, 'Could not insert flag', str(e))

            if not len(events) == before_event_num + 1 + after_event_num:
                quit(Status.DOWN, 'Could not insert flag',
                     'new event is not in list')

        # retrieve the newly created event
        try:
            events = ch1.get_events()
        except Exception as e:
            quit(Status.DOWN, 'Could not insert flag',
                 'exception get events ' + str(e))

        if not len(events) == before_event_num + 1 + after_event_num:
            quit(Status.DOWN, 'Could not insert flag',
                 'new event is not in list')

        event = events[before_event_num]
        if event['description'] != flag:
            quit(Status.DOWN, 'Could not insert flag',
                 'flag event data is wrong')

        # Post flag id to game server
        try:
            post_flag_id('CCalendar-1', team_id, {'username': username})
        except Exception as e:
            quit(Status.ERROR, 'Failed to post flag ID', str(e))
    except Exception as e:
        quit(Status.DOWN, 'PUT FLAG check failed', str(e))

    quit(Status.OK, 'OK')


def get_flag(host, flag):
    try:
        ch1 = Challenge(f'{host}:8443')

        username, password = get_flag_data(flag)

        # login
        try:
            ch1.login(username, password)
        except ConstraintException as e:
            quit(Status.DOWN, 'Could not login',
                 'error while logging in: ' + str(e))
        except Exception as e:
            quit(Status.DOWN, 'Could not login', 'exception login ' + str(e))

        # retrieve the event
        try:
            events = ch1.get_events()
        except Exception as e:
            quit(Status.DOWN, 'Could not retrieve flag',
                 'exception get events ' + str(e))

        if len(events) == 0:
            quit(Status.DOWN, 'Could not retrieve flag', 'event list is empty')

        for event in events:
            if event['description'] == flag:
                break
        else:
            quit(Status.DOWN, 'Could not retrieve flag', 'flag is not in event list')
    except Exception as e:
        quit(Status.DOWN, 'GET FLAG check failed', str(e))

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
            quit(Status.DOWN, 'Cannot check SLA', str(e))
    elif action == Action.PUT_FLAG.name:
        flag = data['flag']
        try:
            put_flag(host, team_id, flag)
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

    quit(Status.OK)
