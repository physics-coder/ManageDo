import _thread
import ctypes
import json
import os
import signal
import threading
import time
import tkinter
import tkinter as tk
import uuid
import webbrowser
from time import sleep
from flask import Flask, request, redirect, render_template_string
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from todoist_api_python.api import TodoistAPI
import requests
from flask import request
import tkinter.messagebox
from werkzeug.serving import make_server

import logging
import sys

app_dir = os.path.dirname(sys.argv[0])


def get_path(name):
    global app_dir
    # Join it with the name of the file you wish to create
    return os.path.join(app_dir, name)

def reset():
    TOKEN_SAVE_PATH = get_path('access_token.txt')
    open(TOKEN_SAVE_PATH, 'w').close()
    open(get_path('cookies.json'), 'w').close()



def retrieve_token_from_file(file_path):
    try:
        with open(file_path, 'r') as f:
            return f.read().strip()  # read the file content and strip any leading/trailing whitespace
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
# Setup Todoist API

def retrieve_token(TOKEN_SAVE_PATH):
    API_KEY = retrieve_token_from_file(TOKEN_SAVE_PATH)
    return API_KEY


def flask_app(TOKEN_SAVE_PATH):
    global server_shutdown_event
    REDIRECT_URI = 'http://localhost:5000/callback'
    CLIENT_ID = '413a1ec35550467b9417de161a1d776d'
    CLIENT_SECRET = '69f1fba62c07480c93cbf4b911645ea9'
    STATE = str(uuid.uuid4())
    AUTHORIZATION_URL = 'https://todoist.com/oauth/authorize'
    TOKEN_URL = 'https://todoist.com/oauth/access_token'

    app = Flask(__name__)

    @app.route('/')
    def index():
        params = {
            'client_id': CLIENT_ID,
            'redirect_uri': REDIRECT_URI,
            'state': STATE,
            'scope': 'data:read_write'
        }
        authorization_redirect_url = requests.Request('GET', AUTHORIZATION_URL, params=params).prepare().url
        return redirect(authorization_redirect_url)

    @app.route('/callback')
    def callback():
        error = request.args.get('error', '')
        if error:
            return f"Error received from authorization server: {error}"

        state = request.args.get('state', '')
        if state != STATE:
            return "State mismatch error. Make sure you are not a victim of CSRF."

        code = request.args.get('code')

        token_response = requests.post(TOKEN_URL, data={
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': code,
            'redirect_uri': REDIRECT_URI
        })

        token_json = token_response.json()
        access_token = token_json.get('access_token')

        # Save the token to a separate file
        with open(TOKEN_SAVE_PATH, 'w') as f:
            f.write(access_token)
        if access_token:
            server_shutdown_event.set()
        return render_template_string("<h2>You can now close this tab and continue in the application</h2>")

    class FlaskServer(threading.Thread):
        def __init__(self, app, host, port):
            super().__init__()
            self.srv = make_server(host, port, app)
            self.ctx = app.app_context()
            self.ctx.push()

        def run(self):
            print("Starting Flask server...")
            self.srv.serve_forever()

        def shutdown(self):
            print("Stopping Flask server...")
            self.srv.shutdown()
    global server
    server = FlaskServer(app, '127.0.0.1', 5000)
    server.start()

def retrieve_active_tasks(api):
    try:
        active_tasks = api.get_tasks()
        for i in range(len(active_tasks)):
            active_tasks[i] = active_tasks[i].content
        return active_tasks
    except:
        return None
def retrieve_completed_tasks(API_KEY):
    headers_1 = {
        'Authorization': f'Bearer {API_KEY}',
    }
    response_228 = requests.get('https://api.todoist.com/sync/v9/completed/get_all', headers=headers_1)

    if response_228.status_code == 200:
        # If the request was successful (status code 200), parse the JSON response
        data_228 = response_228.json()

        # The completed tasks are stored in the 'items' key of the response
        completed_tasks = data_228.get('items', [])
        real_completed_tasks = []
        # Extract and print the names of the completed tasks
        for task in completed_tasks:
            task_name = task.get('content', 'No Name')  # 'No Name' is a default value in case 'content' is missing
            real_completed_tasks.append(task_name)
        return real_completed_tasks

    else:
        print(f"Request failed with status code {response_228.status_code}")
        return None
def start_up_webdriver():
    global driver
    options = Options()
    options.add_argument("--headless=new")
    try:
        driver = webdriver.Chrome(options=options)
        return 1

    except:
        return 0
def navigate_to_managebac(url):
    global driver
    try:
        driver.get(url)
        return 1
    except:
        return 0

