
import asyncio
import websockets
from threading import Lock
tts_lock = Lock()
system_monitor_proc = None

import sys
import threading
import time
import random
import math
import os
import subprocess
import signal
import datetime
from io import BytesIO

# Speech & TTS
import speech_recognition as sr
import pyttsx3

# Web & System
import webbrowser
import wikipedia
import pyautogui
##delete thing 
import winreg
import shutil
from send2trash import send2trash
import json
# ---------- App / Folder Manager Globals ----------
CACHE_FILE = "apps_cache.json"
installed_apps = {}      # will be filled at startup

default_apps = {
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "vscode": r"C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "word": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "powerpoint": r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
    "cmd": "cmd.exe",
    "explorer": "explorer.exe",
    "control panel": "control.exe",
    "settings": "ms-settings:",
    "gmail": "https://mail.google.com",
}

# Flask + Feeds + HTTP
from flask import Flask, render_template_string
import requests
import feedparser
import base64

# OCR
import pytesseract
from PIL import Image

# Vision + Game
import cv2
import mediapipe as mp
import keyboard
import screen_brightness_control as sbc


# PyQt5 Orb UI
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QRadialGradient, QColor, QBrush, QPen
from PyQt5.QtCore import Qt, QTimer

# AI (Groq-compatible OpenAI client)
from openai import OpenAI
# ---------- App Scanner ----------
def get_installed_programs():
    installed = {}
    reg_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall")
    ]
    for root, path in reg_paths:
        try:
            with winreg.OpenKey(root, path) as key:
                for i in range(0, winreg.QueryInfoKey(key)[0]):
                    subkey_name = winreg.EnumKey(key, i)
                    try:
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            name = None
                            install_loc = None
                            exe_path = None
                            for j in range(winreg.QueryInfoKey(subkey)[1]):
                                try:
                                    key_name, value, _ = winreg.EnumValue(subkey, j)
                                    if key_name == "DisplayName":
                                        name = value
                                    elif key_name == "InstallLocation":
                                        install_loc = value
                                    elif key_name == "DisplayIcon":
                                        exe_path = value
                                except Exception:
                                    continue
                            if name:
                                app_name = name.lower()
                                if exe_path and os.path.exists(exe_path):
                                    installed[app_name] = exe_path
                                elif install_loc and os.path.exists(install_loc):
                                    installed[app_name] = install_loc
                    except Exception:
                        continue
        except Exception:
            continue

    common_paths = [
        r"C:\Program Files",
        r"C:\Program Files (x86)",
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs")
    ]
    for base in common_paths:
        for root, dirs, files in os.walk(base):
            for file in files:
                if file.endswith(".exe"):
                    name = file.lower().replace(".exe", "")
                    installed[name] = os.path.join(root, file)
    return installed

def load_or_scan_apps():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    speak("Quickly scanning your installed applications, please wait...")
    apps = get_installed_programs()
    with open(CACHE_FILE, "w") as f:
        json.dump(apps, f, indent=2)
    speak("All applications have been indexed.")
    return apps

def open_application(query, installed_apps):
    query = query.lower()
    for app_name, path in default_apps.items():
        if app_name in query:
            try:
                if path.startswith("http"):
                    webbrowser.open(path)
                elif path.startswith("ms-settings"):
                    os.system(f"start {path}")
                else:
                    os.startfile(os.path.expandvars(path))
                return f"Opening {app_name}"
            except Exception as e:
                return f"Unable to open {app_name}: {e}"

    for app_name, path in installed_apps.items():
        if app_name in query:
            try:
                os.startfile(path)
                return f"Opening {app_name}"
            except Exception as e:
                return f"Error opening {app_name}: {e}"
    return f"I couldn’t find {query} on your system."

def close_application(query, installed_apps):
    query = query.lower()
    for app_name, path in installed_apps.items():
        if app_name in query:
            exe_name = os.path.basename(path)
            os.system(f"taskkill /f /im {exe_name} >nul 2>&1")
            return f"Closed {app_name}"
    return "I couldn’t identify which app to close."

# ---------- Folder / File ----------
def detect_drive(query):
    if "d drive" in query: return "D:\\"
    elif "e drive" in query: return "E:\\"
    elif "c drive" in query: return "C:\\"
    elif "desktop" in query: return os.path.join(os.path.expanduser("~"), "Desktop")
    else: return os.getcwd()

