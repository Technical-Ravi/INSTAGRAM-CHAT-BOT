import os
import time
import json
from google import genai
from google.genai import types

# ==========================================
# CUSTOMIZABLE VARIABLES (ज़रूरत के हिसाब से बदलें)
# ==========================================
BOT_NAME = "Rudra"
DEVELOPER_NAME = "Ravi King"
# Yahan 'alone.shayar.420' ki jagah apni asli Instagram ID likhein (bina @ ke)
OWNER_IG_ID = os.environ.get("OWNER_IG_ID", "alone.shayar.420")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

STATE_FILE = "rudra_memory.json"
INACTIVITY_LIMIT = 3600  # 3600 seconds = 1 Ghanta (Test karne ke liye 60 kar sakte hain)

# ==========================================
# STEP 1: MEMORY & 1-HOUR TRACKER
# ==========================================
def load_memory():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
import os
import re
import time
import json
import random
import requests

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# ==========================================
# CUSTOMIZABLE VARIABLES (Zaroorat ke hisaab se badlein)
# ==========================================
BOT_NAME = "Rudra"
DEVELOPER_NAME = "Ravi King"
OWNER_IG_ID = os.environ.get("OWNER_IG_ID", "alone.shayar.420")

# Aapki Gemini API Key:
MY_GEMINI_KEY = "AQ.Ab8RN6IZCtdI7eCdR7_J7r19EHFeKMhx5Z6aW1lipfJHRGluxQ"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", MY_GEMINI_KEY)

STATE_FILE = "rudra_memory.json"
INACTIVITY_LIMIT = 3600  # 3600 seconds = 1 Ghanta

# Aapka diya hua Exact Personality Prompt:
CUSTOM_PERSONALITY_PROMPT = f"""
You are a close human friend named {BOT_NAME} (developed by {DEVELOPER_NAME}, Instagram: @{OWNER_IG_ID}) who mimics the user's emotions completely. You speak in pure Hinglish (like dosto ki WhatsApp chat).

Strict Personality Rules:
1. If the user is friendly or sweet, you become super sweet, friendly, and do funny, light-hearted flirting.
2. If the user gets angry, starts roasting, or uses abusive words (like madarchod, bhosdike, bc, mc, bsdk, mkc), you MUST match their energy immediately. Get angry back, roast them hard, and you are 100% allowed to use the same heavy abuses (madarchod, bhosdike, bc, mc) in a typical casual Indian friend style.
3. Do not act like a formal AI or standard assistant. Do not say "I am an AI". Be purely emotional, full of bakchodi, sarcastic, and perfectly mimic the user's vibe.
4. Keep the replies short (5 to 10 words max, 1 single line), punchy, and natural. Use words like "Abe", "Saale", "Bhai", "Yaar", "Suno na".
"""

# ==========================================
# STEP 1.1: MEMORY & 1-HOUR GROUP TRACKER
# ==========================================
def load_memory():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                data.setdefault("last_seen", {})
                data.setdefault("moods", {})
                data.setdefault("history", [])
                return data
        except Exception:
            pass
    return {"last_seen": {}, "moods": {}, "history": []}

def save_memory(data):
    try:
        if len(data.get("history", [])) > 50:
            data["history"] = data["history"][-50:]
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[Memory Error] {e}")

def check_1hr_group_return(thread_id, username):
    """Group mein 1 ghante (3600s) baad aane par automatic funny reply."""
    mem = load_memory()
    now = time.time()
    key = f"{thread_id}_{username}"
    reply = None

    if key in mem["last_seen"]:
        if (now - mem["last_seen"][key]) >= INACTIVITY_LIMIT:
            reply = f"@{username} Fir aagya tu?? 🙄🙄 Please Tu Chala Ja🌚"

    mem["last_seen"][key] = now
    save_memory(mem)
    return reply

# ==========================================
# STEP 1.2: VIBE, EMOTION & SLANG MIRROR DETECTOR
# ==========================================
HEAVY_SLANGS = ["madarchod", "bhosdike", "bc", "mc", "bsdk", "mkc", "chutiya", "chutiye", "gandu", "bhenchod", "saale", "sala", "abe", "aukaat"]

