#!/usr/bin/env python3

from modules.gui_utils import *


def render_base_interface(surface, data):
    render_image(surface, pygame.transform.scale(LOGO, (90, 30)), (40, 10))
	
    taskbar = pygame.Rect(50, 50, 1500, TASKBAR_HEIGHT)
    pygame.draw.rect(surface, TASKBAR_COLOR, taskbar, border_radius=BORDER_RADIUS)
    folders = pygame.Rect(50, 110, FOLDERS_WIDTH, 770)
    pygame.draw.rect(surface, STATUSBAR_COLOR, folders, border_top_left_radius=BORDER_RADIUS)
    maildetails = pygame.Rect(50+FOLDERS_WIDTH, 110, 1500-FOLDERS_WIDTH, 770)
    pygame.draw.rect(surface, MAILDETAILS_COLOR, maildetails, border_top_right_radius=BORDER_RADIUS)
    main_area_border = pygame.Rect(50, 110, 1500, 770)
    pygame.draw.rect(surface, MAIN_BORDER_COLOR, main_area_border, width=1, border_radius=BORDER_RADIUS)
    pygame.draw.line(surface, MAIN_BORDER_COLOR, (50+2*FOLDERS_WIDTH, 120), (50+2*FOLDERS_WIDTH, 870))
    statusbar = pygame.Rect(0, 870, 1600, 30)
    pygame.draw.rect(surface, STATUSBAR_COLOR, statusbar)
    pygame.draw.line(surface, STATUSBAR_BORDER_COLOR, (0, 870), (1600, 870))

    pygame.draw.circle(surface, ACCOUNT_COLOR, (1500, 25), 15)
    Text((data["name"][0] + data["surname"][0]).upper(), center=(1500, 25), font_size=15).render(surface)
    logout_button = Button(text_input="Logout", pos=(1523, 17), fontsize=15)
	
    render_image(surface, NEWEMAIL, (60, 60))
    newemail_button = Button(text_input="New Email", pos=(100, 67), fontsize=14, bgcolor=TASKBAR_COLOR)
    pygame.draw.line(surface, MAIN_BORDER_COLOR, (180, 60), (180, 90))
    render_image(surface, TRASH, (190, 60))
    render_image(surface, ARCHIVE, (230, 60))
    render_image(surface, MOVE, (270, 60))
    pygame.draw.line(surface, MAIN_BORDER_COLOR, (310, 60), (310, 90))
    render_image(surface, REPLY, (320, 60))
    render_image(surface, REPLYALL, (360, 60))
    render_image(surface, FORWARD, (400, 60))
    pygame.draw.line(surface, MAIN_BORDER_COLOR, (440, 60), (440, 90))
    render_image(surface, UNREAD, (450, 60))
    Text(text="Unread/Read", topleft=(490, 67), font_size=14).render(surface)
    pygame.draw.line(surface, MAIN_BORDER_COLOR, (590, 60), (590, 90))
    render_image(surface, UPDATE, (600, 60))
    sendreceive_button = Button(text_input="Send/Receive All Folders", pos=(640, 67), fontsize=14, bgcolor=TASKBAR_COLOR)
    pygame.draw.line(surface, MAIN_BORDER_COLOR, (810, 60), (810, 90))
    render_image(surface, SHOWMAILINGLIST, (820, 60))
    showmailinglists_button = Button(text_input="Show Mailing List", pos=(860, 67), fontsize=14, bgcolor=TASKBAR_COLOR)
    pygame.draw.line(surface, MAIN_BORDER_COLOR, (990, 60), (990, 90))
    render_image(surface, CREATEMAILINGLIST, (1000, 60))
    createmailinglist_button = Button(text_input="Create Mailing Lists", pos=(1040, 67), fontsize=14, bgcolor=TASKBAR_COLOR)
    
    Text(text=data["email"][:35], topleft=(60, 130), font_size=17).render(surface)
    line = 170
    inbox_button = Button(text_input="Inbox", pos=(70, line), fontsize=15, bgcolor=STATUSBAR_COLOR)
    line += LINE_SKIP
    Text(text="Drafts", topleft=(70, line), font_size=15).render(surface)
    line += LINE_SKIP
    Text(text="Sent Items", topleft=(70, line), font_size=15).render(surface)
    sent_button = Button(text_input="Sent Items", pos=(70, line), fontsize=15, bgcolor=STATUSBAR_COLOR)
    line += LINE_SKIP
    Text(text="Deleted Items", topleft=(70, line), font_size=15).render(surface)
    line += LINE_SKIP
    Text(text="Archive", topleft=(70, line), font_size=15).render(surface)
    line += LINE_SKIP
    Text(text="Conversation History", topleft=(70, line), font_size=15).render(surface)
    line += LINE_SKIP
    Text(text="Junk Email", topleft=(70, line), font_size=15).render(surface)
    line += LINE_SKIP
    Text(text="Outbox", topleft=(70, line), font_size=15).render(surface)
    line += LINE_SKIP
    Text(text="RSS Feeds", topleft=(70, line), font_size=15).render(surface)
    line += LINE_SKIP
    Text(text="Sent", topleft=(70, line), font_size=15).render(surface)
    line += LINE_SKIP
    Text(text="Trash", topleft=(70, line), font_size=15).render(surface)
    line += LINE_SKIP
    Text(text="Search Folders", topleft=(70, line), font_size=15).render(surface)
	
    Text(text="All", topleft=(370, 130), font_size=20).render(surface)
    Text(text="Unread", topleft=(410, 130), font_size=20).render(surface)
    Text(text="By Date", topleft=(580, 137), font_size=13).render(surface)
    pygame.draw.line(surface, MAIN_BORDER_COLOR, (50+FOLDERS_WIDTH, 165), (50+2*FOLDERS_WIDTH, 165))

    Text(text=f"Items: {len(data['email_ids'])}", topleft=(10, 877), font_size=13).render(surface)
    Text(text="All folders are up to date", topleft=(1200, 877), font_size=13).render(surface)
    Text(text=f"Connected to: {data['server']}", topleft=(1380, 877), font_size=13).render(surface)
	
    mailtile_buttons = []
    for i, email_id in enumerate(data["emails"]):
        email = data["emails"][email_id]
        mt = MailTile(email["sender"], email["subject"], email["content"], i, email["verified"])
        mt.render(surface)
        mailtile_buttons.append(mt.button())
    
    mail_buttons = []
    if "visualized_email" in data:
        visualizedemail = Mail(data["visualized_email"]["sender"], data["visualized_email"]["recipient"], data["visualized_email"]["subject"], data["visualized_email"]["content"])
        visualizedemail.render(surface)
        mail_buttons = visualizedemail.buttons()

    return [], [logout_button, newemail_button, sendreceive_button, showmailinglists_button, createmailinglist_button, inbox_button, sent_button, *mailtile_buttons, *mail_buttons]


