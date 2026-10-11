import os
import re
import time
import random
import threading
import urllib.parse
from flask import Flask, render_template_string, request, redirect, url_for
from instagrapi import Client
import rudra_brain

app = Flask(__name__, static_folder="static")

# ==========================================
# CUSTOMIZABLE VARIABLES (Zaroorat ke hisaab se badlein)
# ==========================================
DEFAULT_COOKIE = "Csrftoken=zG1pH59sADOl0KudEa71Or3erDvWo4Zz;ds_user_id=48375386992;datr=3Za0akqrdNzsMt2Wq-4HHzH3;ig_did=5BBC5B81-47AE-4876-B15E-1F2B93DB6322;ps_l=1;ps_n=1;mid=arSW5AABAAGaENQikZ0PQFe6q_Td;dpr=2.294114351272583;sessionid=48375386992%3AaALzZvrk15BrFx%3A17%3AAYmTItDHyZFUMjTh5zbWya-7nFsLaVOLAflYdtc_rQ;wd=471x555"
DEFAULT_API_KEY = "AQ.Ab8RN6IZCtdI7eCdR7_J7r19EHFeKMhx5Z6aW1lipfJHRGluxQ"

IG_SESSIONID = os.environ.get("IG_SESSIONID", DEFAULT_COOKIE)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", DEFAULT_API_KEY)
OWNER_IG_ID = os.environ.get("OWNER_IG_ID", "alone.shayar.420")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", 10))
SESSION_FILE = "session.json"

status_data = {
    "bot_name": rudra_brain.BOT_NAME,
    "developer": rudra_brain.DEVELOPER_NAME,
    "owner_id": OWNER_IG_ID,
    "logged_in": False,
    "ai_active": True,
    "account_user": "Not Connected",
    "last_checked": "Starting...",
    "last_emotion": "WhatsApp Friend Mode 😎",
    "replies_sent": 0,
    "error_msg": ""
}

cl_client = None
listener_thread = None

def parse_cookie_string(raw_input):
    cookies = {}
    raw_input = (raw_input or "").strip()
    if ";" in raw_input or "sessionid=" in raw_input.lower():
        for part in raw_input.split(";"):
            if "=" in part:
                k, v = part.strip().split("=", 1)
                cookies[k.strip().lower()] = urllib.parse.unquote(v.strip())
    else:
        cookies["sessionid"] = urllib.parse.unquote(raw_input)
    return cookies

def login_with_session_id(raw_session_id=None):
    global cl_client, IG_SESSIONID
    if raw_session_id:
        IG_SESSIONID = raw_session_id.strip()

    cl = Client()
    cl.delay_range = [2, 4]
    cookies = parse_cookie_string(IG_SESSIONID)
    clean_sid = cookies.get("sessionid", "")

    if not clean_sid:
        status_data["error_msg"] = "Please Session ID dalein!"
        status_data["logged_in"] = False
        return None

    try:
        cl.login_by_sessionid(clean_sid)
        cl.dump_settings(SESSION_FILE)
        status_data["logged_in"] = True
        status_data["account_user"] = f"ID: {cl.user_id}"
        status_data["error_msg"] = ""
        cl_client = cl
        return cl
    except Exception:
        pass

    try:
        user_id = cookies.get("ds_user_id") or clean_sid.split(":")[0]
        csrf = cookies.get("csrftoken", "")
        cl.private.cookies.update({
            "sessionid": clean_sid,
            "ds_user_id": str(user_id),
            "csrftoken": csrf,
            "mid": cookies.get("mid", ""),
            "ig_did": cookies.get("ig_did", "")
        })
        if csrf:
            cl.private.headers.update({"X-CSRFToken": csrf})
        cl.direct_threads(amount=1)
        status_data["logged_in"] = True
        status_data["account_user"] = f"ID: {user_id}"
        status_data["error_msg"] = ""
        cl_client = cl
        return cl
    except Exception as e2:
        status_data["logged_in"] = False
        status_data["error_msg"] = f"Login Error: {e2}"
        return None

