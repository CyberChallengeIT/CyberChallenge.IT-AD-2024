#!/usr/bin/env python3

import pygame
import pygame_textinput


# =============================================================================== Constants

FPS = 10
WIDTH = 1600
HEIGHT = 900
HEIGHT = 900
CENTER = WIDTH//2
BORDER_RADIUS = 5
BANNER_WIDTH = 1400
BANNER_HEIGHT = 50
FOLDERS_WIDTH = 300
TASKBAR_HEIGHT = 50
LINE_SKIP = 25
MAIL_SKIP = 65
MAIL_LIMIT = 10
MAILINGLISTS_LIMIT = 11

# =============================================================================== Colors

BG_COLOR = "#070B13"
TASKBAR_COLOR = "#292929"
MAIN_BORDER_COLOR = "#666666"
MAILDETAILS_COLOR = "#262626"
STATUSBAR_BORDER_COLOR = "#3B3A39"
STATUSBAR_COLOR = "#141414"
TEXT_COLOR = "#FFFFFF"
ACCOUNT_COLOR = "#91BAEA"
SENDER_COLOR = "#EA3680"
ERROR_COLOR = "#FF0000"
NOTIFICATION_COLOR = "#0275D8"


INPUT_COLOR = STATUSBAR_COLOR
PLACEHOLDER_COLOR = TEXT_COLOR
HOVERING_COLOR = "#3B9DB6"

# =============================================================================== Images

LOGO = pygame.transform.scale(pygame.image.load("assets/logo.png"), (600, 200))
ICON = pygame.transform.scale(pygame.image.load("assets/icon.png"), (20, 20))
NEWEMAIL = pygame.transform.scale(pygame.image.load("assets/newemail.png"), (30, 30))
TRASH = pygame.transform.scale(pygame.image.load("assets/trash.png"), (30, 30))
ARCHIVE = pygame.transform.scale(pygame.image.load("assets/archive.png"), (30, 30))
MOVE = pygame.transform.scale(pygame.image.load("assets/move.png"), (30, 30))
REPLY = pygame.transform.scale(pygame.image.load("assets/reply.png"), (30, 30))
REPLYALL = pygame.transform.scale(pygame.image.load("assets/replyall.png"), (30, 30))
FORWARD = pygame.transform.scale(pygame.image.load("assets/forward.png"), (30, 30))
BACK = pygame.transform.flip(pygame.transform.scale(pygame.image.load("assets/forward.png"), (30, 30)), True, False)
UNREAD = pygame.transform.scale(pygame.image.load("assets/unread.png"), (30, 30))
UPDATE = pygame.transform.scale(pygame.image.load("assets/update.png"), (30, 30))
SEND = pygame.transform.scale(pygame.image.load("assets/send.png"), (30, 30))
NOTVERIFIED = pygame.transform.scale(pygame.image.load("assets/notverified.png"), (30, 30))
CREATEMAILINGLIST = pygame.transform.scale(pygame.image.load("assets/createmailinglist.png"), (30, 30))
SHOWMAILINGLIST = pygame.transform.scale(pygame.image.load("assets/showmailinglist.png"), (30, 30))

# =============================================================================== GUI Elements

class Text():
	def __init__(self, text, center=(CENTER, 100), topleft=None, font_size=50, color=TEXT_COLOR, bgcolor=None):
		self.text = get_font(font_size).render(text, True, color, bgcolor)
		if topleft is not None:
			self.rect = self.text.get_rect(topleft=topleft)
		else:
			self.rect = self.text.get_rect(center=center)

	def render(self, surface):
		surface.blit(self.text, self.rect)
		
