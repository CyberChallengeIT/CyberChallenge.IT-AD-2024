#!/usr/bin/env python3

from checklib import *
import random
import string
from client import Client
import traceback

PORT = 1337
alphabet = string.ascii_letters + string.digits


def get_random_str(len):
    return ''.join(random.choice(alphabet) for i in range(len))


def check_mailing_list_creation():
    num_lists = random.randint(1, 5)
    c = Client(host, PORT)
    name, surname, email, password = [get_random_str(random.randint(8, 20)) for _ in range(4)]
    email += "@cc.it"
    c.connect()
    c.register(name, surname, email, password)
    lists = []
    for i in range(num_lists):
        ml_name, ml_desc = [get_random_str(random.randint(8, 20)), get_random_str(random.randint(8, 200))]
        lists.append((ml_name, ml_desc))
        c.create_mailinglist(ml_name, ml_desc)
    check = True
    result = c.get_mailinglists()
    for i in range(num_lists):
        check = check and any([((result["mailinglists"][ml]["name"] == lists[i][0]) and (result["mailinglists"][ml]["description"] == lists[i][1])) for ml in result["mailinglists"]])
    return check, [result, lists]


def check_mailing_list_send():
    num_clients = random.randint(1, 5)
    clients = []
    c1 = Client(host, PORT)
    name, surname, email, password = [get_random_str(random.randint(8, 20)) for _ in range(4)]
    email += "@cc.it"
    c1.connect()
    c1.register(name, surname, email, password)
    ml_name, ml_desc = [get_random_str(random.randint(8, 20)), get_random_str(random.randint(8, 200))]
    c1.create_mailinglist(ml_name, ml_desc)
    for i in range(num_clients):
        ci = Client(host, PORT)
        clients.append(ci)
        name, surname, email, password = [get_random_str(random.randint(8, 20)) for _ in range(4)]
        email += "@cc.it"
        ci.connect()
        ci.register(name, surname, email, password)
        ci.get_mailinglists()
        ci.join_mailinglist(ml_name)
    
    subject, content = get_random_str(random.randint(8, 20)), get_random_str(random.randint(10, 100))
    c1.send_mail(ml_name, subject, content)

    check = False
    for ci in clients:
        result = ci.get_folder("inbox")
        for id in result["email_ids"]:
            if result["metadata"][id]["subject"] == subject:
                email = ci.get_email("inbox", id)
                return email["content"] == content, [email, subject, content]
    
    return check, [result, subject, content]


def check_mailing_list_subscription_single_creator():
    num_subs = random.randint(1, 5)
    c1 = Client(host, PORT)
    name, surname, email, password = [get_random_str(random.randint(8, 20)) for _ in range(4)]
    email += "@cc.it"
    c1.connect()
    c1.register(name, surname, email, password)
    lists = []
    for i in range(num_subs):
        ml_name, ml_desc = [get_random_str(random.randint(8, 20)), get_random_str(random.randint(8, 200))]
        c1.create_mailinglist(ml_name, ml_desc)
        lists.append((ml_name, ml_desc))
    c1.logout()
    random.shuffle(lists)
    c2 = Client(host, PORT)
    name, surname, email, password = [get_random_str(random.randint(8, 20)) for _ in range(4)]
    email += "@cc.it"
    c2.connect()
    c2.register(name, surname, email, password)
    c2.get_mailinglists()
    for i in range(num_subs):
        c2.join_mailinglist(lists[i][0])

    check = True
    result = c2.get_user_mailinglists()
    for i in range(num_subs):
        check = check and (any([((result["mailinglists"][ml]["name"] == lists[i][0]) and (result["mailinglists"][ml]["description"] == lists[i][1])) for ml in result["mailinglists"]]))
    return check, [result, lists]


