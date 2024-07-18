#!/usr/bin/env python3

import pygame
from modules.gui_utils import *
from modules.interfaces import *
from enum import Enum
from modules.client import Client

# Setup pygame
pygame.init()
pygame.key.set_repeat(200, 25)
pygame.display.set_caption("MacroHard Inlook")
pygame.display.set_icon(ICON)
CLOCK = pygame.time.Clock()
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))

textinputs = []
buttons = []

Status = Enum('Status', ['LOGGED_OUT', 'SIGNUP', 'LOGGED_IN', 'WRITING', 'SHOWML', 'CREATEML'])

def download_emails(client, data):
    result = client.get_folder(data["folder"])
    data["metadata"] = result["metadata"]
    data["email_ids"] = sorted(result["email_ids"], key=lambda id: data["metadata"][id]["timestamp"], reverse=True)
    data["emails"] = {}
    for email_id in data["email_ids"][:MAIL_LIMIT]:
        if email_id not in data["emails"]:
            content = client.get_email(data["folder"], email_id)
            data["emails"][email_id] = {k: v for k, v in data["metadata"][email_id].items()}
            data["emails"][email_id].update({"content": content["content"], "verified": content["result"]=="success"})


def download_mailinglists(client, data):
    result = client.get_mailinglists()
    data["mailinglists"] = {ml: result["mailinglists"][ml] for ml in list(result["mailinglists"].keys())[:MAILINGLISTS_LIMIT]}
    result = client.get_user_mailinglists()
    for ml in data["mailinglists"]:
        data["mailinglists"][ml]["subscripted"] = ml in result["mailinglists"]