def render_login_interface(surface, data):
    render_image(surface, LOGO, (500, 150))

    Text(text="E-mail address:", topleft=(600, 400), font_size=13).render(surface)
    email_input = TextInput(placeholder="E-mail address", y=420, xoffset=600)
    Text(text="Password:", topleft=(600, 480), font_size=13).render(surface)
    password_input = TextInput(placeholder="Password", y=500, xoffset=600)
    Text(text="Server:", topleft=(600, 560), font_size=13).render(surface)
    server_input = TextInput(placeholder="127.0.0.1:1337", y=580, xoffset=600)

    login_button = Button(text_input="Login", pos=(700, 650))
    signup_button = Button(text_input="Signup", pos=(840, 650))
	
    return [email_input, password_input, server_input], [login_button, signup_button]


def render_signup_interface(surface, data):
    Text(text="Name:", topleft=(600, 240), font_size=13).render(surface)
    name_input = TextInput(placeholder="Name", y=260, xoffset=600)
    Text(text="Surname:", topleft=(600, 320), font_size=13).render(surface)
    surname_input = TextInput(placeholder="Surname", y=340, xoffset=600)
    Text(text="E-mail address:", topleft=(600, 400), font_size=13).render(surface)
    email_input = TextInput(placeholder="E-mail address", y=420, xoffset=600)
    Text(text="Password:", topleft=(600, 480), font_size=13).render(surface)
    password_input = TextInput(placeholder="Password", y=500, xoffset=600)
    Text(text="Server:", topleft=(600, 560), font_size=13).render(surface)
    server_input = TextInput(placeholder="127.0.0.1:1337", y=580, xoffset=600)

    cancel_button = Button(text_input="Cancel", pos=(700, 730))
    signup_button = Button(text_input="Signup", pos=(840, 730))
	
    return [name_input, surname_input, email_input, password_input, server_input], [cancel_button, signup_button]