def create_folder(query):
    try:
        drive = detect_drive(query)
        folder_name = query.replace("create a folder","").replace("create folder","") \
                           .replace("make a folder","").replace("new folder","") \
                           .replace("in","").replace("on","").replace("drive","").strip()
        if not folder_name:
            return "Please specify a name for the folder."
        folder_path = os.path.join(drive, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        return f"Folder '{folder_name}' created successfully in {drive}"
    except Exception as e:
        return f"Error creating folder: {e}"

def delete_folder(query):
    try:
        folder_name = query.replace("delete folder","").strip()
        if not folder_name:
            return "Please specify the folder name to delete."
        folder_path = os.path.join(detect_drive(query), folder_name)
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            send2trash(folder_path)
            return f"Folder '{folder_name}' sent to Recycle Bin."
        return "Folder not found in the specified location."
    except Exception as e:
        return f"Error deleting folder: {e}"

def create_file(query):
    try:
        drive = detect_drive(query)
        query = query.replace("create a file","").replace("create file","").strip()
        name = query.split("named")[-1].strip() if "named" in query else query
        if not name: return "Please specify the file name."
        if not os.path.splitext(name)[1]:
            name += ".txt"
        file_path = os.path.join(drive, name)
        with open(file_path, "w") as f: f.write("")
        return f"File '{name}' created successfully in {drive}"
    except Exception as e:
        return f"Error creating file: {e}"

# SMS
from twilio.rest import Client as TwilioClient

# ==================== CONFIG ====================
# ✅ Tesseract path (adjust if different)
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# ✅ Groq/OpenAI direct key (NOT recommended for production!)
GROQ_API_KEY = "GroqAPIkey"       # paste your actual Groq key here
client = OpenAI(api_key=GROQ_API_KEY,
                base_url="gorqurl")


# ==================== TWILIO SMS (CLEAN DROP-IN) ====================
from twilio.rest import Client
from datetime import datetime as dt_sms

TWILIO_SID = "SID"        # rotate this ASAP
TWILIO_AUTH_TOKEN = "TOken"    # rotate this ASAP
TWILIO_NUMBER = "RandomNumber"
CARETAKER_NUMBER = "CaretakerNumber"

def send_sms(message: str) -> bool:
    """Sends an SMS via Twilio to the caretaker number."""
    try:
        client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
        sms = client.messages.create(
            body=message,
            from_=TWILIO_NUMBER,
            to=CARETAKER_NUMBER
        )
        print("✅ SMS sent! SID:", sms.sid)
        return True
    except Exception as e:
        print("❌ SMS failed:", e)
        return False


# ==================== FLASK APP (Memes + News) ====================
flask_app = Flask(__name__)

# Fetch a single meme from light, safe subreddits
def fetch_random_reddit_meme():
    """
    Fetch a random meme from a few popular subreddits using meme-api.
    Returns (base64_image, title) or (None, error_message)
    """
    try:
        subreddits = ["memes", "dankmemes", "wholesomememes", "funny"]
        subreddit = random.choice(subreddits)
        url = f"https://meme-api.com/gimme/{subreddit}"

        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        meme_url = data.get("url")
        meme_title = data.get("title", "Untitled meme")

        if not meme_url:
            return None, "No meme found."

        img_data = requests.get(meme_url, timeout=5).content
        encoded_img = base64.b64encode(img_data).decode("utf-8")

        return encoded_img, f"{subreddit}: {meme_title}"

    except Exception as e:
        return None, f"⚠ Error fetching meme: {e}"


# Fetch the top 10 world news headlines
def fetch_latest_news():
    rss_url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
    try:
        feed = feedparser.parse(rss_url)
        headlines = []
        for entry in feed.entries:
            title = entry.title.strip()
            if title and title not in headlines:
                headlines.append(title)
            if len(headlines) >= 10:
                break
        return headlines
    except Exception as e:
        return [f"⚠ Error fetching news: {e}"]

@flask_app.route("/")
def index():
    memes = [fetch_random_reddit_meme() for _ in range(2)]
    headlines = fetch_latest_news()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""
    <html>
    <head>
        <title>Live Daily Update</title>
        <meta http-equiv="refresh" content="60">
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            .meme-container {{ display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; margin-bottom: 20px; }}
            .meme-card {{ max-width: 45%; text-align: center; }}
            .meme-card img {{ max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }}
        </style>
    </head>
    <body>
        <h1>🤣 Random Memes</h1>
        <div class="meme-container">
    """
    for meme_img, meme_title in memes:
        if meme_img is None:
            meme_img = ""
        html += f"""
            <div class="meme-card">
                <p><b>{meme_title}</b></p>
                <img src="data:image/jpeg;base64,{meme_img}" alt="Meme">
            </div>
        """

    html += f"""
        </div>
        <h1>📰 Top 10 World News Headlines</h1>
        <p>Last Updated: {now}</p>
        <ol>
    """
    for headline in headlines:
        html += f"<li>{headline}</li>"

    html += """
        </ol>
        <p>🔄 Page refreshes automatically every 1 minute.</p>
    </body>
    </html>
    """
    return render_template_string(html)

@flask_app.route("/meme")
def meme_page():
    memes = [fetch_random_reddit_meme() for _ in range(2)]
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = f"""
    <html>
    <head>
        <title>🤣 Memes</title>
        <meta http-equiv="refresh" content="60">
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            .meme-container {{ display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; }}
            .meme-card {{ max-width: 45%; text-align: center; }}
            .meme-card img {{ max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }}
        </style>
    </head>
    <body>
        <h1>🤣 Random Memes</h1>
        <p>Last Updated: {now}</p>
        <div class="meme-container">
    """
    for meme_img, meme_title in memes:
        if meme_img is None:
            meme_img = ""
        html += f"""
            <div class="meme-card">
                <p><b>{meme_title}</b></p>
                <img src="data:image/jpeg;base64,{meme_img}" alt="Meme">
            </div>
        """
    html += """
        </div>
        <p>🔄 Page refreshes automatically every 1 minute.</p>
    </body>
    </html>
    """
    return render_template_string(html)

@flask_app.route("/news")
def news_page():
    headlines = fetch_latest_news()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = f"""
    <html>
    <head>
        <title>📰 News</title>
        <meta http-equiv="refresh" content="60">
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            ol  {{ font-size: 18px; line-height: 1.5; }}
            h1  {{ color: #333; }}
        </style>
    </head>
    <body>
        <h1>📰 Top 10 World News Headlines</h1>
        <p>Last Updated: {now}</p>
        <ol>
            {''.join(f'<li>{h}</li>' for h in headlines)}
        </ol>
        <p>🔄 Page refreshes automatically every 1 minute.</p>
    </body>
    </html>
    """
    return render_template_string(html)


# ==================== OCR + SUMMARIZATION FUNCTIONS ====================
def take_screenshot():
    screenshot_path = "screenshot.png"
    pyautogui.screenshot(screenshot_path)
    return screenshot_path


def extract_text_from_image(image_path):
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image, config="--psm 6")
    return text.strip()


def _speak_in_chunks(assistant, text, chunk_size=180):
    text = text.replace("\n", " ").strip()
    if not text:
        return
    i = 0
    while i < len(text):
        assistant.speak(text[i:i+chunk_size])
        i += chunk_size


def process_summarization(assistant):
    assistant.speak("Capturing your screen now, boss.")
    image_path = take_screenshot()
    extracted_text = extract_text_from_image(image_path)

    if not extracted_text:
        assistant.speak("I couldn't find any readable text on your screen.")
        return

    assistant.speak("Here's what I can read on your screen.")
    _speak_in_chunks(assistant, extracted_text, chunk_size=220)

# ==================== Slowroads Game Steering ====================
def play_slowroads(assistant):
    assistant.speak("Launching Slowroads boss, please wait...")

    webbrowser.open("https://slowroads.io/")
    time.sleep(6)
    assistant.speak("Click inside the game window to focus, then come back.")
    time.sleep(3)

    mp_face = mp.solutions.face_mesh
    face_mesh = mp_face.FaceMesh(min_detection_confidence=0.7, min_tracking_confidence=0.7)

    cap = cv2.VideoCapture(0)

    TILT_LEFT_THRESHOLD = -5
    TILT_RIGHT_THRESHOLD = 5
    key_a_pressed = False
    key_d_pressed = False

    def get_roll_and_eye_points(landmarks, w, h):
        left_eye = landmarks[33]
        right_eye = landmarks[263]
        x1, y1 = int(left_eye.x * w), int(left_eye.y * h)
        x2, y2 = int(right_eye.x * w), int(right_eye.y * h)
        roll = math.degrees(math.atan2(y2 - y1, x2 - x1))
        return roll, (x1, y1), (x2, y2)

    assistant.speak("Tilt your head left or right to steer. Press ESC to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(frame_rgb)
        h, w, _ = frame.shape

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            roll, left_pt, right_pt = get_roll_and_eye_points(landmarks, w, h)

            cv2.circle(frame, left_pt, 5, (0, 255, 0), -1)
            cv2.circle(frame, right_pt, 5, (0, 255, 0), -1)
            cv2.line(frame, left_pt, right_pt, (255, 255, 255), 2)

            if roll < TILT_LEFT_THRESHOLD:
                if not key_a_pressed:
                    keyboard.press('a')
                    key_a_pressed = True
                if key_d_pressed:
                    keyboard.release('d')
                    key_d_pressed = False
            elif roll > TILT_RIGHT_THRESHOLD:
                if not key_d_pressed:
                    keyboard.press('d')
                    key_d_pressed = True
                if key_a_pressed:
                    keyboard.release('a')
                    key_a_pressed = False
            else:
                if key_a_pressed:
                    keyboard.release('a')
                    key_a_pressed = False
                if key_d_pressed:
                    keyboard.release('d')
                    key_d_pressed = False

            cv2.putText(frame, f'Roll: {int(roll)}°', (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("Slowroads Steering", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    keyboard.release('a')
    keyboard.release('d')
    assistant.speak("Slowroads steering stopped.")

# ==================== TTS CORE ====================
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
if voices:
    engine.setProperty('voice', voices[1].id if len(voices) > 1 else voices[0].id)


def speak(audio):
    try:
        with tts_lock:
            engine.say(audio)
            engine.runAndWait()
    except RuntimeError as e:
        print("⚠️ TTS busy, skipping:", e)

def speak(text):
    with tts_lock:                # <-- ensures only one speak at a time
        print("🗣️ Friday:", text)
        engine.say(text)
        engine.runAndWait()


def wishMe():
    hour = int(datetime.datetime.now().hour)
    if 0 <= hour < 12:
        speak("Good morning boss")
    elif 12 <= hour < 18:
        speak("Good afternoon boss")
    else:
        speak("Good evening boss")
    speak("I'm Friday, personal assistant at your service")

# ==================== Improved Voice Capture ====================
def takeVoice():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        if 'orb' in globals():
            orb.set_state("listening")          # green
        print("Boss, I'm listening...")
        r.adjust_for_ambient_noise(source, duration=0.8)
        r.pause_threshold = 1.2
        r.energy_threshold = 3000
        try:
            audio = r.listen(source, timeout=6, phrase_time_limit=12)
        except sr.WaitTimeoutError:
            if 'orb' in globals():
                orb.set_state("idle")           # back to white
            print("No speech detected within the timeout.")
            return None
    if 'orb' in globals():
        orb.set_state("idle")                   # back to white after capture
    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language='en-in')
        print("Boss said:", query)
        return query
    except sr.UnknownValueError:
        print("Could not understand audio")
        return None
    except sr.RequestError as e:
        print(f"Google Speech Recognition service error: {e}")
        return None


# ==================== AI FALLBACK ====================
def askAI(question: str) -> str:
    try:
        response = client.chat.completions.create(
            model="moonshotai/kimi-k2-instruct-0905",  # or another Groq model
            messages=[{"role": "user", "content": question}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("Error in askAI:", str(e))
        return "Sorry boss, I couldn't reach the AI right now."



# ------------------ Orb Widget ------------------
class OrbWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.state = "idle"
        self.base_size = 80
        self.orb_size = self.base_size
        self.pulse_angle = 0
        self.float_angle = 0
        self.float_offset = 0
        self.orb_pos = "right"

        self.stars = [
            [random.randint(10, self.base_size - 10),
             random.randint(10, self.base_size - 10),
             random.uniform(0.5, 1.5),
             random.randint(1, 3)]
            for _ in range(25)
        ]

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(50)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(self.base_size + 40, self.base_size + 60)
        self.move_to_default()

    def move_to_default(self):
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        x = screen_geometry.width() - self.width() - 20 if self.orb_pos == "right" else 20
        y = 20
        self.move(x, y)

    def set_state(self, new_state):
        self.state = new_state
        self.update()

    def animate(self):
        self.pulse_angle += 0.12
        self.orb_size = self.base_size + int(8 * math.sin(self.pulse_angle))
        self.float_angle += 0.05
        self.float_offset = int(8 * math.sin(self.float_angle))
        for star in self.stars:
            star[0] += math.sin(self.pulse_angle * star[2]) * 0.5
            star[1] += math.cos(self.pulse_angle * star[2]) * 0.5
            if star[0] < 10 or star[0] > self.base_size - 10:
                star[0] = random.randint(10, self.base_size - 10)
            if star[1] < 10 or star[1] > self.base_size - 10:
                star[1] = random.randint(10, self.base_size - 10)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.state == "idle":
            base_color = QColor(255, 255, 255)    # white idle
        elif self.state == "listening":
            base_color = QColor(0, 255, 0)        # green listening
        elif self.state == "speaking":
            base_color = QColor(0, 102, 255)      # blue speaking
        else:
            base_color = QColor(255, 255, 255)

        x = (self.width() - self.orb_size) / 2
        y = (self.height() - self.orb_size) / 2 + self.float_offset

        painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(x), int(y + self.orb_size + 5), self.orb_size, 15)

        gradient = QRadialGradient(x + self.orb_size/2, y + self.orb_size/2, self.orb_size/1.2)
        gradient.setColorAt(0.0, QColor(255, 255, 255, 230))
        gradient.setColorAt(0.3, base_color.lighter(160))
        gradient.setColorAt(0.8, base_color)
        gradient.setColorAt(1.0, base_color.darker(250))

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(x), int(y), self.orb_size, self.orb_size)

        for star in self.stars:
            star_color = QColor(255, 255, 255, random.randint(150, 255))
            painter.setPen(QPen(star_color, star[3]))
            painter.drawPoint(int(x + star[0]), int(y + star[1]))

        painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(x + self.orb_size*0.25),
                            int(y + self.orb_size*0.2),
                            int(self.orb_size*0.25),
                            int(self.orb_size*0.18))


# ---------- Brightness Control ----------
def set_brightness(level: int):
    """
    Sets brightness to a specific level (0–100).
    """
    try:
        sbc.set_brightness(level)
        return f"Brightness set to {level} percent."
    except Exception as e:
        return f"Could not set brightness: {e}"

def adjust_brightness(delta: int):
    """
    Increases or decreases brightness by a delta value (+/-).
    """
    try:
        current = sbc.get_brightness(display=0)[0]    # get current brightness
        new_level = max(0, min(100, current + delta))
        sbc.set_brightness(new_level)
        return f"Brightness changed to {new_level} percent."
    except Exception as e:
        return f"Could not change brightness: {e}"


# ------------------ Friday Assistant ------------------
class FridayAssistant:
    def __init__(self, orb_widget):
        self.orb = orb_widget
        self.listener = sr.Recognizer()
        self.engine = engine
        self.google_process = None
        self.system_monitor_proc = None 

    def speak(self, text):
        self.orb.set_state("speaking")
        with tts_lock:            # <-- lock here too
            self.engine.say(text)
            self.engine.runAndWait()
        self.orb.set_state("idle")


    # Optional direct listen (not used because we use global takeVoice)
    def listen(self):
        with sr.Microphone() as source:
            self.orb.set_state("listening")
            print("Listening...")
            audio = self.listener.listen(source)
        try:
            command = self.listener.recognize_google(audio)
            print("User said:", command)
            self.orb.set_state("idle")
            return command.lower()
        except:
            self.orb.set_state("idle")
            return ""

    # ---- Google control ----
    def open_google(self):
        self.speak("Opening Google")
        try:
            self.google_process = subprocess.Popen(["chrome", "https://www.google.com"])
        except FileNotFoundError:
            webbrowser.open("https://www.google.com")
            self.google_process = None

    def close_google(self):
        if self.google_process:
            self.speak("Closing Google")
            self.google_process.terminate()
            self.google_process = None
        else:
            self.speak("Closing all Google Chrome windows")
            if os.name == "nt":
                os.system("taskkill /im chrome.exe /f")
            else:
                os.system("pkill chrome")
# ------------------ Friday Network (Peer-to-Peer) ------------------
class FridayNetwork:
    def __init__(self, name, orb_ref, speak_fn):
        self.name = name
        self.orb = orb_ref
        self.speak = speak_fn           # reuse assistant.speak
        self.server_uri = "ws://10.16.231.155:8765"   # <--- change to your server
        self.connection = None
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.run_network, daemon=True).start()

    async def connect(self):
        while True:
            try:
                async with websockets.connect(self.server_uri) as ws:
                    self.connection = ws
                    await ws.send(json.dumps({"action": "register", "name": self.name}))
                    print(f"✅ {self.name} connected to network.")
                    async for msg in ws:
                        data = json.loads(msg)
                        if data.get("type") == "message":
                            sender, text = data.get("from"), data.get("text")
                            print(f"📩 {sender}: {text}")
                            self.speak(f"{sender} says: {text}")
            except Exception as e:
                print("⚠️ Network error:", e)
                await asyncio.sleep(5)

    def run_network(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.connect())

    def send_message(self, to, text):
        if not self.connection:
            self.speak("Server not connected yet.")
            return
        asyncio.run_coroutine_threadsafe(
            self.connection.send(json.dumps({
                "action": "message",
                "from": self.name,
                "to": to,
                "text": text
            })), self.loop)



# ------------------ Face Detection Control ------------------
face_proc = None

def start_face_detection(assistant):
    global face_proc
    if face_proc is None or face_proc.poll() is not None:
        assistant.speak("Starting face detection boss.")
        face_proc = subprocess.Popen([sys.executable, "vision_gestures_improved.py"])
    else:
        assistant.speak("Face detection is already running.")


def stop_face_detection(assistant):
    global face_proc
    if face_proc is not None and face_proc.poll() is None:
        assistant.speak("Stopping face detection boss.")
        face_proc.terminate()
        try:
            face_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            face_proc.kill()
        face_proc = None
    else:
        assistant.speak("Face detection is not currently running.")

# ==================== TWILIO SMS ====================
from datetime import datetime as dt_sms

def send_sms(message):
    try:
        client_twilio = TwilioClient(TWILIO_SID, TWILIO_AUTH_TOKEN)
        sms = client_twilio.messages.create(
            body=message,
            from_=TWILIO_NUMBER,
            to=CARETAKER_NUMBER
        )
        print("✅ SMS sent! SID:", sms.sid)
    except Exception as e:
        print("❌ SMS failed:", e)

# ==================== Activation & Run Loop ====================

def activation(assistant, orb):
    while True:
        orb.set_state("listening")
        query = takeVoice()
        orb.set_state("idle")

        if query:
            query = query.lower()
            if 'hey friday' in query or 'hi friday' in query or 'start program' in query:
                assistant.speak("Yes boss, I'm here")
                run(assistant, orb)
                break
            elif 'thanks friday' in query or 'search complete' in query:
                assistant.speak("Goodbye boss, have a great day")
                orb.close()
                QApplication.quit()
                os._exit(0)
                break


def run(assistant, orb):
    while True:
        orb.set_state("listening")
        query = takeVoice()
        orb.set_state("idle")

        if not query:
            continue
        query = query.lower()
        # ----- OPEN SYSTEM MONITOR -----
        
        if "show system info" in query or "open system monitor" in query:
            assistant.speak("Opening EcoSystem Monitor in your browser.")
            # launch streamlit and remember the process
            assistant.system_monitor_proc = subprocess.Popen(
                ["streamlit", "run", "eco.py"]
            )
            time.sleep(3)
            webbrowser.open("http://localhost:8501")
            continue
        elif "new tab" in query:
            pyautogui.hotkey('ctrl','t'); assistant.speak("New tab opened")
        elif "close tab" in query:
            pyautogui.hotkey('ctrl','w'); assistant.speak("Tab closed")
        # ----- CLOSE SYSTEM MONITOR -----
        elif "close system info" in query or "close system monitor" in query:
            if assistant.system_monitor_proc and assistant.system_monitor_proc.poll() is None:
                assistant.speak("Closing EcoSystem Monitor.")
                assistant.system_monitor_proc.terminate()
                assistant.system_monitor_proc = None
            else:
                assistant.speak("System Monitor is not running.")
            continue
        # ---------- Face Detection ----------
        if "read my face" in query or "start face detect" in query or "start face scan" in query:
            start_face_detection(assistant)
            continue
        elif "close face detect" in query or "stop face detect" in query or "stop face scan" in query:
            stop_face_detection(assistant)
            continue

        # ---------- Slowroads Game ----------
        elif "play game" in query or "start slowroads" in query:
            play_slowroads(assistant)
            continue

        # ---------- News & Memes (Flask UI + TTS) ----------
        elif "tell me news" in query or "give me news" in query or "latest news" in query:
            webbrowser.open("http://127.0.0.1:5000/news")
            assistant.speak("Fetching the latest world news for you boss.")
            headlines = fetch_latest_news()
            if headlines:
                assistant.speak("Here are the headlines on your screen.")
                for idx, headline in enumerate(headlines[:10], 1):
                    assistant.speak(f"Headline {idx}: {headline}")
                    time.sleep(0.4)
                assistant.speak("That’s all the headlines boss.")
            else:
                assistant.speak("Sorry boss, I couldn’t fetch any headlines right now.")
            continue
                # ---------- App / Folder Manager ----------
                # ---------- App / Folder Manager ----------
        elif query.startswith("open "):
            # Any voice command starting with "open " goes here
            assistant.speak(open_application(query, installed_apps))
            continue     # prevents AI fallback
                # ---------- Network Messaging ----------
        

        
        if "send message" in query:
            assistant.speak("Who should I send the message to?")
            target = takeVoice()
            if not target:
                assistant.speak("I didn’t catch the recipient’s name.")
                continue
            assistant.speak(f"What’s your message for {target}?")
            msg = takeVoice()
            if msg:
                network.send_message(target, msg)
                assistant.speak(f"Message sent to {target}.")
            continue


        elif query.startswith("close "):
            assistant.speak(close_application(query, installed_apps))
            continue     # prevents AI fallback


        elif any(x in query for x in ["create folder", "create a folder", "make a folder", "new folder"]):
            assistant.speak(create_folder(query))

        elif "delete folder" in query:
            assistant.speak(delete_folder(query))

        elif any(x in query for x in ["create file", "create a file"]):
            assistant.speak(create_file(query))

        elif "tell me a meme" in query or "tell me a joke" in query or "give me a meme" in query:
            webbrowser.open("http://127.0.0.1:5000/meme")
            assistant.speak("Fetching some memes for you boss.")
            continue

        elif "show dashboard" in query or "open dashboard" in query or "show memes" in query or "show news" in query:
            webbrowser.open("http://127.0.0.1:5000/")
            assistant.speak("Opening the meme and news dashboard boss")
            continue

        # ---------- Screenshot OCR Reader ----------
        elif "capture" in query:
            process_summarization(assistant)
            continue

                # ---------- Emergency SMS ----------
        elif "emergency" in query:
            message_text = f"Emergency detected at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}! Please check immediately."
            send_sms(message_text)
            assistant.speak("Emergency SMS sent to caretaker.")
            continue


        # ---------- Open/Close Google ----------
        elif "open google" in query:
            assistant.open_google()
            continue
        elif "close google" in query:
            assistant.close_google()
            continue

        # ---------- Mouse Absolute Move ----------
        if "mouse move" in query:
            parts = query.split()
            try:
                x = int(parts[-2])
                y = int(parts[-1])
                pyautogui.moveTo(x, y, duration=0.3)
                assistant.speak(f"Moved mouse to {x}, {y}")
            except:
                assistant.speak("Boss, give me two numbers for the coordinates")

        # ---------- Mouse Relative Moves ----------
        elif "move mouse up" in query:
            parts = query.split()
            for p in parts:
                if p.isdigit():
                    pyautogui.moveRel(0, -int(p), duration=0.2)
                    assistant.speak(f"Moved mouse up by {p} pixels")
                    break
        elif "move mouse down" in query:
            parts = query.split()
            for p in parts:
                if p.isdigit():
                    pyautogui.moveRel(0, int(p), duration=0.2)
                    assistant.speak(f"Moved mouse down by {p} pixels")
                    break
        elif "move mouse left" in query:
            parts = query.split()
            for p in parts:
                if p.isdigit():
                    pyautogui.moveRel(-int(p), 0, duration=0.2)
                    assistant.speak(f"Moved mouse left by {p} pixels")
                    break
        elif "move mouse right" in query:
            parts = query.split()
            for p in parts:
                if p.isdigit():
                    pyautogui.moveRel(int(p), 0, duration=0.2)
                    assistant.speak(f"Moved mouse right by {p} pixels")
                    break

        # ---------- Clicks ----------
        elif "click left" in query:
            pyautogui.click(button='left')
            assistant.speak("Left click done")
        elif "click right" in query:
            pyautogui.click(button='right')
            assistant.speak("Right click done")

        # ---------- Volume ----------
        elif "volume" in query:
            if "up" in query or "increase" in query:
                for _ in range(5): pyautogui.press('volumeup')
                assistant.speak("Volume increased")
            elif "down" in query or "decrease" in query:
                for _ in range(5): pyautogui.press('volumedown')
                assistant.speak("Volume decreased")

        # ---------- Media ----------
        elif 'change' in query:
            pyautogui.hotkey('alt','tab')
        elif 'stop' in query or 'resume' in query:
            pyautogui.hotkey('space')
        elif 'next video' in query:
            pyautogui.hotkey('shift','n')

        elif 'video search' in query:
            pyautogui.hotkey('/')
            pyautogui.hotkey('ctrl','a')
            pyautogui.press('backspace')
            assistant.speak("Boss, what should I search?")
            search_query = takeVoice()
            if search_query:
                pyautogui.write(search_query)
                pyautogui.press('enter')
                assistant.speak("Say 'first video' to play the top result.")
                orb.set_state("listening")
                follow_up = takeVoice()
                orb.set_state("idle")
                if follow_up and 'first video' in follow_up.lower():
                    pyautogui.click(x=420, y=420)

        # ---------- Wikipedia ----------
        elif 'wikipedia' in query:
            assistant.speak("Searching Wikipedia...")
            q2 = query.replace('wikipedia','').strip()
            try:
                results = wikipedia.summary(q2, sentences=2)
                assistant.speak("According to Wikipedia")
                assistant.speak(results)
            except:
                assistant.speak("Sorry boss, I couldn't find anything on Wikipedia")

        # ---------- Websites ----------
        elif 'instagram' in query:
            webbrowser.open("https://instagram.com")
        elif 'youtube' in query and 'search' not in query:
            assistant.speak("Opening YouTube")
            webbrowser.open("https://www.youtube.com")
        elif 'youtube' in query and 'search' in query:
            assistant.speak("What do you want to search boss?")
            webbrowser.open("https://www.youtube.com")
            time.sleep(2)
            search_query = takeVoice()
            if search_query:
                pyautogui.write(search_query)
                pyautogui.press('enter')

                # ---------- Brightness ----------
        elif "brightness " in query:
            if "increase" in query or "up" in query:
                assistant.speak(adjust_brightness(+20))     # increase by 20%
                continue

            elif "decrease" in query or "down" in query:
                assistant.speak(adjust_brightness(-20))     # decrease by 20%
                continue

            else:
                # try to catch "set brightness to 50"
                for word in query.split():
                    if word.isdigit():
                        level = int(word)
                        assistant.speak(set_brightness(level))
                        break
                else:
                    assistant.speak("Tell me a brightness level between 0 and 100.")
                continue


        # ---------- Orb Position ----------
        elif 'orb left' in query:
            orb.orb_pos = "left"
            orb.move_to_default()
            assistant.speak("Orb moved to left")
        elif 'orb right' in query:
            orb.orb_pos = "right"
            orb.move_to_default()
            assistant.speak("Orb moved to right")

        # ---------- Scrolling ----------
        elif "scroll down" in query:
            steps = 300
            if "fast" in query: steps = 600
            elif "slow" in query: steps = 150
            pyautogui.scroll(-steps)
        elif "scroll up" in query:
            steps = 300
            if "fast" in query: steps = 600
            elif "slow" in query: steps = 150
            pyautogui.scroll(steps)

        # ---------- Browser Controls ----------
        
        elif "reopen tab" in query:
            pyautogui.hotkey('ctrl','shift','t'); assistant.speak("Last closed tab reopened")
        elif "new window" in query:
            pyautogui.hotkey('ctrl','n'); assistant.speak("New window opened")
        elif "incognito" in query:
            pyautogui.hotkey('ctrl','shift','n'); assistant.speak("Incognito window opened")
        elif "history" in query:
            pyautogui.hotkey('ctrl','h'); assistant.speak("History opened")
        elif "download" in query:
            pyautogui.hotkey('ctrl','j'); assistant.speak("Downloads opened")
        elif "bookmarks" in query:
            pyautogui.hotkey('ctrl','shift','b'); assistant.speak("Bookmarks opened")
        elif "find" in query:
            pyautogui.hotkey('ctrl','f'); assistant.speak("Find on page activated")
        elif "address bar" in query:
            pyautogui.hotkey('ctrl','l'); assistant.speak("Address bar focused")
        elif "back" in query:
            pyautogui.hotkey('alt','left'); assistant.speak("Went back")
        elif "forward" in query:
            pyautogui.hotkey('alt','right'); assistant.speak("Went forward")
        elif "reload" in query:
            pyautogui.hotkey('ctrl','r'); assistant.speak("Page reloaded")
        elif "hard reload" in query:
            pyautogui.hotkey('ctrl','shift','r'); assistant.speak("Page reloaded ignoring cache")
        elif "zoom in" in query:
            pyautogui.hotkey('ctrl','+'); assistant.speak("Zoomed in")
        elif "zoom out" in query:
            pyautogui.hotkey('ctrl','-'); assistant.speak("Zoomed out")
        elif "reset zoom" in query:
            pyautogui.hotkey('ctrl','0'); assistant.speak("Zoom reset")
        elif "full screen" in query:
            pyautogui.press('f11'); assistant.speak("Full screen toggled")
        elif "view source" in query:
            pyautogui.hotkey('ctrl','u'); assistant.speak("Page source opened")
        elif "print page" in query:
            pyautogui.hotkey('ctrl','p'); assistant.speak("Print dialog opened")
        elif "save page" in query:
            pyautogui.hotkey('ctrl','s'); assistant.speak("Save dialog opened")
        elif "extensions" in query:
            pyautogui.hotkey('ctrl','shift','a'); assistant.speak("Extensions opened")
        elif "task manager" in query:
            pyautogui.hotkey('shift','esc'); assistant.speak("Browser task manager opened")
        elif "clear data" in query:
            pyautogui.hotkey('ctrl','shift','delete'); assistant.speak("Clear browsing data dialog opened")
        elif "switch profile" in query:
            pyautogui.hotkey('ctrl','shift','m'); assistant.speak("Profile switch opened")

        # ---------- Window Controls ----------
        elif "minimize window" in query:
            pyautogui.hotkey('win','down'); assistant.speak("Window minimized")
        elif "close window" in query:
            pyautogui.hotkey('alt','f4'); assistant.speak("Window closed")
        elif "switch next window" in query:
            pyautogui.hotkey('alt','tab'); assistant.speak("Switched to next window")
        elif "switch previous window" in query:
            pyautogui.hotkey('alt','shift','tab'); assistant.speak("Switched to previous window")
        elif "switch to tab" in query:
            for i in range(1, 10):
                if f"tab {i}" in query:
                    pyautogui.hotkey('ctrl', str(i))
                    assistant.speak(f"Switched to tab {i}")
                    break

        # ---------- AI fallback ----------
        # ---------- AI fallback ----------
        else:
            response = askAI(query)
            if response:
                assistant.speak(response)
            else:
                assistant.speak("Sorry boss, I didn’t get that.")


        # ---------- Exit ----------
        if 'search complete' in query or 'thanks friday' in query or 'exit' in query or 'quit' in query:
            assistant.speak("Operation complete, have a great day boss")
            orb.close()
            QApplication.quit()
            os._exit(0)
            break



# ==================== MAIN ENTRY ====================

def run_flask():
    flask_app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    # Qt App + Orb first (MAIN thread)
    app = QApplication(sys.argv)
    orb = OrbWidget()
    orb.show()                      # <-- ensures Orb shows before we start Flask

    # Start Flask in the background
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()            # <-- Flask starts AFTER Orb is live

    # Create the assistant first
    assistant = FridayAssistant(orb)

    # Now start the network AFTER assistant exists
    network = FridayNetwork("Friday1", orb, assistant.speak)

    speak("Hey, boss")
    wishMe()

    # Kick off voice activation
    activation(assistant, orb)

    # Start Qt event loop (this keeps Orb running)
    sys.exit(app.exec_())