def main():
    status = Status.LOGGED_OUT
    old_status = None
    client = None
    data = {}
    updated_data = False
    notification_message = ""
    error_message = ""

    while True:
        CLOCK.tick(FPS)

        if status != old_status or updated_data == True:
            updated_data = False
            SCREEN.fill(BG_COLOR)
            if status == Status.LOGGED_OUT:
                curr_interface = render_login_interface
            elif status == Status.SIGNUP:
                curr_interface = render_signup_interface
            elif status == Status.LOGGED_IN:
                curr_interface = render_base_interface
            elif status == Status.WRITING:
                curr_interface = render_writing_interface
            elif status == Status.SHOWML:
                curr_interface = render_showmailinglist_interface
            elif status == Status.CREATEML:
                curr_interface = render_createmailinglist_interface
            
            textinputs, buttons = curr_interface(SCREEN, data)
        
        if notification_message:
            render_banner(SCREEN, notification_message, NOTIFICATION_COLOR)
            notification_message = ""
        
        if error_message:
            render_banner(SCREEN, error_message, ERROR_COLOR)
            error_message = ""

        old_status = status

        events = pygame.event.get()
        for ti in textinputs:
            ti.render(events, SCREEN)
        
        render_buttons(SCREEN, pygame.mouse.get_pos(), buttons)

        for event in events:
            if event.type == pygame.QUIT:
                gui_quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for ti in textinputs:
                    ti.click(event.pos)
                if status == Status.LOGGED_OUT:
                    if buttons[0].checkForInput(event.pos):
                        email, password, server = [ti.value for ti in textinputs]
                        host, port = server.split(':')
                        client = Client(host, port)
                        client.connect()
                        result = client.login(email, password)
                        if result["result"] == "success":
                            data["name"] = result["name"]
                            data["surname"] = result["surname"]
                            data["email"] = email
                            data["server"] = server
                            data["folder"] = "inbox"
                            download_emails(client, data)
                            status = Status.LOGGED_IN
                        else:
                            error_message = result["error"]
                    elif buttons[1].checkForInput(event.pos):
                        status = Status.SIGNUP
                    
                elif status == Status.SIGNUP:
                    if buttons[0].checkForInput(event.pos):
                        status = Status.LOGGED_OUT
                    elif buttons[1].checkForInput(event.pos):
                        name, surname, email, password, server = [ti.value for ti in textinputs]
                        host, port = server.split(':')
                        client = Client(host, port)
                        client.connect()
                        result = client.register(name, surname, email, password)
                        if result["result"] == "success":
                            data["name"] = name
                            data["surname"] = surname
                            data["email"] = email
                            data["server"] = server
                            data["email_ids"] = []
                            data["metadata"] = {}
                            data["emails"] = {}
                            data["folder"] = "inbox"
                            status = Status.LOGGED_IN
                        else:
                            error_message = result["error"]

                elif status == Status.LOGGED_IN:
                    if buttons[0].checkForInput(event.pos):
                        client.close()
                        data = {}
                        status = Status.LOGGED_OUT
                    elif buttons[1].checkForInput(event.pos):
                        data["writeemail"] = {"recipient": "", "subject": "", "content": ""}
                        status = Status.WRITING
                    elif buttons[2].checkForInput(event.pos):
                        download_emails(client, data)
                        updated_data = True
                    elif buttons[3].checkForInput(event.pos):
                        download_mailinglists(client, data)
                        status = Status.SHOWML
                    elif buttons[4].checkForInput(event.pos):
                        status = Status.CREATEML
                    elif buttons[5].checkForInput(event.pos):
                        data["folder"] = "inbox"
                        download_emails(client, data)
                        updated_data = True
                    elif buttons[6].checkForInput(event.pos):
                        data["folder"] = "sent"
                        download_emails(client, data)
                        updated_data = True
                    else:
                        len_standardactions = 7
                        if "visualized_email" in data:
                            len_mailbuttons = 3
                        else:
                            len_mailbuttons = 0
                        for i in range(len(buttons)-len_standardactions-len_mailbuttons):
                            if buttons[len_standardactions+i].checkForInput(event.pos):
                                data["visualized_email"] = data["emails"][data["email_ids"][i]]
                                updated_data = True
                        if len_mailbuttons != 0:
                            if buttons[-3].checkForInput(event.pos):
                                data["writeemail"] = {"recipient": data["visualized_email"]["sender"], "subject": "RE: "+data["visualized_email"]["subject"], "content": f"\n{data['visualized_email']['sender']} wrote:\n"+data["visualized_email"]["content"]}
                                status = Status.WRITING
                            elif buttons[-1].checkForInput(event.pos):
                                data["writeemail"] = {"recipient": "", "subject": "FW: "+data["visualized_email"]["subject"], "content": f"\n{data['visualized_email']['sender']} wrote:\n"+data["visualized_email"]["content"]}
                                status = Status.WRITING

                elif status == Status.WRITING:
                    if buttons[0].checkForInput(event.pos):
                        recipient, subject, content = [ti.value for ti in textinputs]
                        result = client.send_mail(recipient, subject, content)
                        if result["result"] == "success":
                            notification_message = result["answer"]
                            status = Status.LOGGED_IN
                        else:
                            error_message = result["error"]

                    elif buttons[1].checkForInput(event.pos):
                        status = Status.LOGGED_IN

                elif status == Status.SHOWML:
                    if buttons[0].checkForInput(event.pos):
                        status = Status.LOGGED_IN
                    else:
                        for i, ml in enumerate(data["mailinglists"]):
                            if buttons[i+1].checkForInput(event.pos):
                                result = client.join_mailinglist(data["mailinglists"][ml]["name"])
                                if result["result"] == "success":
                                    download_mailinglists(client, data)
                                    updated_data = True
                                else:
                                    error_message = result["error"]

                elif status == Status.CREATEML:
                    if buttons[0].checkForInput(event.pos):
                        name, description = [ti.value for ti in textinputs]
                        result = client.create_mailinglist(name, description)
                        if result["result"] == "success":
                            download_mailinglists(client, data)
                            status = Status.SHOWML
                        else:
                            error_message = result["error"]
                    elif buttons[1].checkForInput(event.pos):
                        status = Status.LOGGED_IN


        pygame.display.flip()

def gui_quit():
        
    pygame.quit()
    exit()


if __name__ == "__main__":
    main()