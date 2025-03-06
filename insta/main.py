from instagrapi import Client
import os
import json
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from functools import lru_cache
import time

# Use Windows Temp directory for session storage
SESSION_DIR = os.path.join(tempfile.gettempdir(), "InstagramUploader by @marpace1 on yt")
os.makedirs(SESSION_DIR, exist_ok=True)

# Cache session file path to avoid repeated string operations
@lru_cache(maxsize=128)
def get_session_file(username):
    return os.path.join(SESSION_DIR, f"{username}.json")

def save_session(cl, username):
    with open(get_session_file(username), "w") as f:
        json.dump(cl.get_settings(), f)

def load_session(cl, username):
    session_file = get_session_file(username)
    if os.path.exists(session_file):
        with open(session_file, "r") as f:
            cl.set_settings(json.load(f))
        return True
    return False

def prompt_for_password():
    dialog = tk.Toplevel(root)
    dialog.title("Enter Password")
    dialog.geometry("300x150")
    dialog.configure(bg="#f0f0f0")

    tk.Label(dialog, text=f"Enter password for '{username}':", bg="#f0f0f0").pack(pady=10)
    password_entry = tk.Entry(dialog, show="*", width=30)
    password_entry.pack(pady=5)

    password_var = tk.StringVar()
    def on_ok():
        password_var.set(password_entry.get().strip())
        dialog.destroy()

    tk.Button(dialog, text="OK", command=on_ok, bg="#4CAF50", fg="white").pack(pady=10)
    dialog.grab_set()
    dialog.wait_window()
    return password_var.get()

def animate_loading(canvas, stop_flag, operation_type, total_files=1, current_file=1):
    angle = 0
    while not stop_flag():
        canvas.delete("loading")
        canvas.create_arc(10, 10, 50, 50, start=angle, extent=270, fill="blue", outline="blue", tags="loading")
        canvas.create_text(30, 30, text=f"{operation_type.capitalize()} {current_file}/{total_files}...", fill="white", font=("Arial", 8))
        angle = (angle + 10) % 360
        root.update()
        time.sleep(0.05)  # Faster animation for smoother effect
    canvas.delete("loading")
    if operation_type == "login":
        canvas.create_text(30, 30, text="Login Complete!", fill="green", font=("Arial", 10))
    elif operation_type == "upload":
        canvas.create_text(30, 30, text="Upload Complete!", fill="green", font=("Arial", 10))
    root.after(1000, lambda: canvas.delete("all"))  # Fade out message after 1 second

def check_existing_session(login_status_canvas, login_button):
    global cl, username
    session_files = [f for f in os.listdir(SESSION_DIR) if f.endswith(".json")]
    if not session_files:
        return False

    username = session_files[0].replace(".json", "")
    use_saved = messagebox.askyesno("Session Found", f"A saved session for '{username}' exists. Use it?")
    if not use_saved:
        return False

    cl = Client()
    try:
        load_session(cl, username)
        password = prompt_for_password()
        if not password:
            messagebox.showerror("Error", "Password is required to reuse the session.")
            return False

        login_status_canvas.pack(pady=5)
        login_button.config(state="disabled")
        stop_animation = False
        def stop_flag(): return stop_animation
        threading.Thread(target=animate_loading, args=(login_status_canvas, stop_flag, "login"), daemon=True).start()

        cl.login(username, password, relogin=True)
        stop_animation = True
        messagebox.showinfo("Success", "Logged in using saved session.")
        show_upload_frame()
        return True
    except Exception as e:
        stop_animation = True
        messagebox.showerror("Error", f"Failed to reuse session: {e}")
        os.remove(get_session_file(username))
        return False
    finally:
        login_button.config(state="normal")
        login_status_canvas.pack_forget()