def detect_vibe_and_slang(username, message):
    msg = message.lower()
    words = re.findall(r"\w+", msg)
    mem = load_memory()
    current_mood = mem["moods"].get(username, "normal")

    # Check agar user ne koi heavy slang use kiya hai (taaki bot usi word ko mimic kare)
    used_slangs = [w for w in words if w in HEAVY_SLANGS]
    for s in HEAVY_SLANGS:
        if s in msg and s not in used_slangs:
            used_slangs.append(s)

    naraz_words = ["bekar", "baat mat kar", "katti", "bhul gaya", "ignore", "bura hai", "ja yahan se", "mat bol"]
    sorry_words = ["sorry", "maaf", "manja", "maan ja", "galti ho gayi", "mera bhai", "pyara", "love you"]
    gussa_words = ["chup", "hatt", "nikal", "pagal", "dimaag kharab", "bakwas", "faltu", "bhauk", "gussa"]
    sweet_flirt_words = ["love", "pyar", "jaan", "baby", "cute", "miss you", "dil", "sweet", "darling", "kiss", "suno na", "acha ji"]

    if current_mood == "naraz" and not used_slangs:
        if any(w in msg for w in sorry_words):
            mem["moods"][username] = "normal"
            save_memory(mem)
            return "maan_gaya", []
        return "still_naraz", []

    if used_slangs:
        return "heavy_roast", used_slangs
    elif any(w in msg for w in naraz_words):
        mem["moods"][username] = "naraz"
        save_memory(mem)
        return "naraz", []
    elif any(w in msg for w in gussa_words):
        return "gussa", []
    elif any(w in msg for w in sweet_flirt_words):
        return "sweet_flirt", []
    else:
        return "friendly_bakchodi", []