def retrieve_cookies():
    global driver
    if os.path.exists(get_path('cookies.json')):
        try:
            with open(get_path('cookies.json'), 'r') as file:
                cookies = json.load(file)
        except:
            return 0
        for cookie in cookies:
            name = cookie['name']
            value = cookie['value']
            driver.add_cookie({'name': name, 'value': value})
        return 1
    else:
        return 0
def check_for_cookies():
    if os.path.exists(get_path('cookies.json')):
        return 1
    else:
        return 0

def cookie_create():
    global flag
    flag.set()

def signing_in_with_new_cookies(url):
    global driver
    try:
        start_up_webdriver()
        navigate_to_managebac(url)
        with open(get_path('cookies.json'), 'r') as file:
            cookies = json.load(file)
        for cookie in cookies:
            name = cookie['name']
            value = cookie['value']
            driver.add_cookie({'name': name, 'value': value})
        driver.get(url)
        return 1
    except:
        return 0

def creating_cookies(url):
    global flag
    global driver
    cookies = {}
    print("Cookies didn't work. Please log in manually.")
    # Remove the --headless option to show the browser
    driver.quit()
    driver = webdriver.Chrome()
    driver.get(url)
    # input("After you've logged in, press Enter to continue...")
    flag = threading.Event()

    # Save the cookies after manual login for future use

    flag.wait()
    try:
        new_cookies = driver.get_cookies()
        for cookie in new_cookies:
            cookies[cookie['name']] = cookie['value']
        specific_cookies = [cookie for cookie in new_cookies if
                            cookie['name'] in ['_managebac_session', 'user', 'user_id']]
        with open(get_path('cookies.json'), 'w') as file:
            json.dump(specific_cookies, file)
        driver.quit()
        signed_in_with_new_cookies = signing_in_with_new_cookies(url)
        if signed_in_with_new_cookies:
            if not driver.find_elements(By.CSS_SELECTOR, ".upcoming-tasks .fusion-card-item"):
                return 1
            else:
                return 2
        else:
            return 1
    except:
        return 0

def find_managebac_tasks(active_tasks, real_completed_tasks):
    global driver
    while True:
        try:
            boba_divs = driver.find_elements(By.CSS_SELECTOR, ".upcoming-tasks .show-more-link")
            boba_divs[0].find_element(By.TAG_NAME, 'a').click()
        except:
            break
    aboba_divs = driver.find_elements(By.CSS_SELECTOR, ".upcoming-tasks .fusion-card-item")
    h4_elements = []
    links = []
    subject_names = []
    other_labels = []
    times = []
    months = []
    days = []
    labels = []

    for div in aboba_divs:
        links.append(div.find_element(By.TAG_NAME, 'a').get_attribute('href'))
        subject_names.append(div.find_elements(By.CSS_SELECTOR, 'a')[1].text)
        h4_elements.append(div.find_element(By.TAG_NAME, 'h4').text)
        times.append(div.find_element(By.CLASS_NAME, 'due').text)
        months.append(div.find_element(By.CLASS_NAME, 'month').text)
        days.append(div.find_element(By.CLASS_NAME, 'day').text)
        other_labels.append([i.text.replace('\n', '') for i in div.find_elements(By.CLASS_NAME, 'label')])

    labels = [[] for i in range(len(other_labels))]
    for i in range(len(other_labels)):
        subject_list = [subject_names[i]]
        labels[i] = subject_list + other_labels[i]

    to_does = []
    for i in range(0, len(h4_elements)):
        target = h4_elements[i].replace('\n', '')
        if target[-1] == ' ':
            target = target[0:-1]
        a = times[i].split(' ')
        if target not in active_tasks and target not in real_completed_tasks:
            a = times[i].split(' ')
            to_does.append((target, months[i] + " " + days[i] + " " + a[-2] + " " + a[-1], links[i], labels[i]))
    return to_does

def add_new_tasks(to_does, api):
    for i in to_does:
        api.add_task(project='test', content=i[0], due_string=i[1],
                     description=i[2], labels=i[3])
    with open(get_path("time_log.txt"), "w") as file:
        file.write(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "\n")
def finish():
    global driver, complete
    driver.quit()
    complete = True

