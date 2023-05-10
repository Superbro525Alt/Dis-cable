import asyncio
import sched
import time

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import sys
import os
import customtkinter
from PIL import ImageTk, Image
import json as JSON
import datetime
import threading
import screeninfo

customtkinter.set_appearance_mode("dark")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

def get_path():
    """Get path to executing file even if it is frozen."""
    if getattr(sys, 'frozen', False):
        # The application is frozen
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        # The application is not frozen
        application_path = os.path.dirname(__file__)
    return application_path

# Fetch the service account key JSON file contents
cred = credentials.Certificate(get_path() + '\dis-cable-firebase-adminsdk-xbqtc-f8110ab355.json')
# Initialize the app with a service account, granting admin privileges
app = firebase_admin.initialize_app(cred, {
                                    'databaseURL': 'https://dis-cable-default-rtdb.firebaseio.com/'
                                    })

customtkinter.set_window_scaling(0.8 if screeninfo.get_monitors()[0].width > 1080 else 1)
customtkinter.set_widget_scaling(0.8 if screeninfo.get_monitors()[0].width > 1080 else 1)
window = customtkinter.CTk()
window.title("Dis-cable")
window.geometry("1600x800")
window.resizable(False, False)

HOMEIMAGE = customtkinter.CTkImage(Image.open(get_path() + "\images\home.png"), size=(61, 47))
HOMEIMAGE_HOVER = customtkinter.CTkImage(Image.open(get_path() + "\images\home_hover.png"), size=(61, 47))
SENDIMAGE = customtkinter.CTkImage(Image.open(get_path() + "\images\send.png"), size=(47, 47))

global PAGE
PAGE = "LOGIN"
class User:
    def __init__(self, name=None, password=None, remember=None):
            self.name = name
            self.password = password
            self.remember = remember

    def getMessages(self):
        ref = db.reference(f'users/{self.name}/messages')
        return ref.get()

    def send_message(self, message, to):

        ref = db.reference(f'users/{self.name}/messages/{to}/{len(self.getMessages()[to])}')
        ref.set({
            "contents": message,
            "sentAt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sender": self.name})



class ScrollableLabelButtonFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master, command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.width = kwargs.get("width")
        self.command = command
        self.radiobutton_variable = customtkinter.StringVar()
        self.label_list = []
        self.button_list = []
        self._messages = []

    def add_item(self, item, image=None, _command=None, _row=None):

        button = item
        button.configure(width=self.width, height=24)
        if image is not None:
            button.configure(image=image)
            button.configure(corner_radius=5)
            button.configure(corner_radius=0)
        if _command is None:
            if self.command is not None:
                button.configure(command=lambda: self.command(item.cget("text")))
        else:
            button.configure(command=_command)

        button.grid(row=len(self.button_list) + len(self.label_list) if _row is None else _row, column=1, pady=(0, 10) if _row is None else None, padx=5 if _row is None else None)
        self.button_list.append(button)
    def add_on_row(self, item, colmumn, row=1, _command=None):
        button = item
        button.configure(height=24)
        if _command is None:
            if self.command is not None:
                button.configure(command=lambda: self.command(item.cget("text")))
        else:
            button.configure(command=_command)
        button.grid(row=row, column=colmumn)
        self.button_list.append(button)
    def add_label(self, item, grid=True):
        label = item
        label.grid(row=len(self.label_list) + len(self.button_list), column=1, pady=(0, 10), padx=5)

        self.label_list.append(label)

    def add_label_left(self, item, grid=True, message=False):
        label = item
        label.grid(row=len(self.label_list), column=0, pady=(0, 10), padx=5)

        self.label_list.append(label)
        if message:
            self._messages.append(label)

    def remove_item(self, item):
        for label, button in zip(self.label_list, self.button_list):
            if item == label.cget("text"):
                label.destroy()
                button.destroy()
                self.label_list.remove(label)
                self.button_list.remove(button)
                return

def clear_window():
    for widget in window.winfo_children():
        widget.destroy()
