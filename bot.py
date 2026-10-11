import os
import time
import random
import threading
import urllib.parse
from flask import Flask, render_template_string, request, redirect, url_for
from instagrapi import Client
import rudra_brain

app = Flask(__name__, static_folder="static")

# ==========================================
# CUSTOMIZABLE VARIABLES (ज़रूरत के हिसाब से बदलें)
# ==========================================
IG_SESSIONID = os.environ.get("IG_SESSIONID", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OWNER_IG_ID = os.environ.get("OWNER_IG_ID", "ravi_king_official")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", 12))
SESSION_FILE = "session.json"

status_data = {
    "bot_name": rudra_brain.BOT_NAME,
    "developer": rudra_brain.DEVELOPER_NAME,
    "owner_id": OWNER_IG_ID,
    "logged_in": False,
    "ai_active": bool(GEMINI_API_KEY),
    "account_user": "Not Connected",
    "last_checked": "Waiting for Session ID...",
    "replies_sent": 0,
    "error_msg": ""
}

cl_client = None

def login_with_session_id(raw_session_id=None):
    global cl_client, IG_SESSIONID
    if raw_session_id:
        IG_SESSIONID = raw_session_id.strip()

    cl = Client()
    cl.delay_range = [2, 4]

    try:
        if os.path.exists(SESSION_FILE) and not raw_session_id:
            cl.load_settings(SESSION_FILE)
            cl.get_timeline_feed()
            status_data["logged_in"] = True
            status_data["account_user"] = f"ID: {cl.user_id}"
            status_data["error_msg"] = ""
            cl_client = cl
            return cl
    except Exception:
        pass

    if not IG_SESSIONID:
        status_data["error_msg"] = "Please niche Box mein apni Instagram Session ID dalein!"
        status_data["logged_in"] = False
        return None

    try:
        clean_sid = urllib.parse.unquote(IG_SESSIONID.strip())
        cl.login_by_sessionid(clean_sid)
        cl.dump_settings(SESSION_FILE)
        status_data["logged_in"] = True
        status_data["account_user"] = f"ID: {cl.user_id}"
        status_data["error_msg"] = ""
        cl_client = cl
        return cl
    except Exception as e:
        status_data["logged_in"] = False
        status_data["error_msg"] = f"Session Login Error: {e}"
        return None

def rudra_listener():
    global cl_client
    login_with_session_id()
    seen_messages = set()
    initialized = False

    while True:
        if not cl_client or not status_data["logged_in"]:
            time.sleep(8)
            continue

        try:
            my_id = str(cl_client.user_id)

            if not initialized:
                for t in cl_client.direct_threads(amount=10):
                    if t.messages:
                        seen_messages.add(t.messages[0].id)
                initialized = True

            threads = cl_client.direct_threads(amount=10)
            status_data["last_checked"] = time.strftime("%H:%M:%S")

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

                # 1. Check 1-Hour Group Return Rule
                if is_group:
                    reply = rudra_brain.check_1hr_group_return(thread.id, sender)

                # 2. Generate 100% Fresh Emotional Short Reply
                if not reply:
                    rudra_brain.OWNER_IG_ID = status_data["owner_id"]
                    reply = rudra_brain.generate_rudra_reply(sender, msg.text, GEMINI_API_KEY)

                time.sleep(random.uniform(1.5, 3.5))
                cl_client.direct_send(reply, thread_ids=[thread.id])
                status_data["replies_sent"] += 1
                print(f"[Rudra -> @{sender}]: {reply}")

        except Exception as e:
            status_data["error_msg"] = str(e)

        time.sleep(CHECK_INTERVAL)

@app.route("/", methods=["GET", "POST"])
def dashboard():
    global GEMINI_API_KEY
    if request.method == "POST":
        new_sid = request.form.get("sessionid", "").strip()
        new_ai_key = request.form.get("gemini_key", "").strip()
        new_owner = request.form.get("owner_id", "").strip().replace("@", "")

        if new_owner:
            status_data["owner_id"] = new_owner
            rudra_brain.OWNER_IG_ID = new_owner
        if new_ai_key:
            GEMINI_API_KEY = new_ai_key
            status_data["ai_active"] = True
        if new_sid:
            login_with_session_id(new_sid)

        return redirect(url_for("dashboard"))

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ s.bot_name }} Bot - By {{ s.developer }}</title>
        <style>
            body { background: #0f0f0f; color: #fff; font-family: sans-serif; text-align: center; padding: 20px; }
            .box { background: #1c1c1c; padding: 25px; border-radius: 16px; display: inline-block; border: 2px solid #ff0055; max-width: 460px; width: 95%; }
            img { width: 95px; height: 95px; border-radius: 50%; border: 3px solid #00ff88; object-fit: cover; }
            h1 { color: #ff0055; margin: 5px 0; font-size: 22px; }
            .dev { color: #00ff88; font-weight: bold; margin: 4px 0; }
            input[type=text] { width: 88%; padding: 9px; margin: 6px 0; border-radius: 8px; border: 1px solid #444; background: #2a2a2a; color: #fff; }
            button { background: #ff0055; color: #fff; border: none; padding: 10px 22px; border-radius: 8px; cursor: pointer; font-weight: bold; margin-top: 8px; }
            .err { color: #ffaa00; font-size: 13px; }
        </style>
    </head>
    <body>
        <div class="box">
            <img src="/static/ravi.jpg" onerror="this.src='/static/ravi_king_icon_small.png'" alt="Ravi King">
            <h1>🤖 Bot Name: {{ s.bot_name }}</h1>
            <p class="dev">👑 Developer: {{ s.developer }} (@{{ s.owner_id }}) 👑</p>
            <hr style="border-color:#333;">
            <p>Session Login: <b style="color:{{ '#00ff88' if s.logged_in else '#ff4444' }};">{{ s.logged_in }}</b> ({{ s.account_user }})</p>
            <p>Fresh AI Brain Active: <b style="color:{{ '#00ff88' if s.ai_active else '#ff4444' }};">{{ s.ai_active }}</b></p>
            <p>Last Checked: {{ s.last_checked }} | Replies Sent: <b>{{ s.replies_sent }}</b></p>
            {% if s.error_msg %}<p class="err">⚠️ {{ s.error_msg }}</p>{% endif %}
            <hr style="border-color:#333;">
            <form method="POST">
                <input type="text" name="owner_id" placeholder="Owner Insta Username (e.g. ravi_king)" value="{{ s.owner_id }}">
                <input type="text" name="gemini_key" placeholder="Paste Gemini API Key (For 100% New Replies)">
                <input type="text" name="sessionid" placeholder="Paste Instagram Session ID here...">
                <br>
                <button type="submit">Save & Start Rudra 🚀</button>
            </form>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, s=status_data)

threading.Thread(target=rudra_listener, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