def login():
    global cl, username
    username = username_entry.get().strip()
    password = password_entry.get().strip()
    
    if not username or not password:
        messagebox.showerror("Error", "Please enter both username and password.")
        return

    login_button.config(state="disabled")
    login_status_canvas.pack(pady=5)
    stop_animation = False
    def stop_flag(): return stop_animation
    threading.Thread(target=animate_loading, args=(login_status_canvas, stop_flag, "login"), daemon=True).start()

    def login_thread():
        global cl
        try:
            cl = Client()
            cl.login(username, password)
            save_session(cl, username)
            root.after(0, lambda: messagebox.showinfo("Success", "Logged in and session saved."))
            root.after(0, show_upload_frame)
        except Exception as e:
            root.after(0, lambda: messagebox.showerror("Login Failed", f"Login error: {e}"))
        finally:
            nonlocal stop_animation
            stop_animation = True
            root.after(0, lambda: login_status_canvas.pack_forget())
            root.after(0, lambda: login_button.config(state="normal"))

    threading.Thread(target=login_thread, daemon=True).start()

def logout():
    session_file = get_session_file(username)
    if os.path.exists(session_file):
        os.remove(session_file)
        messagebox.showinfo("Logout", "Logged out and session removed.")
        upload_frame.pack_forget()
        login_frame.pack(fill="both", expand=True)
    else:
        messagebox.showerror("Error", "No session found.")

def show_upload_frame():
    login_frame.pack_forget()
    upload_frame.pack(fill="both", expand=True)

def select_file(var, file_types, label):
    file_path = filedialog.askopenfilename(filetypes=file_types)
    if file_path:
        var.set(file_path)
        label.config(text=os.path.basename(file_path))

def select_multiple_files(var, file_types, label):
    file_paths = filedialog.askopenfilenames(filetypes=file_types)
    if file_paths:
        var.set(list(file_paths) if file_paths else "")
        label.config(text=f"{len(file_paths)} files selected")

def update_upload_button_state(*args):
    # Removed dynamic state logic; button is always enabled
    pass

def upload():
    current_tab = notebook.tab(notebook.select(), "text")
    media_files = media_file_var.get()
    cover_file = cover_file_var.get() or None
    caption = caption_text_widget.get("1.0", tk.END).strip()

    print(f"Starting upload for {current_tab}, Media Files: {media_files}, Caption: '{caption}'")

    # Validation: Check if media files are selected
    if not media_files:
        messagebox.showerror("Error", "No media files selected.")
        return

    # Validation: Check if files exist
    if isinstance(media_files, str):
        if not os.path.exists(media_files):
            messagebox.showerror("Error", "Selected media file does not exist.")
            return
        media_files = [media_files]  # Convert single file to list for uniform processing
    elif isinstance(media_files, (list, tuple)):
        if not all(os.path.exists(f) for f in media_files):
            messagebox.showerror("Error", "One or more selected media files do not exist.")
            return
    else:
        messagebox.showerror("Error", "Invalid media file selection.")
        return

    # Validation: Check file types based on tab
    if current_tab == "Reel":
        if not all(f.lower().endswith(".mp4") for f in media_files):
            messagebox.showerror("Error", "All files must be MP4 for Reels.")
            return
        if not caption:
            messagebox.showwarning("Warning", "No caption provided for Reel. Instagram may require a caption.")
    elif current_tab == "Story":
        if not all(f.lower().endswith((".jpg", ".png", ".mp4")) for f in media_files):
            messagebox.showerror("Error", "Files must be JPG, PNG, or MP4 for Stories.")
            return
    else:  # Post
        if not all(f.lower().endswith((".jpg", ".png", ".mp4")) for f in media_files):
            messagebox.showerror("Error", "Files must be JPG, PNG, or MP4 for Posts.")
            return
        if not caption:
            messagebox.showwarning("Warning", "No caption provided for Post. Instagram may require a caption.")

    status_canvas.pack(pady=5)
    upload_button.config(state="disabled")
    total_files = len(media_files)
    current_file = 0

    def upload_thread():
        nonlocal current_file
        stop_animation = False
        def stop_flag(): return stop_animation
        threading.Thread(target=animate_loading, args=(status_canvas, stop_flag, "upload", total_files, 1), daemon=True).start()

        def process_upload(file_list):
            nonlocal current_file
            for i, media_file in enumerate(file_list, 1):
                current_file = i
                root.after(0, lambda: status_canvas.delete("loading"))
                root.after(0, lambda: threading.Thread(target=animate_loading, args=(status_canvas, stop_flag, "upload", total_files, current_file), daemon=True).start())
                try:
                    print(f"Uploading {media_file} ({i}/{total_files})")
                    if current_tab == "Reel":
                        cl.clip_upload(media_file, caption=caption if caption else None, thumbnail=cover_file)
                    elif current_tab == "Post":
                        if media_file.lower().endswith(".mp4"):
                            cl.clip_upload(media_file, caption=caption if caption else None, thumbnail=cover_file)
                        else:
                            cl.photo_upload(media_file, caption=caption if caption else None)
                    elif current_tab == "Story":
                        if media_file.lower().endswith(".mp4"):
                            cl.clip_upload_to_story(media_file)
                        else:
                            cl.photo_upload_to_story(media_file)
                    time.sleep(2)  # Simulate upload delay and API rate limiting
                except Exception as e:
                    root.after(0, lambda: status_canvas.create_text(30, 30, text=f"Upload {i} failed: {e}", fill="red", font=("Arial", 10)))
                    stop_animation = True
                    return False
            return True

        success = process_upload(media_files)
        stop_animation = True
        if success:
            root.after(0, lambda: status_canvas.create_text(30, 30, text="Upload Complete!", fill="green", font=("Arial", 10)))
        root.after(0, lambda: status_canvas.pack_forget())
        root.after(0, lambda: upload_button.config(state="normal"))

    threading.Thread(target=upload_thread, daemon=True).start()

