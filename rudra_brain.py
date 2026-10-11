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
                return json.load(f)
        except Exception:
            return {"last_seen": {}, "moods": {}}
    return {"last_seen": {}, "moods": {}}

def save_memory(data):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[Memory Error] {e}")

def check_1hr_group_return(thread_id, username):
    """Agar user group mein 1 ghante (3600s) baad message kare toh special reply dega."""
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
# STEP 2: EMOTION & MOOD STATE TRACKER
# ==========================================
def update_and_get_emotion(username, message):
    msg = message.lower()
    words = msg.split()
    mem = load_memory()
    current_mood = mem["moods"].get(username, "normal")

    # Triggers
    naraz_words = ["bekar", "baat mat kar", "katti", "bhul gaya", "ignore", "bura hai", "ja yahan se", "nikal"]
    sorry_words = ["sorry", "maaf", "manja", "maan ja", "galti ho gayi", "love you", "mera bhai"]
    savage_words = ["bc", "mkc", "bsdk", "mc", "chutiya", "chutiye", "gandu", "saale", "aukaat", "abe"]
    gussa_words = ["chup", "hatt", "pagal", "dimaag kharab", "bakwas", "faltu", "bhauk"]
    love_words = ["love", "pyar", "jaan", "baby", "cute", "miss you", "dil", "sweet", "darling"]

    # Agar Rudra pehle se naraz hai
    if current_mood == "naraz":
        if any(w in msg for w in sorry_words):
            mem["moods"][username] = "normal"
            save_memory(mem)
            return "maan_gaya (User apologized, forgive them sweetly)"
        return "still_naraz (You are still upset/rootha hua with this user, demand a proper Sorry first)"

    # Naya emotion check karna
    if any(w in words or w in msg for w in savage_words):
        return "savage_roast (User used aggressive/slang words, reply with matching desi street attitude, sharp and savage)"
    elif any(w in msg for w in naraz_words):
        mem["moods"][username] = "naraz"
        save_memory(mem)
        return "naraz_roothna (User hurt your feelings, act upset/naraz and say you won't talk to them)"
    elif any(w in msg for w in gussa_words):
        return "gussa_angry (User is being rude/annoying, reply with short angry attitude)"
    elif any(w in msg for w in love_words):
        return "pyar_love (User is talking with love/affection, reply very sweetly and lovingly)"
    else:
        return "friendly_human (Normal chill desi friend vibe, witty and natural)"

# ==========================================
# STEP 3: 100% NEW AI REPLY GENERATOR
# ==========================================
def generate_rudra_reply(username, message, runtime_api_key=""):
    api_key = runtime_api_key or os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY)
    emotion_instruction = update_and_get_emotion(username, message)

    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            
            system_prompt = f"""
            Tera naam '{BOT_NAME}' hai. Tujhe '{DEVELOPER_NAME}' (Instagram ID: @{OWNER_IG_ID}) ne banaya hai.
            Tu koi robotic AI nahi hai, tu Instagram par ek asli insaan ki tarah baat karne wala desi ladka hai.

            STRICT RULES JO TUJHE HAMESHA FOLLOW KARNE HAIN:
            1. SHORT REPLY ONLY: Tera har jawab bahut chota (sirf 4 se 10 words ka, 1 single line) hona chahiye. Kabhi lamba reply mat dena.
            2. ALWAYS FRESH: Har baar ekdum naya, unique aur natural Hinglish reply bana.
            3. OWNER & IDENTITY: Agar koi puche ki tera naam kya hai, tujhe kisne banaya, tera owner/developer/boss kaun hai, toh garv se bata ki tera naam {BOT_NAME} hai aur tujhe {DEVELOPER_NAME} (@{OWNER_IG_ID}) ne banaya hai.
            4. CURRENT EMOTION STATE: Abhi samne wale user (@{username}) ke saath tera mood/emotion hai: [{emotion_instruction}]. Isi emotion mein reh kar jawab de!
            5. MENTION USER: Apne reply ki shuruwat mein @{username} zaroor lagana.
            """

            user_prompt = f"User @{username} ne abhi message kiya: '{message}'. Iska ekdum chota (5-8 words) Hinglish reply de."

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=1.1,  # High creativity taaki har baar naya jawab aaye
                )
            )
            if response and response.text:
                clean_reply = response.text.strip().replace("\n", " ")
                if not clean_reply.startswith(f"@{username}"):
                    clean_reply = f"@{username} {clean_reply}"
                return clean_reply
        except Exception as e:
            print(f"[Gemini AI Error] {e}")

    # Agar API key abhi tak nahi daali gayi hai, toh identity aur dynamic short fallback
    msg_low = message.lower()
    if any(k in msg_low for k in ["kon", "kaun", "naam", "owner", "developer", "banaya", "ravi", "rudra"]):
        return f"@{username} Naam {BOT_NAME} hai 🔥 Mujhe {DEVELOPER_NAME} (@{OWNER_IG_ID}) ne banaya hai 👑"
    
    return f"@{username} Oye sun, mere boss @{OWNER_IG_ID} ko bol Dashboard mein Gemini API Key daalein taaki main naye replies de sakun! 😎"
