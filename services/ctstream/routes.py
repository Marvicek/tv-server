
from bottle import Bottle, response
import threading, time, json, subprocess, requests, os

ctstream_app = Bottle()
STATE_FILE = "channels_state.json"
ONLINE_URL = "https://hbbtv.ceskatelevize.cz/online/services/data/online.json"

state = {"channels": {}}

def load_state():
    global state
    if os.path.exists(STATE_FILE):
        state = json.load(open(STATE_FILE))

def save_state():
    json.dump(state, open(STATE_FILE, "w"), indent=2)

def update_online():
    while True:
        try:
            data = requests.get(ONLINE_URL, timeout=10).json()
            for it in data:
                ch = it.get("encoder")
                if not ch:
                    continue
                if ch not in state["channels"]:
                    state["channels"][ch] = {
                        "status": "unknown",
                        "title": it.get("programTitle"),
                        "last_test": None,
                        "last_ok": None
                    }
            save_state()
        except Exception as e:
            print("update_online error", e)
        time.sleep(1800)

def start_ct_updater():
    load_state()
    t = threading.Thread(target=update_online, daemon=True)
    t.start()

@ctstream_app.get("/playlist/ct_playlist.m3u")
def playlist():
    response.content_type = "audio/x-mpegurl; charset=utf-8"
    out = ["#EXTM3U"]
    for ch, meta in state["channels"].items():
        if meta["status"] == "dead":
            continue
        name = meta.get("title") or ch
        out.append(f'#EXTINF:-1 tvg-name="{name}",{name}')
        out.append(f"http://127.0.0.1:8080/ct/play/dash/{ch}")
    return "\n".join(out) + "\n"

@ctstream_app.get("/play/dash/<ch>")
def play_dash(ch):
    api = f"https://api.ceskatelevize.cz/video/v1/playlist-live/v1/stream-data/channel/{ch}?canPlayDrm=false&streamType=dash"
    data = requests.get(api, timeout=10).json()
    return requests.get(data["streamUrls"]["dash"], allow_redirects=True).text