def main(USER):
    clear_window()
    window.title("Dis-cable")
    homebutton = customtkinter.CTkButton(window, text="", command=lambda: main(USER), image=HOMEIMAGE, fg_color="transparent", bg_color="transparent", width=71, height=57)
    def on_hover(event=None):
        homebutton.configure(image=HOMEIMAGE_HOVER, corner_radius=5)
    def on_leave(event=None):
        homebutton.configure(image=HOMEIMAGE, corner_radius=5)

    homebutton.bind("<Enter>", on_hover)
    homebutton.bind("<Leave>", on_leave)

    homebutton.place(relx=0.05, rely=0.05, anchor="center")

    messages = customtkinter.CTkFrame(window, width=1500, height=800)
    messages.place(relx=0.6, rely=0.5, anchor="center")

    m = USER.getMessages()
    users = list(m.keys())
    # sort the user list by the time stored in the last message in m[user][messages][highest number]
    users.sort(key=lambda x: datetime.datetime.strptime(m[x][-1]['sentAt'], "%Y-%m-%d %H:%M:%S"), reverse=True)
    def load_messages(user):
        global PAGE
        PAGE = "MESSAGES"
        ref = db.reference("users/" + user + "/notifications/" + USER.name + "/newMessages")
        ref.set(False)
        for widget in messages.winfo_children():
            widget.destroy()
        m = USER.getMessages()[user]
        otherUser = User(name=user)
        otherUserMessages = otherUser.getMessages()[USER.name]
        messagesFrom = customtkinter.CTkFrame(messages, width=1300, height=800)
        messagesFrom.place(relx=0.55, rely=0.5, anchor="center")
        userTitle = customtkinter.CTkLabel(messagesFrom, text=user, font=("Arial", 25), fg_color="transparent", text_color=("gray10", "gray90"), anchor="w")
        userTitle.place(relx=0.05, rely=0.05, anchor="w")

        messagesFrameList = ScrollableLabelButtonFrame(master=messagesFrom, width=1400, height=620)
        messagesFrameList.place(relx=0.5, rely=0.55, anchor="center")
        #join the two lists of messages together
        m = m + otherUserMessages
        messagesFrameList._parent_canvas.configure(scrollregion=messagesFrameList._parent_canvas.bbox("all"))
        def sort_by_time(x):
            return datetime.datetime.strptime(x['sentAt'], "%Y-%m-%d %H:%M:%S")
        m.sort(key=lambda x: sort_by_time(x))
        for message in m:
            if message["sender"] != USER.name:
                messagesFrameList.add_label_left(customtkinter.CTkLabel(messagesFrameList, text=message['sender'], width= 1170, font=("Arial", 25, "bold"), fg_color="transparent", text_color=("gray10", "gray90"), anchor="w"), grid=False)
                messagesFrameList.add_label_left(customtkinter.CTkLabel(messagesFrameList, text=message['contents'], width=1170, font=("Arial", 20), fg_color="transparent", text_color=("gray10", "gray90"), anchor="w"), grid=False, message=True)
            if message["sender"] == USER.name:
                messagesFrameList.add_label_left(
                    customtkinter.CTkLabel(messagesFrameList, text=message['sender'], width=1100,
                                           font=("Arial", 25, "bold"), fg_color="transparent",
                                           text_color=("gray10", "gray90"), anchor="e"), grid=False)
                messagesFrameList.add_label_left(
                    customtkinter.CTkLabel(messagesFrameList, text=message['contents'], width=1100, font=("Arial", 20),
                                           fg_color="transparent", text_color=("gray10", "gray90"), anchor="e"),
                    grid=False, message=True)

            messagesFrameList._parent_canvas.update_idletasks()
            messagesFrameList._parent_canvas.yview_moveto(1)

        messageEntry = customtkinter.CTkEntry(messagesFrom, width=1100, height=40, font=("Arial", 20), fg_color="transparent", text_color=("gray10", "gray90"))
        messageEntry.place(relx=0.46, rely=0.975, anchor="center")
        def send_message(msg, to):
            if msg != "":
                USER.send_message(msg, to)
                messageEntry.delete(0, "end")
                ref = db.reference("users/" + user + "/notifications/" + USER.name + "/newMessages")
                ref.set(True)
                load_messages(user)

        #scroll to bottom of messages frame
        sendButton = customtkinter.CTkButton(messagesFrom, text="", width=40, height=40, font=("Arial", 20),
                                             fg_color="transparent", text_color=("gray10", "gray90"),
                                             hover_color=("gray70", "gray30"), anchor="w", image=SENDIMAGE,
                                             command=lambda: send_message(messageEntry.get(), otherUser.name))
        sendButton.place(relx=0.908, rely=0.975, anchor="center")

        # bind enter to send message
        def enter(event):
            sendButton.invoke()

        messageEntry.bind("<Return>", enter)

        def wait_for_message():
            print("waiting for message")
            if PAGE != "MESSAGES":
                rt.stop()
                return
            ref = db.reference("users/" + USER.name + "/notifications/" + user + "/newMessages")
            if ref.get() == True:
                time.sleep(0.5)
                load_messages(user)
                ref.set(False)

        class RepeatedTimer(object):
            def __init__(self, interval, function, *args, **kwargs):
                self._timer = None
                self.interval = interval
                self.function = function
                self.args = args
                self.kwargs = kwargs
                self.is_running = False
                self.start()

            def _run(self):
                self.is_running = False
                self.start()
                self.function(*self.args, **self.kwargs)

            def start(self):
                if not self.is_running:
                    self._timer = threading.Timer(self.interval, self._run)
                    self._timer.start()
                    self.is_running = True

            def stop(self):
                self._timer.cancel()
                self.is_running = False

        rt = RepeatedTimer(1, wait_for_message)




        # run wait_for_message after 2 seconds
        print('f')






    usersFrameList = ScrollableLabelButtonFrame(master=window, width=200, height=800, command=load_messages)
    def display_friends():
        global PAGE
        PAGE = "FRIENDS"
        for widget in messages.winfo_children():
            widget.destroy()

        ref = db.reference("users/" + USER.name + "/friends")
        friends = ref.get()
        friendsFrameList = ScrollableLabelButtonFrame(master=messages, width=1140, height=800, command=load_messages)
        friendsFrameList.place(relx=0.54, rely=0.5, anchor="center")
        def add_friend():
            popup = customtkinter.CTkFrame(window, width=800, height=400, fg_color="#515151", corner_radius=20, border_width=5, border_color="gray10")
            popup.place(relx=0.5, rely=0.5, anchor="center")
            username = customtkinter.CTkEntry(popup, width=600, height=40, font=("Arial", 20), text_color=("gray10", "gray90"), fg_color="#434343")
            username.place(relx=0.5, rely=0.3, anchor="center")
            def add_friend_to_db(username):
                ref = db.reference("users/" + USER.name + "/requests-out")
                friends = ref.get()

                if friends == "":
                    friends = []
                if username in friends:
                    return
                friends.append(username)
                ref.set(friends)

                ref = db.reference("users/" + username + "/requests-in")
                _friends = ref.get()
                print(_friends)
                if _friends == "":
                    _friends = []
                _friends.append(USER.name)
                ref.set(_friends)

                popup.destroy()
                display_friends()

            add = customtkinter.CTkButton(popup, corner_radius=10, height=40, border_spacing=10, text="Add", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), command=lambda: add_friend_to_db(username.get()))
            add.place(relx=0.5, rely=0.5, anchor="center")
            cancel = customtkinter.CTkButton(popup, corner_radius=10, height=40, border_spacing=10, text="Cancel", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), command=lambda: popup.destroy())
            cancel.place(relx=0.5, rely=0.7, anchor="center")

        friendsFrameList.add_on_row(customtkinter.CTkButton(friendsFrameList, width=200, corner_radius=0, height=40, border_spacing=10, text="Add Friend", fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="center"), _command=add_friend, colmumn=1, row=1)
        friendsFrameList.add_on_row(customtkinter.CTkButton(friendsFrameList, width=200, corner_radius=0, height=40, border_spacing=10, text="Pending Requests Out", fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="center"), _command=add_friend, colmumn=4, row=1)

        for friend in friends:
            friendsFrameList.add_item(customtkinter.CTkButton(friendsFrameList, corner_radius=0, height=40, border_spacing=10, text=friend, fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w"))

    try:
        load_messages(users[0])
    except IndexError:
        display_friends()

    usersFrameList.add_item(customtkinter.CTkButton(usersFrameList, corner_radius=0, height=40, border_spacing=10, text="Friends", fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w"), customtkinter.CTkImage(Image.open(get_path() + r"\images\friends.png"), size=(30, 30)), display_friends)
    usersFrameList.add_label(customtkinter.CTkLabel(usersFrameList, text="DIRECT MESSAGES", height=40, font=("Arial", 10, "bold")))
    userButtonDict = {}
    for user in users:
        userButtonDict[user] = customtkinter.CTkButton(usersFrameList, corner_radius=0, height=40, border_spacing=10, text=user, fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w")

    usersFrameList.grid(row=0, column=2, padx=0, pady=0, sticky="nsew")
    for user in list(userButtonDict.values()):
        usersFrameList.add_item(user)

    usersFrameList.place(relx=0.2, rely=0.5, anchor="center")






def login(name, password, remember):
    global PAGE
    PAGE = "LOGIN"
    if name == "":
        popup = customtkinter.CTkFrame(window)
        popup.place(relx=0.5, rely=0.5, anchor="center")
        popup_label = customtkinter.CTkLabel(popup, text="Please enter a username")
        popup_label.place(relx=0.5, rely=0.5, anchor="center")
        close = customtkinter.CTkButton(popup, text="Close", command=lambda: popup.destroy())
        close.place(relx=0.5, rely=0.65, anchor="center")
        return
    if password == "":
        popup = customtkinter.CTkFrame(window)
        popup.place(relx=0.5, rely=0.5, anchor="center")
        popup_label = customtkinter.CTkLabel(popup, text="Please enter a password")
        popup_label.place(relx=0.5, rely=0.5, anchor="center")
        close = customtkinter.CTkButton(popup, text="Close", command=lambda: popup.destroy())
        close.place(relx=0.5, rely=0.65, anchor="center")
        return
    ref = db.reference('users/' + name)
    try:
        user = ref.get()
        if user['password'] == password:
            if remember == 1:
                _data = open(get_path() + "\prefs\signin.json", "r")
                data = JSON.loads(_data.read())
                _data.close()
                data['username'] = name
                data['password'] = password
                data['remember'] = remember
                data = JSON.dumps(data)
                file = open(get_path() + "\prefs\signin.json", "w")
                file.write(data)
                file.close()



            main(User(name, password, remember))

        else:
            popup = customtkinter.CTkFrame(window)
            popup.place(relx=0.5, rely=0.5, anchor="center")
            popup_label = customtkinter.CTkLabel(popup, text="Incorrect password")
            popup_label.place(relx=0.5, rely=0.5, anchor="center")
            close = customtkinter.CTkButton(popup, text="Close", command=lambda: popup.destroy())
            close.place(relx=0.5, rely=0.65, anchor="center")
            return

    except firebase_admin.exceptions.NotFoundError as e:
        print(e)
        popup = customtkinter.CTkFrame(window)
        popup.place(relx=0.5, rely=0.5, anchor="center")
        popup_label = customtkinter.CTkLabel(popup, text="User does not exist")
        popup_label.place(relx=0.5, rely=0.5, anchor="center")
        close = customtkinter.CTkButton(popup, text="Close", command=lambda: popup.destroy())
        close.place(relx=0.5, rely=0.65, anchor="center")
        return

def loadPrefs(name):
    file = open(get_path() + f"\prefs\{name}.json", "r")
    data = JSON.loads(file.read())
    file.close()
    return data

def login_menu():
    clear_window()
    window.title("Dis-cable Login")
    loginData = loadPrefs("signin")
    if loginData['remember'] == 1:
        login(loginData['username'], loginData['password'], 1)
        return
    title = customtkinter.CTkLabel(window, text="Dis-cable", font=("Arial", 50))
    title.place(relx=0.5, rely=0.05, anchor="center")
    login_label = customtkinter.CTkLabel(window, text="Login", font=("Arial", 30))
    login_label.place(relx=0.5, rely=0.15, anchor="center")
    username_label = customtkinter.CTkLabel(window, text="Username", font=("Arial", 20))
    username_label.place(relx=0.5, rely=0.4, anchor="center")
    username_entry = customtkinter.CTkEntry(window, width=200, height=50, font=("Arial", 17))
    username_entry.place(relx=0.5, rely=0.45, anchor="center")
    password_label = customtkinter.CTkLabel(window, text="Password", font=("Arial", 20))
    password_label.place(relx=0.5, rely=0.55, anchor="center")
    password_entry = customtkinter.CTkEntry(window, width=200, height=50, font=("Arial", 17))
    password_entry.place(relx=0.5, rely=0.6, anchor="center")
    remember_me = customtkinter.CTkSwitch(window, text="Remember me")
    remember_me.place(relx=0.5, rely=0.65, anchor="center")

    login_button = customtkinter.CTkButton(window, text="Login", command=lambda: login(username_entry.get(), password_entry.get(), remember_me.get()))
    login_button.place(relx=0.5, rely=0.75, anchor="center")


login_menu()
window.mainloop()