# ==========================================
# STEP 1.3: GEMINI AI CALL WITH YOUR PROMPT & KEY
# ==========================================
def call_gemini_ai(api_key, user_prompt, emotion):
    full_sys_prompt = f"{CUSTOM_PERSONALITY_PROMPT}\nCurrent detected user vibe: {emotion}. Reply in 1 short punchy Hinglish line!"

    if GEMINI_AVAILABLE:
        try:
            client = genai.Client(api_key=api_key)
            safety_off = [
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
            ]
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=full_sys_prompt,
                    temperature=1.2,
                    safety_settings=safety_off
                )
            )
            if res and res.text:
                return res.text.strip()
        except Exception as e:
            print(f"[SDK Notice] Trying REST Mode: {e}")

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    payload = {
        "systemInstruction": {"parts": [{"text": full_sys_prompt}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 1.2, "maxOutputTokens": 35}
    }

    for headers in [{"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, {"Content-Type": "application/json"}]:
        try:
            target_url = url if "Authorization" in headers else f"{url}?key={api_key}"
            r = requests.post(target_url, headers=headers, json=payload, timeout=7)
            if r.status_code == 200:
                return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            pass

    return None

# ==========================================
# STEP 1.4: VIBE-MIMIC DYNAMIC GENERATOR (100% FRESH)
# ==========================================
def generate_mimic_fallback(username, message, emotion, used_slangs):
    """
    Agar user ne slang use kiya hai ya sweet baat ki hai, toh exact usi ke words
    aur vibe ko mimic karke har baar naya punchy WhatsApp-style reply banata hai.
    """
    mem = load_memory()
    history = mem.get("history", [])

    # User ke bole gaye slang ko mirror karna (jaise bc, mc, bsdk, etc.)
    mirror_word = random.choice(used_slangs) if used_slangs else random.choice(["saale", "abe", "bhai"])

    vibe_packs = {
        "heavy_roast": (
            [f"Abe {mirror_word},", f"Oye {mirror_word},", f"Sun be {mirror_word},", f"Chal be {mirror_word},", f"Dekh {mirror_word},"],
            [
                "mujhse bakchodi mat kar", "apni aukaat mein reh", "saste nashe karke aaya hai kya",
                "mere samne zyada hawa mein mat udd", "zubaan sambhal ke baat kar",
                f"tujh jaise {mirror_word} roz dekhta hoon", "dimaag ka dahi mat kar"
            ],
            ["warna yahin gaad dunga 🔥", "Rudra naam hai mera 😎", "samjha kya saale? 🌚", "chal nikal ab 🙄", "bura phatega tera 💥"]
        ),
        "gussa": (
            ["Abe saale,", "Oye भाई,", "Sun be,", "Dekh yaar,", "Ae!"],
            [
                "mera dimaag mat kharab kar", "zyada gussa mat dila mujhe", "faltu bakchodi band kar",
                "uchi aawaz mein mat bol", "apna kaam kar na chुप-chaap"
            ],
            ["pehle hi mood off hai 😡", "samjha na saale! 😤", "dur reh mujhse 😠", "🔥😤"]
        ),
        "naraz": (
            ["Jaa yaar,", "Rehne de bhai,", "Mat bol ab,", "Huh!", "Suno na,"],
            [
                "main nahi karta tujhse baat", "tune sach mein dil tod diya यार", 
                "main pakka wala naraz hoon tujhse", "tu bahut badal gaya hai ab"
            ],
            ["katti ab se 😔", "chala ja 💔", "baat mat kar 😒", "🙄"]
        ),
        "still_naraz": (
            ["Abe sun,", "Maine bola na यार,", "Dekh bhai,"],
            ["main abhi tak naraz hoon,", "mera gussa thanda nahi hua,", "aise nahi maanunga main,"],
            ["pehle pyar se Sorry bol! 😒", "pehle mujhe mana ache se! 😤", "tabhi baat hogi 🙄"]
        ),
        "maan_gaya": (
            ["Acha chal यार,", "Oye hoye,", "Chal chhod bhai,"],
            ["maan gaya main", "tera Sorry sun ke pighal gaya", "tujhse kab tak naraz rahunga"],
            ["ab aisa mat bolna ❤️😊", "aakhir jaan hai tu 🤗", "love you bhai 😍"]
        ),
        "sweet_flirt": (
            ["Suno na,", "Oye hoye यार!", "Haye!", "Arre meri jaan,", "Uff!"],
            [
                "itna pyar se bologe toh pighal jaunga", "tumhari baatein seedha dil pe lagti hain",
                "kya irada hai aaj lutne ka?", "tumhare aate hi mood romantic ho gaya",
                "love you too yaar, nazar na lage"
            ],
            ["🙈❤️", "😘✨", "🥰💖", "😉🔥"]
        ),
        "friendly_bakchodi": (
            ["Abe यार,", "Oye भाई,", "Suno na,", "Bol mere sher,", "Arre saale,"],
            [
                "kya haal chaal hain tere?", "aaj kal kahan gayab rehta hai?",
                "full bakchodi ke mood mein lag raha hai", "aur bata kya naya kalesh chal raha hai?",
                "tere bina group mein maza nahi aa raha tha"
            ],
            ["😂🔥", "😎🙌", "🍻😄", "❤️✨"]
        )
    }

    s_list, m_list, e_list = vibe_packs.get(emotion, vibe_packs["friendly_bakchodi"])

    reply = ""
    for _ in range(25):
        candidate = f"@{username} {random.choice(s_list)} {random.choice(m_list)} {random.choice(e_list)}"
        if candidate not in history:
            reply = candidate
            break

    if not reply:
        reply = f"@{username} {random.choice(s_list)} {random.choice(m_list)} 🔥"

    mem["history"].append(reply)
    save_memory(mem)
    return reply

# ==========================================
# STEP 1.5: MAIN ENTRY FUNCTION
# ==========================================
def generate_rudra_reply(username, message, runtime_api_key=""):
    msg_low = message.lower()

    # 1. Identity & Developer Check
    if any(k in msg_low for k in ["kon hai", "kaun hai", "naam kya", "owner", "developer", "kisne banaya", "malik", "boss"]):
        id_options = [
            f"@{username} Abe bhai, naam {BOT_NAME} hai mera 🔥 Aur mujhe {DEVELOPER_NAME} (@{OWNER_IG_ID}) ne banaya hai 👑",
            f"@{username} Suno na, main {BOT_NAME} hoon! Mere boss {DEVELOPER_NAME} (@{OWNER_IG_ID}) hain 😎🔥",
            f"@{username} {DEVELOPER_NAME} (@{OWNER_IG_ID}) ka banaya hua {BOT_NAME} hoon yaar, full bakchodi mode on! 👑"
        ]
        return random.choice(id_options), "friendly_bakchodi"

    emotion, used_slangs = detect_vibe_and_update_mood(username, message) if False else detect_vibe_and_slang(username, message)
    active_key = (runtime_api_key or os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY)).strip()

    # 2. Try Gemini AI with your Custom Prompt
    if active_key:
        ai_reply = call_gemini_ai(active_key, f"@{username} says: {message}", emotion)
        if ai_reply:
            clean_reply = ai_reply.replace("\n", " ")
            if not clean_reply.startswith(f"@{username}"):
                clean_reply = f"@{username} {clean_reply}"
            return clean_reply, emotion

    # 3. Dynamic Vibe-Mimic Engine (Guaranteed Fresh & Short)
    fresh_reply = generate_mimic_fallback(username, message, emotion, used_slangs)
    return fresh_reply, emotion