class Task:
    instances = []
    animation_chars = ["|", "/", "-", "\\"]

    def __init__(self, task_name, button_text="", function=""):
        Task.instances.append(self)
        global root_1, task_frame
        try:
            self.running = True
            self.task_name = task_name
            if not button_text:
                self.task_label = tk.Label(task_frame, text=task_name, padx=10, pady=5)
                self.status_label = tk.Label(task_frame, text="|", padx=10, pady=5)
                self.grid_labels()
                self.start_loading()
            else:
                self.button = tk.Button(task_frame, text=button_text, command=function)
                self.grid_buttons()
        except Exception as e:
            print(f"An error occurred: {e}")
            return
            # Create the labels and buttons for each task

    @classmethod
    def destroy_all(cls):
        while cls.instances:
            task = cls.instances.pop()
            task.stop()
            try:
                if task.widget_exists(task.task_label):
                    task.task_label.destroy()
            except:
                pass
            try:
                if task.widget_exists(task.status_label):
                    task.status_label.destroy()
            except:
                pass
            try:
                if task.widget_exists(task.button):
                    task.button.destroy()
            except:
                pass
            # Optionally, you can do additional cleanup here if needed
            del task

    def grid_labels(self):
        global root_1, task_frame
        total_tasks = len(task_frame.grid_slaves(column=0))
        self.task_label.grid(row=total_tasks, column=0, sticky="w")
        self.status_label.grid(row=total_tasks, column=1)

    def grid_buttons(self):
        global root_1, task_frame
        total_tasks = len(task_frame.grid_slaves(column=0))
        self.button.grid(row=total_tasks, column=0, sticky="EW")

    def start_loading(self):
        global root_1, task_frame
        # Start the loading animation
        self.animate_loading()

    def widget_exists(self, widget):
        try:
            widget.winfo_exists()
            return True
        except tk.TclError:
            return False

    def animate_loading(self):
        global root_1, task_frame
        try:
            if self.status_label.cget("text") not in self.animation_chars:
                return

            current_char = self.animation_chars.index(self.status_label.cget("text"))
            next_char = (current_char + 1) % 4
            self.status_label.config(text=self.animation_chars[next_char])

            # If the task is still in "Loading..." state, continue the animation
            if self.status_label.cget("text") != "✔" and self.status_label.cget("text") != "✖":
                root_1.after(100, self.animate_loading)
        except Exception as e:
            print("animate_loading")
            print(f"An error occurred: {e}")
            return

    def complete(self):
        if self.running and self.widget_exists(self.status_label):
            global root_1, task_frame
            try:
                self.status_label.config(text="✔")
            except Exception as e:
                print("complete")
                print(f"An error occurred: {e}")
                return
                # Updating the status to a tick

    def fail(self):
        global root_1, task_frame
        self.status_label.config(text="✖")

    def stop(self):
        self.running = False


def back_end():
    global complete
    global driver
    global cookies
    global flag
    global server_shutdown_event

    retrieve_token_task = Task("Retrieving your todoist api token")
    TOKEN_SAVE_PATH = get_path('access_token.txt')
    API_KEY = retrieve_token(TOKEN_SAVE_PATH)

    if not API_KEY:
        retrieve_token_task.fail()
        create_token_task = Task("Creating a new todoist api token. Please log to your account in the browser window")

        server_shutdown_event = threading.Event()
        webbrowser.open("http://127.0.0.1:5000/")
        threading.Thread(target=flask_app, args=(TOKEN_SAVE_PATH,)).start()

        server_shutdown_event.wait()
        create_token_task.complete()
    else:
        retrieve_token_task.complete()
    API_KEY = retrieve_token(TOKEN_SAVE_PATH)
    api = TodoistAPI(API_KEY)
    retrieve_active_tasks_gui = Task("Retrieving your active tasks")
    active_tasks = retrieve_active_tasks(api)
    if active_tasks:
        retrieve_active_tasks_gui.complete()
    else:
        retrieve_active_tasks_gui.fail()
        tkinter.messagebox.showwarning(title="Error retrieving active tasks",
                                       message="Please make sure you have a stable internet connection and try again later")
        exit(0)

    retrieve_completed_tasks_gui = Task("Retrieving your completed tasks")
    real_completed_tasks=retrieve_completed_tasks(API_KEY)
    if real_completed_tasks:
        retrieve_completed_tasks_gui.complete()
    else:
        retrieve_completed_tasks_gui.fail()
        tkinter.messagebox.showwarning(title="Error",
                                       message=f"Request failed")
        exit(0)

    # Start up the webdriver
    web_driver_start = Task("Starting up web driver")
    started_web_driver = start_up_webdriver()
    if started_web_driver:
        web_driver_start.complete()
    else:
        web_driver_start.fail()
        tkinter.messagebox.showwarning(title="Error starting up web driver",
                                       message="Please make sure you have the chrome browser installed")
        exit(0)

    # Navigate to the desired webpage
    opening_url = Task("Opening the managebac website")
    url = 'https://letovo.managebac.com/student/tasks_and_deadlines'
    navigated_to_managebac = navigate_to_managebac(url)
    if navigated_to_managebac:
        opening_url.complete()
    else:
        opening_url.fail()
        tkinter.messagebox.showwarning(title="Error opening the managebac website",
                                       message="Please make sure you have a stable internet connection and that the website is alive.")
        exit(0)

    # Retrieve
    retrieving_cookies = Task("Retrieving login cookies")
    retrieved_cookies = retrieve_cookies()
    if retrieved_cookies:
        driver.get(url)
        retrieving_cookies.complete()
        cookies_exist = True
    else:
        cookies_exist = False



    # Check if the element signifying a successful login is present
    if not driver.find_elements(By.CSS_SELECTOR, ".upcoming-tasks .fusion-card-item") or not cookies_exist:
        retrieving_cookies.fail()
        creating_cookies_gui = Task("Creating login cookies. Please sign in to managebac in the browser window")
        signing_in_with_new_cookies = Task("Signing in with new cookies")
        login_button = Task("login button", "Press me when you have logged in", cookie_create)
        cookies_created = creating_cookies(url)
        if cookies_created == 2:
            creating_cookies_gui.complete()
            signing_in_with_new_cookies.complete()
        elif cookies_created == 1:
            creating_cookies_gui.complete()
            signing_in_with_new_cookies.fail()
            tkinter.messagebox.showwarning(title="Error signing in",
                                           message="Please make sure you have the correct credentials and try again with a new sync")
            exit(0)
        else:
            creating_cookies_gui.fail()
            signing_in_with_new_cookies.fail()
            tkinter.messagebox.showwarning(title="Error creating login cookies",
                                           message="Please make sure you pressed the enter key after logging in with the correct credentials")
            exit(0)

    # Retrieve the tasks
    finding_managebac_tasks_gui = Task("Finding your managebac tasks")
    to_does = find_managebac_tasks(active_tasks,real_completed_tasks)
    finding_managebac_tasks_gui.complete()
    adding_new_tasks = Task("Adding new tasks to todoist")
    add_new_tasks(to_does, api)
    adding_new_tasks.complete()
    done_button = Task("done button", "Done", on_closing)

    print("Done")

    # Close the browser session
    finish()