def check_mailing_list_subscription_multiple_creators():
    num_subs = random.randint(1, 5)
    lists = []
    for i in range(num_subs):
        c1 = Client(host, PORT)
        name, surname, email, password = [get_random_str(random.randint(8, 20)) for _ in range(4)]
        email += "@cc.it"
        c1.connect()
        c1.register(name, surname, email, password)
        ml_name, ml_desc = [get_random_str(random.randint(8, 20)), get_random_str(random.randint(8, 200))]
        c1.create_mailinglist(ml_name, ml_desc)
        lists.append((ml_name, ml_desc))
        c1.logout()
    random.shuffle(lists)
    c2 = Client(host, PORT)
    name, surname, email, password = [get_random_str(random.randint(8, 20)) for _ in range(4)]
    email += "@cc.it"
    c2.connect()
    c2.register(name, surname, email, password)
    c2.get_mailinglists()
    for i in range(num_subs):
        c2.join_mailinglist(lists[i][0])

    check = True
    result = c2.get_user_mailinglists()
    for i in range(num_subs):
        check = check and (any([((result["mailinglists"][ml]["name"] == lists[i][0]) and (result["mailinglists"][ml]["description"] == lists[i][1])) for ml in result["mailinglists"]]))
    return check, [result, lists]


def check_mailing_list_ownership():
    num_lists = random.randint(1, 5)
    c1 = Client(host, PORT)
    name, surname, email, password = [get_random_str(random.randint(8, 20)) for _ in range(4)]
    email += "@cc.it"
    c1.connect()
    c1.register(name, surname, email, password)
    lists = []
    for i in range(num_lists):
        ml_name, ml_desc = [get_random_str(random.randint(8, 20)), get_random_str(random.randint(8, 200))]
        c1.create_mailinglist(ml_name, ml_desc)
        lists.append((ml_name, ml_desc))
    check = True
    result = c1.get_user_owned_mailinglists()
    for i in range(num_lists):
        check = check and (any([((result["mailinglists"][ml]["name"] == lists[i][0]) and (result["mailinglists"][ml]["description"] == lists[i][1])) for ml in result["mailinglists"]]))
    return check, [result, lists]


def check_mailing_list_users():
    num_subs = random.randint(1, 5)
    c1 = Client(host, PORT)
    name, surname, email, password = [get_random_str(random.randint(8, 20)) for _ in range(4)]
    email += "@cc.it"
    c1.connect()
    c1.register(name, surname, email, password)
    ml_name, ml_desc = [get_random_str(random.randint(8, 20)), get_random_str(random.randint(8, 200))]
    c1.create_mailinglist(ml_name, ml_desc)
    subs = []
    for i in range(num_subs):
        ci = Client(host, PORT)
        name, surname, email, password = [get_random_str(random.randint(8, 20)) for _ in range(4)]
        email += "@cc.it"
        ci.connect()
        ci.register(name, surname, email, password)
        ci.get_mailinglists()
        ci.join_mailinglist(ml_name)
        subs.append(email)
        ci.logout()
    result = c1.get_mailinglist_users(ml_name)
    return all([s in result["users"] for s in subs]), [result, subs]
    

def check_mailing_list_invite():
    num_subs = random.randint(1, 5)
    c1 = Client(host, PORT)
    name, surname, email, password = [get_random_str(random.randint(8, 20)) for _ in range(4)]
    email += "@cc.it"
    c1.connect()
    c1.register(name, surname, email, password)
    ml_name, ml_desc = [get_random_str(random.randint(8, 20)), get_random_str(random.randint(8, 200))]
    c1.create_mailinglist(ml_name, ml_desc)
    subs = []
    for i in range(num_subs):
        ci = Client(host, PORT)
        name, surname, email, password = [get_random_str(random.randint(8, 20)) for _ in range(4)]
        email += "@cc.it"
        ci.connect()
        ci.register(name, surname, email, password)
        subs.append(email)
    random.shuffle(subs)
    send_result = []
    for i in range(num_subs):
        send_result.append(c1.send_mail(subs[i], get_random_str(20), f"=====MAILING LIST INVITE=====\nYou are kindly invited to join my mailing list: {ml_name}\n=====MAILING LIST INVITE====="))
    result = c1.get_mailinglist_users(ml_name)
    return all([s in result["users"] for s in subs]), [result, subs, send_result]

