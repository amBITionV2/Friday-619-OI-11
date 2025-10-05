# ==========================================================
#  FRIDAY2.PY — Personal Assistant (System 2)
# ==========================================================
import sys, threading, time, math, os, json, asyncio, datetime
import pyttsx3, speech_recognition as sr, webbrowser, websockets
from openai import OpenAI
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QRadialGradient, QColor, QBrush

engine = pyttsx3.init('sapi5')
engine.setProperty('voice', engine.getProperty('voices')[1].id)

def speak(text):
    print("🗣️ Friday2:", text)
    engine.say(text)
    engine.runAndWait()

client = OpenAI(
    api_key="YOUR_GROQ_API_KEY",
    base_url="https://api.groq.com/openai/v1"
)

def askAI(q):
    try:
        res = client.chat.completions.create(
            model="moonshotai/kimi-k2-instruct-0905",
            messages=[{"role": "user", "content": q}],
            temperature=0.7
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        print("AI error:", e)
        return "I couldn’t process that."

# ---------------- Orb ----------------
class OrbWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.state="idle"
        self.base_size=80
        self.orb_size=self.base_size
        self.angle=0
        self.timer=QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(50)

        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint|Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(self.base_size+40,self.base_size+60)
        self.move(100,100)

    def set_state(self,s):
        self.state=s
        self.update()

    def animate(self):
        self.angle+=0.1
        self.orb_size=self.base_size+int(8*math.sin(self.angle))
        self.update()

    def paintEvent(self,e):
        p=QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        c=QColor(255,100,100) if self.state=="listening" else QColor(255,0,150)
        g=QRadialGradient(self.width()/2,self.height()/2,self.orb_size)
        g.setColorAt(0,QColor(255,255,255,230))
        g.setColorAt(1,c)
        p.setBrush(QBrush(g))
        p.setPen(Qt.NoPen)
        p.drawEllipse(10,10,self.orb_size,self.orb_size)

# ---------------- Assistant ---------------
class FridayAssistant:
    def __init__(self, orb):
        self.orb=orb
        self.name="Friday2"
        self.server_uri="ws://10.16.231.155:8765"  # <<< CHANGE THIS
        self.connection=None
        self.loop=asyncio.new_event_loop()
        threading.Thread(target=self.run_network,daemon=True).start()

    async def connect(self):
        while True:
            try:
                async with websockets.connect(self.server_uri) as ws:
                    self.connection=ws
                    await ws.send(json.dumps({"action":"register","name":self.name}))
                    print("✅ Connected as",self.name)
                    async for msg in ws:
                        data=json.loads(msg)
                        if data.get("type")=="message":
                            sender, text = data.get("from"), data.get("text")
                            print(f"📩 {sender}: {text}")
                            self.speak(f"{sender} says: {text}")
            except Exception as e:
                print("⚠️ Network error:",e)
                await asyncio.sleep(5)

    def run_network(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.connect())

    def send_message(self,to,text):
        if not self.connection:
            self.speak("Server not connected yet.")
            return
        asyncio.run_coroutine_threadsafe(
            self.connection.send(json.dumps({
                "action":"message","from":self.name,"to":to,"text":text
            })), self.loop)

    def speak(self,t):
        self.orb.set_state("speaking")
        speak(t)
        self.orb.set_state("idle")

# --------------- Voice -----------------
def takeVoice():
    r=sr.Recognizer()
    with sr.Microphone() as s:
        print("🎤 Listening...")
        r.adjust_for_ambient_noise(s, duration=0.8)
        try:
            audio=r.listen(s,timeout=6,phrase_time_limit=8)
        except sr.WaitTimeoutError:
            return None
    try:
        q=r.recognize_google(audio,language='en-in')
        print("👤 You:",q)
        return q
    except:
        return None

# --------------- Logic -----------------
def activate(a,o):
    a.speak("Friday two is online.")
    while True:
        o.set_state("listening")
        q=takeVoice()
        o.set_state("idle")
        if not q: continue
        q=q.lower()

        if "send message" in q:
            a.speak("What should I tell Friday1?")
            msg=takeVoice()
            if msg: a.send_message("Friday1",msg)
        elif "exit" in q:
            a.speak("Goodbye boss.")
            break
        else:
            a.speak(askAI(q))

if __name__=="__main__":
    app=QApplication(sys.argv)
    orb=OrbWidget()
    orb.show()
    a=FridayAssistant(orb)
    threading.Thread(target=lambda: activate(a,orb),daemon=True).start()
    sys.exit(app.exec_())