def render_writing_interface(surface, data):
    render_image(surface, pygame.transform.scale(LOGO, (90, 30)), (40, 10))

    newmail = pygame.Rect(50, 50, 1500, 830)
    pygame.draw.rect(surface, MAILDETAILS_COLOR, newmail, border_top_right_radius=BORDER_RADIUS)
    main_area_border = pygame.Rect(50, 50, 1500, 830)
    pygame.draw.rect(surface, MAIN_BORDER_COLOR, main_area_border, width=1, border_radius=BORDER_RADIUS)

    render_image(surface, SEND, (80, 90))
    send_button = Button(text_input="Send", pos=(80, 130), fontsize=14, bgcolor=MAILDETAILS_COLOR)
    render_image(surface, BACK, (1450, 90))
    back_button = Button(text_input="Back", pos=(1450, 130), fontsize=14, bgcolor=MAILDETAILS_COLOR)
    Text(text="To:", topleft=(150, 80), font_size=16).render(surface)
    to_input = TextInput(placeholder="", y=65, xoffset=220)
    to_input.value = data["writeemail"]["recipient"]
    Text(text="Subject:", topleft=(150, 140), font_size=16).render(surface)
    subject_input = TextInput(placeholder="", y=125, xoffset=220, max_len=100)
    subject_input.value = data["writeemail"]["subject"]
    emailcontent_input = TextInput(placeholder="", y=205, h=650, xoffset=70, max_len=5000)
    emailcontent_input.value = data["writeemail"]["content"]
    return [to_input, subject_input, emailcontent_input], [send_button, back_button]


def render_showmailinglist_interface(surface, data):
    render_image(surface, pygame.transform.scale(LOGO, (90, 30)), (40, 10))
    
    newmailinglist = pygame.Rect(50, 50, 1500, 830)
    pygame.draw.rect(surface, MAILDETAILS_COLOR, newmailinglist, border_top_right_radius=BORDER_RADIUS)
    main_area_border = pygame.Rect(50, 50, 1500, 830)
    pygame.draw.rect(surface, MAIN_BORDER_COLOR, main_area_border, width=1, border_radius=BORDER_RADIUS)

    mailinglists_buttons = []
    for i, ml in enumerate(data["mailinglists"]):
        mltile = MailingListTile(data["mailinglists"][ml]["name"], data["mailinglists"][ml]["description"], data["mailinglists"][ml]["subscripted"], i) # todo: check user subscription
        mltile.render(surface)
        mailinglists_buttons.append(mltile.button())

    render_image(surface, BACK, (750, 800))
    back_button = Button(text_input="Back", pos=(750, 840), fontsize=14, bgcolor=MAILDETAILS_COLOR)

    return [], [back_button, *mailinglists_buttons]


def render_createmailinglist_interface(surface, data):
    render_image(surface, pygame.transform.scale(LOGO, (90, 30)), (40, 10))
    
    newmailinglist = pygame.Rect(50, 50, 1500, 830)
    pygame.draw.rect(surface, MAILDETAILS_COLOR, newmailinglist, border_top_right_radius=BORDER_RADIUS)
    main_area_border = pygame.Rect(50, 50, 1500, 830)
    pygame.draw.rect(surface, MAIN_BORDER_COLOR, main_area_border, width=1, border_radius=BORDER_RADIUS)

    Text(text="Name:", topleft=(100, 380), font_size=16).render(surface)
    mailinglistname_input = TextInput(placeholder="", y=365, xoffset=220)
    Text(text="Description:", topleft=(100, 440), font_size=16).render(surface)
    mailinglistdescription_input = TextInput(placeholder="", y=425, xoffset=220)

    render_image(surface, CREATEMAILINGLIST, (670, 550))
    create_button = Button(text_input="Create", pos=(665, 590), fontsize=14, bgcolor=MAILDETAILS_COLOR)
    render_image(surface, BACK, (900, 550))
    back_button = Button(text_input="Back", pos=(900, 590), fontsize=14, bgcolor=MAILDETAILS_COLOR)

    return [mailinglistname_input, mailinglistdescription_input], [create_button, back_button]


def render_banner(surface, message, color):
    s = pygame.Surface((BANNER_WIDTH, BANNER_HEIGHT))
    notification_banner = pygame.Rect(0, 0, BANNER_WIDTH, BANNER_HEIGHT)
    pygame.draw.rect(s, color, notification_banner, border_top_right_radius=BORDER_RADIUS)
    Text(text=message, center=(BANNER_WIDTH//2, 20), font_size=16).render(s)
    s.set_alpha(192)
    surface.blit(s, (100,10))