def rudra_listener():
    global cl_client
    if not cl_client or not status_data["logged_in"]:
        login_with_session_id()

    seen_messages = set()
    initialized = False

    while True:
        try:
            status_data["last_checked"] = time.strftime("%H:%M:%S")

            if not cl_client or not status_data["logged_in"]:
                time.sleep(8)
                continue

            my_id = str(getattr(cl_client, "user_id", "") or "48375386992")

            if not initialized:
                for t in cl_client.direct_threads(amount=10):
                    if t.messages:
                        seen_messages.add(t.messages[0].id)
                initialized = True

            threads = cl_client.direct_threads(amount=10)

            for thread in threads:
                if not thread.messages:
                    continue
                msg = thread.messages[0]
                if str(msg.user_id) == my_id or msg.id in seen_messages:
                    continue

                seen_messages.add(msg.id)
                if not msg.text:
                    continue

                sender = "dost"
                for u in thread.users:
                    if str(u.pk) == str(msg.user_id):
                        sender = u.username
                        break

                is_group = len(thread.users) > 1
                reply = None
                emotion = "1hr_roast"

                # 1. Check 1-Hour Group Return Rule
                if is_group:
                    reply = rudra_brain.check_1hr_group_return(thread.id, sender)

                # 2. Generate Vibe-Mimic Short Reply
                if not reply:
                    rudra_brain.OWNER_IG_ID = status_data["owner_id"]
                    reply, emotion = rudra_brain.generate_rudra_reply(sender, msg.text, GEMINI_API_KEY)

                status_data["last_emotion"] = emotion.upper()

                time.sleep(random.uniform(1.5, 3.0))
                cl_client.direct_send(reply, thread_ids=[thread.id])
                status_data["replies_sent"] += 1
                status_data["error_msg"] = ""
                print(f"[Rudra ({emotion}) -> @{sender}]: {reply}")

        except Exception as e:
            status_data["error_msg"] = f"Loop Notice: {e}"

        time.sleep(CHECK_INTERVAL)

def ensure_listener_running():
    global listener_thread
    if listener_thread is None or not listener_thread.is_alive():
        listener_thread = threading.Thread(target=rudra_listener, daemon=True)
        listener_thread.start()

@app.route("/", methods=["GET", "POST"])
def dashboard():
    global GEMINI_API_KEY
    ensure_listener_running()

    if request.method == "POST":
        new_sid = request.form.get("sessionid", "").strip()
        new_ai_key = request.form.get("gemini_key", "").strip()
        new_owner = request.form.get("owner_id", "").strip().replace("@", "")

        if new_owner:
            status_data["owner_id"] = new_owner
            rudra_brain.OWNER_IG_ID = new_owner
        if new_ai_key:
            GEMINI_API_KEY = new_ai_key
            rudra_brain.GEMINI_API_KEY = new_ai_key
        if new_sid:
            login_with_session_id(new_sid)

        ensure_listener_running()
        return redirect(url_for("dashboard"))

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ s.bot_name }} Bot - By {{ s.developer }}</title>
        <meta http-equiv="refresh" content="15">
        <style>
            body { background: #0f0f0f; color: #fff; font-family: sans-serif; text-align: center; padding: 20px; }
            .box { background: #1c1c1c; padding: 25px; border-radius: 16px; display: inline-block; border: 2px solid #ff0055; max-width: 460px; width: 95%; }
            .avatar { width: 95px; height: 95px; border-radius: 50%; border: 3px solid #00ff88; object-fit: cover; background: #2a2a2a; }
            h1 { color: #ff0055; margin: 5px 0; font-size: 22px; }
            .dev { color: #00ff88; font-weight: bold; margin: 4px 0; }
            input[type=text] { width: 88%; padding: 9px; margin: 6px 0; border-radius: 8px; border: 1px solid #444; background: #2a2a2a; color: #fff; }
            button { background: #ff0055; color: #fff; border: none; padding: 10px 22px; border-radius: 8px; cursor: pointer; font-weight: bold; margin-top: 8px; }
            .err { color: #ffaa00; font-size: 13px; }
        </style>
    </head>
    <body>
        <div class="box">
            <img class="avatar" src="/static/ravi.jpg" onerror="this.src='https://cdn-icons-png.flaticon.com/512/4712/4712035.png'" alt="Ravi King">
            <h1>🤖 Bot Name: {{ s.bot_name }}</h1>
            <p class="dev">👑 Developer: {{ s.developer }} (@{{ s.owner_id }}) 👑</p>
            <hr style="border-color:#333;">
            <p>Session Login: <b style="color:{{ '#00ff88' if s.logged_in else '#ff4444' }};">{{ s.logged_in }}</b> ({{ s.account_user }})</p>
            <p>Current Vibe Mode: <b style="color:#ff0055;">{{ s.last_emotion }}</b></p>
            <p>Last Checked: <b>{{ s.last_checked }}</b> | Replies Sent: <b>{{ s.replies_sent }}</b></p>
            {% if s.error_msg %}<p class="err">⚠️ {{ s.error_msg }}</p>{% endif %}
            <hr style="border-color:#333;">
            <form method="POST">
                <input type="text" name="owner_id" placeholder="Owner Insta Username" value="{{ s.owner_id }}">
                <input type="text" name="gemini_key" placeholder="Update Gemini API Key (Optional)">
                <input type="text" name="sessionid" placeholder="Update Instagram Session ID (Optional)">
                <br>
                <button type="submit">Save & Start Rudra 🚀</button>
            </form>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, s=status_data)

ensure_listener_running()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