class MailTile():
    def __init__(self, sender, subject, content, index, verified):
        self.index = index
        self.verified = verified
        self.sender = Text(sender.replace("\n", " ")[:30], topleft=(70+FOLDERS_WIDTH, 180+MAIL_SKIP*index), font_size=17)
        self.subject = Text(subject.replace("\n", " ")[:35], topleft=(70+FOLDERS_WIDTH, 203+MAIL_SKIP*index), font_size=13)
        self.content = Text(content.replace("\n", " ")[:45], topleft=(70+FOLDERS_WIDTH, 220+MAIL_SKIP*index), font_size=11)
		
    def render(self, surface):
        self.sender.render(surface)
        self.subject.render(surface)
        self.content.render(surface)
        if not self.verified:
             render_image(surface, NOTVERIFIED, (2*FOLDERS_WIDTH, 190+MAIL_SKIP*self.index))
        pygame.draw.line(surface, MAIN_BORDER_COLOR, (55+FOLDERS_WIDTH, 240+MAIL_SKIP*self.index), (45+2*FOLDERS_WIDTH, 240+MAIL_SKIP*self.index))

    def button(self):
         return Button(text_input="                    ", pos=(60+FOLDERS_WIDTH, 180+MAIL_SKIP*self.index), fontsize=50, bgcolor=None)
		
class MailingListTile():
    def __init__(self, name, description, joined, index):
        self.index = index
        self.joined = joined
        self.name = Text(name.replace("\n", " ")[:50], topleft=(70, 65+MAIL_SKIP*index), font_size=17)
        self.description = Text(description.replace("\n", " ")[:150], topleft=(70, 90+MAIL_SKIP*index), font_size=13)
             
		
    def render(self, surface):
        self.name.render(surface)
        self.description.render(surface)
        pygame.draw.line(surface, MAIN_BORDER_COLOR, (60, 120+MAIL_SKIP*self.index), (1540, 120+MAIL_SKIP*self.index))

    def button(self):
        if self.joined:
            button_text = ""
        else:
            button_text = "Join"
        return Button(text_input=button_text, pos=(1400, 75+MAIL_SKIP*self.index), fontsize=18, bgcolor=MAILDETAILS_COLOR)

class Mail():
    def __init__(self, sender, receiver, subject, content):
        self.subject = Text(subject, topleft=(70+2*FOLDERS_WIDTH, 140), font_size=20)
        self.sender = Text(sender, topleft=(115+2*FOLDERS_WIDTH, 175), font_size=14)
        self.receiver = Text(f"To: {receiver}", topleft=(115+2*FOLDERS_WIDTH, 195), font_size=11)
        self.sender_initial = Text(sender[0], center=(90+2*FOLDERS_WIDTH, 190), font_size=20)
        self.content = [Text(contentline, topleft=(70+2*FOLDERS_WIDTH, 260+LINE_SKIP*i), font_size=15) for i, contentline in enumerate(content.split("\n"))]
		
    def render(self, surface):
        self.subject.render(surface)
        self.sender.render(surface)
        pygame.draw.circle(surface, SENDER_COLOR, (90+2*FOLDERS_WIDTH, 190), 20)
        self.sender_initial.render(surface)
        self.receiver.render(surface)
        for contentline in self.content:
            contentline.render(surface)

        buttons_border = pygame.Rect(1220, 160, 320, 50)
        pygame.draw.rect(surface, MAIN_BORDER_COLOR, buttons_border, width=1, border_radius=BORDER_RADIUS)
        pygame.draw.line(surface, MAIN_BORDER_COLOR, (1320, 160), (1320, 210))
        pygame.draw.line(surface, MAIN_BORDER_COLOR, (1435, 160), (1435, 210))
        render_image(surface, REPLY, (1230, 170))
        Text(text="Reply", topleft=(1270, 180), font_size=15).render(surface)
        render_image(surface, REPLYALL, (1330, 170))
        Text(text="Reply All", topleft=(1370, 180), font_size=15).render(surface)
        render_image(surface, FORWARD, (1440, 170))
        Text(text="Forward", topleft=(1480, 180), font_size=15).render(surface)
        
    def buttons(self):
        reply_button = Button(text_input="        ", pos=(1220, 160), fontsize=45, bgcolor=None)
        replyall_button = Button(text_input="        ", pos=(1325, 160), fontsize=50, bgcolor=None)
        forward_button = Button(text_input="       ", pos=(1437, 160), fontsize=50, bgcolor=None)
        return [reply_button, replyall_button, forward_button]

