from flask import Flask, send_from_directory, jsonify
import subprocess, os, sys, signal, threading

app = Flask(__name__, static_folder='static')

ORB_PY = os.path.join(os.path.dirname(__file__), 'orb.py')
orb_proc = None
proc_lock = threading.Lock()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/static/<path:path>')
def staticfiles(path):
    return send_from_directory('static', path)

@app.route('/start_orb', methods=['POST'])
def start_orb():
    global orb_proc
    with proc_lock:
        if orb_proc and orb_proc.poll() is None:
            return jsonify(success=True, msg='already running')
        try:
            orb_proc = subprocess.Popen([sys.executable, ORB_PY])
            return jsonify(success=True)
        except Exception as e:
            return jsonify(success=False, msg=str(e))

@app.route('/stop_orb', methods=['POST'])
def stop_orb():
    global orb_proc
    with proc_lock:
        if not orb_proc:
            return jsonify(success=True, msg='not running')
        try:
            orb_proc.terminate()
            orb_proc.wait(timeout=4)
        except Exception:
            try: os.kill(orb_proc.pid, signal.SIGKILL)
            except Exception: pass
        orb_proc = None
        return jsonify(success=True)

@app.route('/status')
def status():
    running = False
    with proc_lock:
        if orb_proc and orb_proc.poll() is None:
            running = True
    return jsonify(running=running)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
