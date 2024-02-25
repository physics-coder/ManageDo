import threading
import tkinter as tk
from tkinter import ttk
import Selenium_crawl
import time
import logging
import sys
import os

# Setup logging
app_dir = os.path.dirname(sys.argv[0])

def get_path(name):
    global app_dir
    return os.path.join(app_dir, name)

def sign_in():
    Selenium_crawl.reset()
    on_start()

def on_start():
    global root
    try:
        Selenium_crawl.graphical_sync(root, last_sync)
    except Exception as e:
        tk.messagebox.showwarning("Synchronization Warning", str(e))

def update_until(break_time):
    if break_time > 0:
        minutes_left = break_time//60
        while minutes_left > 0:
            time_until_sync.config(text=f"{minutes_left} min until auto sync")
            time.sleep(60)
            minutes_left-=1
    else:
        time_until_sync.config(text="auto sync in progress")


def on_refresh(last_sync):
    last_sync_time = read_last_line(get_path("time_log.txt"))
    if last_sync_time:
        last_sync.config(text=last_sync_time)
    else:
        last_sync.config(text="Never")

def background_sync():
    global break_time
    while True:
        if sync_var.get() and selected_time.get():
            print("background sync started")
            time_mapping = {
                "5  minutes": 300,
                "10 minutes": 600,
                "30 minutes": 1800,
                "60 minutes": 3600
            }
            break_time = time_mapping.get(selected_time.get(), 30)
            update_until(0)# Default sleep time if selection is invalid
            try:
                if Selenium_crawl.check():
                    Selenium_crawl.auto_sync()
                    on_refresh(last_sync)
                    update_until(break_time)
                else:
                    tk.messagebox.showwarning("Synchronization Warning", "Please sign in again")
            except Exception as e:
                print(f"Error during background sync: {e}")
            time.sleep(break_time)
        else:
            break

def read_last_line(filename):
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
            return lines[-1] if lines else None
    except FileNotFoundError:
        return None

def on_background_select():
    # Respond to checkbox clicks for enabling/disabling background sync
    if sync_var.get():
        # If checkbox is checked, start or ensure the background sync is running
        if not selected_time.get():
            # If no time is selected, maybe set a default or prompt for selection
            selected_time.set("5  minutes")  # Example: setting a default if none is selected
        threading.Thread(target=background_sync, daemon=True).start()
    else:
        # If checkbox is unchecked, uncheck any selected time options
        selected_time.set("")  # This will uncheck all radio buttons





def main():
    global sync_var, selected_time, last_sync, root
    logging.basicConfig(filename=get_path("error.log"), level=logging.ERROR)

    def handle_exception(exc_type, exc_value, exc_traceback):
        logging.exception("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception

    root = tk.Tk()
    root.minsize(280,260)
    root.title("ManageDo")
    last_sync_time = read_last_line(get_path("time_log.txt"))
    last_sync_text = ttk.Label(root, text = "Last Successful Sync:")
    last_sync_text.pack()
    last_sync = ttk.Label(root, text=last_sync_time if last_sync_time else "Never", foreground="light blue")
    last_sync.pack()
    global time_until_sync
    time_until_sync = ttk.Label(root, text="Auto sync disabled", foreground="light green")
    time_until_sync.pack()
    ttk.Button(root, text="Start Sync", command=on_start).pack()
    ttk.Button(root, text="Sign in again", command=sign_in).pack()

    sync_var = tk.BooleanVar()
    ttk.Checkbutton(root, text="Background synchronization", variable=sync_var, command=on_background_select).pack(pady=10)

    selected_time = tk.StringVar()
    global radio_buttons
    radio_buttons = []
    for time in ["5  minutes", "10 minutes", "30 minutes", "60 minutes"]:
        button = ttk.Radiobutton(root, text=time, variable=selected_time, value=time)
        button.pack()
        radio_buttons.append(button)

    threading.Thread(target=background_sync, daemon=True).start()

    root.mainloop()

if __name__ == "__main__":
    main()