class Button():
    def __init__(self, text_input, pos, image=None, fontsize=20, base_color=TEXT_COLOR, hovering_color=HOVERING_COLOR, bgcolor=BG_COLOR):
        self.image = image
        self.x_pos = pos[0]
        self.y_pos = pos[1]
        self.font = get_font(fontsize)
        self.base_color, self.hovering_color, self.bgcolor = base_color, hovering_color, bgcolor
        self.text_input = text_input
        self.text = self.font.render(self.text_input, True, self.base_color)
        if self.image is None:
            self.image = self.text
        self.rect = self.image.get_rect(topleft=(self.x_pos, self.y_pos))
        self.text_rect = self.text.get_rect(topleft=(self.x_pos, self.y_pos))

    def update(self, surface):
        if self.image is not None:
            surface.blit(self.image, self.rect)
        surface.blit(self.text, self.text_rect)

    def checkForInput(self, position):
        if position[0] in range(self.rect.left, self.rect.right) and position[1] in range(self.rect.top, self.rect.bottom):
            return True
        return False

    def changeColor(self, position):
        if position[0] in range(self.rect.left, self.rect.right) and position[1] in range(self.rect.top, self.rect.bottom):
            self.text = self.font.render(self.text_input, True, self.hovering_color, self.bgcolor)
        else:
            self.text = self.font.render(self.text_input, True, self.base_color, self.bgcolor)

def render_buttons(surface, pos, buttons):
	for button in buttons:
		button.changeColor(pos)
		button.update(surface)
						
class TextInput():
    def __init__(self, placeholder, y, h=50, xoffset=90, max_len=50, validator=None):
        self.validator = lambda input: len(input) <= max_len and (validator is None or validator(input))
        self.manager = pygame_textinput.TextInputManager(validator=self.validator)
        self.pos = (xoffset, y, WIDTH - xoffset*2, h)
        self.visualizer = pygame_textinput.TextInputVisualizer(self.manager, get_font(15), True, PLACEHOLDER_COLOR, 500, 1, PLACEHOLDER_COLOR)
        self.rect = pygame.Rect(self.pos)
        self.isActive = False
        self.isClean = False
        self.visualizer.value = placeholder

    @property
    def value(self):
        return self.visualizer.value
    
    @value.setter
    def value(self, value):
        self.isClean = True
        self.visualizer.value = value
	
    @property
    def isValid(self):
        return self.isClean and self.visualizer.value != ""

    def update(self, events):
        self.visualizer.update(events)

    def clean(self):
        self.visualizer.value = ""
        self.isClean = True

    def active(self, value=True):
        if value:
            self.visualizer.font_color = TEXT_COLOR
            self.visualizer.cursor_color = TEXT_COLOR
            self.isActive = True
        else:
            self.visualizer.font_color = PLACEHOLDER_COLOR
            self.visualizer.cursor_color = INPUT_COLOR
            self.isActive = False

    def render(self, events, surface):
        if self.isActive:
            self.update(events)
        pygame.draw.rect(surface, INPUT_COLOR, self.rect)
        surface.blit(self.visualizer.surface, (self.pos[0] + 10, self.pos[1] + 10))
        textinput_border = pygame.Rect(*self.pos)
        pygame.draw.rect(surface, MAIN_BORDER_COLOR, textinput_border, width=1, border_radius=BORDER_RADIUS)

    def click(self, pos):
        if self.rect.collidepoint(pos):
            if not self.isClean:
                self.clean()
            self.active()
        else:
            self.active(False)

# =============================================================================== Misc utils

def render_image(screen, image, topleft):
	rect = image.get_rect(topleft=topleft)
	screen.blit(image, rect)

def get_font(size):
	return pygame.font.Font("assets/font.ttf", size)