def create_gui():
    global root, login_frame, upload_frame, username_entry, password_entry, login_status_canvas, login_button
    global notebook, media_file_var, cover_file_var, caption_text_widget, upload_button, status_canvas

    root = tk.Tk()
    root.title("Instagram Uploader by @marpace1 on yt")
    root.geometry("500x400")
    root.configure(bg="#f0f0f0")

    # Login Frame
    login_frame = tk.Frame(root, bg="#f0f0f0")
    login_frame.pack(fill="both", expand=True)

    tk.Label(login_frame, text="Instagram Uploader by @marpace1 on yt", font=("Arial", 16, "bold"), bg="#f0f0f0").pack(pady=10)
    
    tk.Label(login_frame, text="Username:", bg="#f0f0f0").pack()
    username_entry = tk.Entry(login_frame, width=30)
    username_entry.pack(pady=5)

    tk.Label(login_frame, text="Password:", bg="#f0f0f0").pack()
    password_entry = tk.Entry(login_frame, show="*", width=30)
    password_entry.pack(pady=5)

    login_button = tk.Button(login_frame, text="Login", command=login, bg="#4CAF50", fg="white", width=10)
    login_button.pack(pady=10)

    login_status_canvas = tk.Canvas(login_frame, width=60, height=60, bg="#f0f0f0", highlightthickness=0)
    root.after(0, lambda: check_existing_session(login_status_canvas, login_button))

    # Upload Frame
    upload_frame = tk.Frame(root, bg="#f0f0f0")
    notebook = ttk.Notebook(upload_frame)
    notebook.pack(pady=10, fill="both", expand=True)

    # Tab Setup
    reel_tab = ttk.Frame(notebook)
    story_tab = ttk.Frame(notebook)
    post_tab = ttk.Frame(notebook)
    notebook.add(reel_tab, text="Reel")
    notebook.add(story_tab, text="Story")
    notebook.add(post_tab, text="Post")

    # Variables
    media_file_var = tk.StringVar()
    cover_file_var = tk.StringVar()

    # Reel Tab
    tk.Label(reel_tab, text="Media File(s):", bg="#f0f0f0").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    media_label_reel = tk.Label(reel_tab, text="No file selected", bg="#f0f0f0")
    media_label_reel.grid(row=0, column=1, padx=5, pady=5, columnspan=2)
    tk.Button(reel_tab, text="Select", command=lambda: select_file(media_file_var, [("MP4 files", "*.mp4")], media_label_reel)).grid(row=0, column=3, padx=5)
    tk.Button(reel_tab, text="Select Multiple", command=lambda: select_multiple_files(media_file_var, [("MP4 files", "*.mp4")], media_label_reel)).grid(row=0, column=4, padx=5)

    tk.Label(reel_tab, text="Cover Image (optional):", bg="#f0f0f0").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    cover_label_reel = tk.Label(reel_tab, text="No file selected", bg="#f0f0f0")
    cover_label_reel.grid(row=1, column=1, padx=5, pady=5, columnspan=2)
    tk.Button(reel_tab, text="Select", command=lambda: select_file(cover_file_var, [("Image files", "*.jpg;*.png")], cover_label_reel)).grid(row=1, column=3, padx=5, columnspan=2)

    tk.Label(reel_tab, text="Caption:", bg="#f0f0f0").grid(row=2, column=0, padx=5, pady=5, sticky="nw")
    caption_text_widget = tk.Text(reel_tab, height=4, width=40)
    caption_text_widget.grid(row=2, column=1, columnspan=4, padx=5, pady=5)

    # Story Tab
    tk.Label(story_tab, text="Media File (JPG/PNG/MP4):", bg="#f0f0f0").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    media_label_story = tk.Label(story_tab, text="No file selected", bg="#f0f0f0")
    media_label_story.grid(row=0, column=1, padx=5, pady=5)
    tk.Button(story_tab, text="Select", command=lambda: select_file(media_file_var, [("Media files", "*.jpg;*.png;*.mp4")], media_label_story)).grid(row=0, column=2, padx=5)

    # Post Tab
    tk.Label(post_tab, text="Media File(s):", bg="#f0f0f0").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    media_label_post = tk.Label(post_tab, text="No files selected", bg="#f0f0f0")
    media_label_post.grid(row=0, column=1, padx=5, pady=5, columnspan=2)
    tk.Button(post_tab, text="Select", command=lambda: select_file(media_file_var, [("Media files", "*.jpg;*.png;*.mp4")], media_label_post)).grid(row=0, column=3, padx=5)
    tk.Button(post_tab, text="Select Multiple", command=lambda: select_multiple_files(media_file_var, [("Media files", "*.jpg;*.png;*.mp4")], media_label_post)).grid(row=0, column=4, padx=5)

    tk.Label(post_tab, text="Cover Image (optional):", bg="#f0f0f0").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    cover_label_post = tk.Label(post_tab, text="No file selected", bg="#f0f0f0")
    cover_label_post.grid(row=1, column=1, padx=5, pady=5, columnspan=2)
    tk.Button(post_tab, text="Select", command=lambda: select_file(cover_file_var, [("Image files", "*.jpg;*.png")], cover_label_post)).grid(row=1, column=3, padx=5, columnspan=2)

    tk.Label(post_tab, text="Caption:", bg="#f0f0f0").grid(row=2, column=0, padx=5, pady=5, sticky="nw")
    caption_text_widget = tk.Text(post_tab, height=4, width=40)
    caption_text_widget.grid(row=2, column=1, columnspan=4, padx=5, pady=5)

    # Removed bindings since the button is always enabled
    # caption_text_widget.bind("<KeyRelease>", throttled_update)
    # notebook.bind("<<NotebookTabChanged>>", throttled_update)

    # Upload and Status
    upload_button = tk.Button(upload_frame, text="Upload", command=upload, bg="#4CAF50", fg="white", state="normal")
    upload_button.pack(pady=5)
    status_canvas = tk.Canvas(upload_frame, width=60, height=60, bg="#f0f0f0", highlightthickness=0)
    tk.Button(upload_frame, text="Logout", command=logout, bg="#f44336", fg="white").pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
