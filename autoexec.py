import os
import shutil
import json
from customtkinter import *
from tkinter import filedialog
from PIL import Image, ImageSequence
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

SETTINGS_FILE = "settings.json"
WAVE_AUTOEXEC_FOLDER = os.path.expandvars(r'%LOCALAPPDATA%\Wave\autoexec')
ZENITH_AUTOEXEC_FOLDER = os.path.expandvars(r'%APPDATA%\Zenith\AutoExec')
ZENITH_SCRIPTS_FOLDER = os.path.expandvars(r'%APPDATA%\Zenith\Scripts')
AWP_AUTOEXEC_FOLDER = os.path.expandvars(r'%LOCALAPPDATA%\ui\autoexec')
AWP_SCRIPTS_FOLDER = os.path.expandvars(r'%LOCALAPPDATA%\ui\scripts')

WAVE_COLOR = "#318ce7"
ZENITH_COLOR = "#B675B5"
ZENITH_HOVER_COLOR = "#A14BA2"
AWP_COLOR = "#808080"
AWP_HOVER_COLOR = "#5A5A5A"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class App(CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.load_settings()
        self.current_mode = self.settings.get("current_mode", "Wave")
        self.update_folders_for_mode()
        self.previous_files = set()
        self.animation_timer_id = None
        
        self.grid_columnconfigure(0, weight=1)

        self.header_frame = CTkFrame(master=self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10)
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.wave_gif_path = resource_path("Assets/animated.gif")
        self.zenith_gif_path = resource_path("Assets/zenith.png")
        self.awp_gif_path = resource_path("Assets/awp.png")
        
        self.load_current_gif()
        self.gif_label = CTkLabel(master=self.header_frame, text="")
        self.gif_label.grid(row=0, column=0, sticky="ew", pady=10)
        self.gif_label.bind("<Button-1>", self.toggle_mode)
        self.animate_gif()

        self.title_label = CTkLabel(master=self.header_frame, text=f"{self.current_mode}", font=CTkFont(size=30, weight="normal"))
        self.title_label.grid(row=1, column=0, sticky="ew")

        self.set_theme_colors()
        
        self.set_folder_button = CTkButton(
            master=self, 
            text="Set Scripts Folder", 
            command=self.set_scripts_folder,
            fg_color=self.theme_color,
            hover_color=self.hover_color
        )
        self.set_folder_button.grid(row=2, column=0, pady=30)
        
        self.create_checkbox_frame()
        self.log_messages = []
        self.observer = Observer()
        self.restart_observer()
        self.update_option_menu()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.cancel_animation()
        self.stop_observer()
        self.save_settings()
        self.destroy()

    def cancel_animation(self):
        if self.animation_timer_id:
            self.after_cancel(self.animation_timer_id)
            self.animation_timer_id = None

    def stop_observer(self):
        if hasattr(self, 'observer') and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()

    def create_checkbox_frame(self):
        self.checkbox_frame = CTkScrollableFrame(
            master=self, width=280, height=340, fg_color="#1D1E1E",
            scrollbar_button_hover_color="#1D1E1E",
            scrollbar_button_color="#1D1E1E"
        )
        self.checkbox_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)

    def update_folders_for_mode(self):
        if self.current_mode == "Wave":
            self.autoexec_folder = WAVE_AUTOEXEC_FOLDER
            self.script_folder = self.settings.get("wave_script_folder", "")
        elif self.current_mode == "Zenith":
            self.autoexec_folder = ZENITH_AUTOEXEC_FOLDER
            self.script_folder = self.settings.get("zenith_script_folder", ZENITH_SCRIPTS_FOLDER)
        else:
            self.autoexec_folder = AWP_AUTOEXEC_FOLDER
            self.script_folder = self.settings.get("awp_script_folder", AWP_SCRIPTS_FOLDER)

    def set_theme_colors(self):
        if self.current_mode == "Wave":
            self.theme_color = WAVE_COLOR
            self.hover_color = "#1c5189"
        elif self.current_mode == "Zenith":
            self.theme_color = ZENITH_COLOR
            self.hover_color = ZENITH_HOVER_COLOR
        else:
            self.theme_color = AWP_COLOR
            self.hover_color = AWP_HOVER_COLOR

    def load_settings(self):
        self.settings = {}
        if os.path.isfile(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                self.settings = json.load(f)

    def load_current_gif(self):
        if self.current_mode == "Wave":
            gif_path = self.wave_gif_path
        elif self.current_mode == "Zenith":
            gif_path = self.zenith_gif_path
        else:
            gif_path = self.awp_gif_path
            
        self.gif_frames, self.frame_durations = self.load_gif(gif_path)
        self.gif_index = 0

    def load_gif(self, path):
        frames = []
        frame_durations = []
        
        if path == self.awp_gif_path:
            size = (120, 80)
        else:
            size = (80, 80)
        
        with Image.open(path) as img:
            for frame in ImageSequence.Iterator(img):
                frame = frame.convert("RGBA")
                ctk_image = CTkImage(dark_image=frame, size=size)
                frames.append(ctk_image)
                frame_durations.append(frame.info.get('duration', 100))
        return frames, frame_durations

    def animate_gif(self):
        if self.gif_frames:
            self.gif_label.configure(image=self.gif_frames[self.gif_index])
            duration = self.frame_durations[self.gif_index]
            self.gif_index = (self.gif_index + 1) % len(self.gif_frames)
            self.animation_timer_id = self.after(duration, self.animate_gif)

    def toggle_mode(self, event=None):
        self.cancel_animation()
        
        if self.current_mode == "Wave":
            self.current_mode = "Zenith"
        elif self.current_mode == "Zenith":
            self.current_mode = "AWP"
        else:
            self.current_mode = "Wave"
            
        self.update_folders_for_mode()
        
        self.set_theme_colors()
        self.set_folder_button.configure(
            fg_color=self.theme_color,
            hover_color=self.hover_color
        )
        
        if hasattr(self, 'checkbox_frame'):
            for widget in self.checkbox_frame.winfo_children():
                widget.destroy()
            self.checkbox_frame.grid_forget()
        
        self.create_checkbox_frame()
        
        self.title_label.configure(text=f"{self.current_mode}")
        self.load_current_gif()
        self.update_console(f"Switched to {self.current_mode} mode")
        
        self.animate_gif()
        
        self.restart_observer()
        self.update_option_menu()
        
        self.settings["current_mode"] = self.current_mode
        self.save_settings()

    def open_log_window(self, event=None):
        log_window = CTkToplevel(self)
        log_window.geometry("600x300")
        log_window.title("Log Messages")
        log_window.configure(fg_color="#000000")

        log_textbox = CTkTextbox(master=log_window, width=580, height=280, state="normal", fg_color="#1D1E1E")
        log_textbox.pack(pady=10, padx=10)

        for message in self.log_messages:
            log_textbox.insert("end", message + "\n")

        log_textbox.configure(state="disabled")

    def set_scripts_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.script_folder = folder_selected
            
            if self.current_mode == "Wave":
                self.settings["wave_script_folder"] = self.script_folder
            elif self.current_mode == "Zenith":
                self.settings["zenith_script_folder"] = self.script_folder
            else:
                self.settings["awp_script_folder"] = self.script_folder
            
            self.update_option_menu()
            self.save_settings()
            self.update_console(f"Set {self.current_mode} scripts folder: {self.script_folder}")
            self.restart_observer()

    def restart_observer(self):
        self.stop_observer()
        
        self.observer = Observer()

        if os.path.isdir(self.script_folder):
            self.observer.schedule(Handler(self), self.script_folder, recursive=False)
        if os.path.isdir(self.autoexec_folder):
            self.observer.schedule(Handler(self), self.autoexec_folder, recursive=False)
        
        self.observer.start()

    def update_option_menu(self):
        for widget in self.checkbox_frame.winfo_children():
            widget.destroy()
            
        script_files = {f for f in os.listdir(self.script_folder) if f.endswith('.luau')} if os.path.isdir(self.script_folder) else set()
        autoexec_files = {f for f in os.listdir(self.autoexec_folder) if f.endswith('.luau')} if os.path.isdir(self.autoexec_folder) else set()

        all_files = sorted(script_files | autoexec_files)

        for script in all_files:
            self.create_checkbox(script, script in autoexec_files)

        self.previous_files = script_files.copy()

    def update_checkbox_color(self, checkbox, in_scripts, in_autoexec):
        if self.current_mode == "Wave":
            highlight_color = WAVE_COLOR
        elif self.current_mode == "Zenith":
            highlight_color = ZENITH_COLOR
        else:
            highlight_color = AWP_COLOR
        
        if in_autoexec and in_scripts:
            checkbox.select()
            checkbox.configure(text_color=highlight_color)
        elif in_autoexec:
            checkbox.select()
            checkbox.configure(fg_color="purple", text_color="purple")
        else:
            checkbox.deselect()
            checkbox.configure(text_color="white")

    def create_checkbox(self, script, in_autoexec):
        var = BooleanVar(value=in_autoexec)
        
        if self.current_mode == "Wave":
            checkbox_color = WAVE_COLOR
            hover_color = "#1c5189"
        elif self.current_mode == "Zenith":
            checkbox_color = ZENITH_COLOR
            hover_color = ZENITH_HOVER_COLOR
        else:
            checkbox_color = AWP_COLOR
            hover_color = AWP_HOVER_COLOR
        
        checkbox = CTkCheckBox(
            master=self.checkbox_frame, 
            text=script, 
            variable=var,
            fg_color=checkbox_color,
            hover_color=hover_color
        )
        self.update_checkbox_color(checkbox, script in {f for f in os.listdir(self.script_folder) if f.endswith('.luau')} if os.path.isdir(self.script_folder) else set(), in_autoexec)
        checkbox.configure(command=lambda s=script, cb=checkbox, v=var: self.on_checkbox_toggle(s, cb, v))
        checkbox.pack(anchor="w", pady=2)

    def on_checkbox_toggle(self, script, checkbox, var):
        if self.current_mode == "Wave":
            highlight_color = WAVE_COLOR
        elif self.current_mode == "Zenith":
            highlight_color = ZENITH_COLOR
        else:
            highlight_color = AWP_COLOR
        
        if var.get():
            self.add_script_to_autoexec(script)
            checkbox.select()
            checkbox.configure(text_color=highlight_color)
        else:
            self.remove_script_from_autoexec(script)
            checkbox.deselect()
            checkbox.configure(text_color="white")

    def add_script_to_autoexec(self, script):
        source_path = os.path.join(self.script_folder, script)
        if os.path.isfile(source_path):
            target_path = os.path.join(self.autoexec_folder, script)
            if not os.path.isfile(target_path):
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                shutil.copy(source_path, target_path)
                self.update_console(f"Copied '{script}' to {self.autoexec_folder}")

    def remove_script_from_autoexec(self, script):
        target_path = os.path.join(self.autoexec_folder, script)
        if os.path.isfile(target_path):
            if self.current_mode == "Zenith" or self.current_mode == "AWP":
                scripts_path = os.path.join(self.script_folder, script)
                if not os.path.isfile(scripts_path):
                    os.makedirs(os.path.dirname(scripts_path), exist_ok=True)
                    shutil.copy(target_path, scripts_path)
                    self.update_console(f"Moved '{script}' back to {self.current_mode} Scripts folder")
            
            os.remove(target_path)
            self.update_console(f"Removed '{script}' from {self.autoexec_folder}")

    def update_console(self, message):
        self.log_messages.append(message)
        print(message)

    def save_settings(self):
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(self.settings, f)

class Handler(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.luau'):
            self.app.after(100, self.app.update_option_menu)

    def on_deleted(self, event):
        if not event.is_directory and event.src_path.endswith('.luau'):
            self.app.after(100, self.app.update_option_menu)

if __name__ == "__main__":
    set_default_color_theme("blue")
    root = App()
    root.geometry("300x600")
    root.title("AutoExec")
    root.configure(fg_color=['#000000', '#000000'])
    root.mainloop()