def check_sla(host):

    # Check service functionality
    utils = [
        check_mailing_list_creation,
        check_mailing_list_send,
        check_mailing_list_subscription_single_creator,
        check_mailing_list_subscription_multiple_creators,
        check_mailing_list_ownership,
        check_mailing_list_users,
        check_mailing_list_invite,
        ]

    messages = {
        "check_mailing_list_creation": "Mailing list creation failed",
        "check_mailing_list_send": "Send to mailing list failed",
        "check_mailing_list_subscription_single_creator": "Mailing list subscription failed",
        "check_mailing_list_subscription_multiple_creators": "Mailing list subscription failed",
        "check_mailing_list_ownership": "Mailing list ownership check failed",
        "check_mailing_list_users": "Mailing list users check failed",
        "check_mailing_list_invite": "Mailing list invite failed",
    }
    
    random.shuffle(utils)
    for u in utils:
        try:
            check, data = u()
            if not check:
                quit(Status.DOWN, messages[u.__name__], str(data))
        except Exception:
            quit(Status.DOWN, messages[u.__name__], str(traceback.format_exc()))

    quit(Status.OK, 'OK')


def put_flag(host, flag):

    try:
        random.seed(flag.encode())
        # Generate flag_id for the flag, put the flag inside the service
        ml_name, ml_desc = [get_random_str(random.randint(8, 20)), get_random_str(random.randint(8, 200))]
        flag_id = {"mailinglist": ml_name}

        name, surname, email, password = [get_random_str(random.randint(8, 20)) for _ in range(4)]
        email += "@cc.it"
        c = Client(host, PORT)
        c.connect()
        c.register(name, surname, email, password)
        c.create_mailinglist(ml_name, ml_desc)
        name, surname, password = [get_random_str(random.randint(8, 20)) for _ in range(3)]
        email = flag
        c1 = Client(host, PORT)
        c1.connect()
        c1.register(name, surname, email, password)
        # c1.get_mailinglists()
        result = c1.join_mailinglist(ml_name)
        if result["result"] != "success":
            quit(Status.DOWN, "Cannot set flag", f"{flag}\n{result}")
    except Exception:    
            quit(Status.DOWN, "Cannot set flag", str(traceback.format_exc()) + f"\n{flag}")

    # Post flag id to game server
    try:
        post_flag_id('Inlook-2', team_id, flag_id)
    except Exception:
        quit(Status.ERROR, 'Failed to post flag id', str(traceback.format_exc()) + f"\n{flag}")

    quit(Status.OK, 'OK')


def get_flag(host, flag):

    # Generate flag_id for this flag, retrieve the flag from the service
    random.seed(flag.encode())
    ml_name, ml_desc = [get_random_str(random.randint(8, 20)), get_random_str(random.randint(8, 200))]
    name, surname, email, password = [get_random_str(random.randint(8, 20)) for _ in range(4)]
    email += "@cc.it"
    c = Client(host, PORT)
    c.connect()
    c.login(email, password)
    result = c.get_mailinglist_users(ml_name)
    if result["result"] != "success" or flag not in result["users"]:
        quit(Status.DOWN, "Cannot get flag", f"{flag}/{result}")

    quit(Status.OK, 'OK')


if __name__ == '__main__':
    data = get_data()
    action = data['action']
    team_id = data['teamId']
    host = '10.60.' + team_id + '.1'
    if 'LOCALHOST' in os.environ:
        host = '127.0.0.1'

    if action == Action.CHECK_SLA.name:
        try:
            check_sla(host)
        except Exception:
            quit(Status.DOWN, 'Cannot check SLA', str(traceback.format_exc()))
    elif action == Action.PUT_FLAG.name:
        flag = data['flag']
        try:
            put_flag(host, flag)
        except Exception:
            quit(Status.DOWN, "Cannot put flag", str(traceback.format_exc()))
    elif action == Action.GET_FLAG.name:
        flag = data['flag']
        try:
            get_flag(host, flag)
        except Exception:
            quit(Status.DOWN, "Cannot get flag", str(traceback.format_exc()))
    else:
        quit(Status.ERROR, 'System error', 'Unknown action: ' + action)

    quit(Status.OK)