# Global tkinter window and frame to hold tasks

def auto_sync():
    global complete
    global driver
    global cookies
    global flag
    global server_shutdown_event

    TOKEN_SAVE_PATH = get_path('access_token.txt')
    API_KEY = retrieve_token(TOKEN_SAVE_PATH)

    if not API_KEY:
        return
    api = TodoistAPI(API_KEY)
    active_tasks = retrieve_active_tasks(api)
    if not active_tasks:
        return

    real_completed_tasks = retrieve_completed_tasks(API_KEY)
    if not real_completed_tasks:
        return
    # Start up the webdriver
    started_web_driver = start_up_webdriver()
    if not started_web_driver:
        return

    # Navigate to the desired webpage
    url = 'https://letovo.managebac.com/student/tasks_and_deadlines'
    navigated_to_managebac = navigate_to_managebac(url)
    if not navigated_to_managebac:
        return

    # Retrieve
    retrieved_cookies = retrieve_cookies()
    if retrieved_cookies:
        driver.get(url)
        cookies_exist = True
    else:
        cookies_exist = False

    # Check if the element signifying a successful login is present
    if not driver.find_elements(By.CSS_SELECTOR, ".upcoming-tasks .fusion-card-item") or not cookies_exist:
        return

    # Retrieve the tasks
    to_does = find_managebac_tasks(active_tasks, real_completed_tasks)
    add_new_tasks(to_does, api)

    # Close the browser session
    finish()
    print("Done")

def check():
    TOKEN_SAVE_PATH = get_path('access_token.txt')
    API_KEY = retrieve_token(TOKEN_SAVE_PATH)
    COOKIES = check_for_cookies()
    if API_KEY and COOKIES:
        return 1
    else:
        return None



def on_closing():
    if complete:
        try:
            server.shutdown()
        except:
            pass
        finally:
            Task.destroy_all()
            root_1.destroy()
            return
    else:
        # Messagebox saying sorry but no
        tkinter.messagebox.showwarning(message="Please wait for the synchronization to complete.")
        # os._exit(0)
# Create tasks
def graphical_sync(root, last_sync):
    global complete
    complete = False
    global root_1, task_frame
    root_1 = tk.Toplevel(root)
    root_1.title("Synchronizing tasks")
    task_frame = tk.Frame(root_1)
    task_frame.pack(pady=10)
    global driver
    back_thread = threading.Thread(target=back_end)
    back_thread.daemon = True
    back_thread.start()
    # back_thread.join()


    root_1.protocol("WM_DELETE_WINDOW", on_closing)



if __name__ == "__main__":
    graphical_sync()
driver = 0
complete = False
