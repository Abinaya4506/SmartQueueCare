import streamlit as st
import pandas as pd
import sqlite3, urllib.parse, webbrowser
import plotly.express as px
from datetime import datetime
import pytz
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

st.set_page_config(page_title="SmartQueueCare", layout="wide", page_icon="🏥")
IST = pytz.timezone("Asia/Kolkata")

# ── DB ───────────────────────────────────────────────────────────────
conn = sqlite3.connect("smartqueue.db", check_same_thread=False, timeout=10)
conn.execute("PRAGMA journal_mode=WAL")
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS contacts(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sid TEXT, name TEXT, phone TEXT)""")
c.execute("""CREATE TABLE IF NOT EXISTS queue(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT UNIQUE, patient TEXT, phone TEXT,
    severity TEXT, wait_mins INTEGER,
    status TEXT DEFAULT 'waiting', reg_at TEXT)""")
conn.commit()

# ── SESSION ──────────────────────────────────────────────────────────
for k,v in {"auth":False,"lang":"English","token":None,
            "wait":30,"alerts":[],"pname":"","pphone":"","patient_logged_in":False}.items():
    if k not in st.session_state: st.session_state[k] = v

# ── TRANSLATIONS ─────────────────────────────────────────────────────
L = {
 "English":{"title":"SmartQueueCare","name":"Your Name","phone":"Phone Number",
  "sev":["Low","Medium","High"],"hi":"Hello","fill":"Enter name and phone to continue.",
  "tabs":["🏠 Home","🎫 My Token","📞 Contacts","🚨 SOS"],
  "dash":["📊 Prediction","📋 Live Queue","📈 Analysis"],
  "login":"Hospital Login","pwd":"Password","welcome":"Welcome, Hospital Staff 👨‍⚕️",
  "hm":"⚠️ HIGH — inform staff!","mm":"ℹ️ Moderate — stay nearby.","lm":"✅ Low — relax.",
  "mins":"mins","hr":"hr","portals":["🏠 Patient","🏥 Hospital"],
  "enter":"🔓 Enter","logout":"🚪 Logout","sev_lbl":"Severity","pred_btn":"🔮 Predict Wait Time",
  "est_wait":"Est. Wait","tok_title":"🎫 Queue Token","tok_info":"Register below to get your queue token.",
  "get_tok":"🎫 Get My Token","your_tok":"Your Token","st_lbl":"Status","st_wait":"⏳ Waiting",
  "your_turn":"🔔 **YOUR TURN! Please proceed to the counter.**",
  "visit_done":"✅ Your visit is complete.","cancel_tok":"❌ Cancel Token",
  "c_note":"Contacts are auto-used in SOS.","add_c":"➕ Add Contact",
  "c_name":"Name","c_phone":"Phone (with country code)","save_c":"💾 Save Contact",
  "saved":"✅ {} saved!","fill2":"Fill both fields.","no_c":"No contacts yet.",
  "sos_note":"Sends emergency WhatsApp with your token and wait time.",
  "sos_sel":"📞 Contact","sos_to":"SOS will go to **{}**","sos_ph":"Phone (with country code)",
  "sos_hint":"💡 Save contacts for one-tap SOS!","preview":"👁 Preview message",
  "send_sos":"🚨 Send SOS Now","sos_ok":"✅ SOS sent!","need_ph":"Enter a phone number.",
  "wrong_pwd":"❌ Wrong password.","login_btn":"🔐 Login","pred_h":"## Wait Time Predictor",
  "u_sl":"🚨 Urgency (1=Low, 5=Critical)","sp_sl":"👨‍⚕️ Specialist Availability",
  "nr_sl":"👩‍⚕️ Nurse-to-Patient Ratio","b_sl":"🛏️ Available Beds","pred_go":"🔮 Predict","cat":"🔖 Category",
  "c_low":"🟢 Low","c_mod":"🟡 Moderate","c_high":"🔴 High",
  "w_long":"⚠️ Long wait — add staff/beds.","w_mod":"ℹ️ Moderate — monitor flow.","w_ok":"✅ Acceptable.",
  "live_q":"## 📋 Live Queue Dashboard","sos_alert_n":"🚨 {} SOS ALERT(S) — Patients need immediate attention!",
  "sos_lbl":"🚨 SOS ALERT","p_lbl":"Patient","ec_lbl":"Emergency Contact Notified",
  "dismiss":"✅ Dismiss All Alerts","clr_q":"🗑️ Clear Queue","q_done":"Queue cleared!",
  "no_pats":"No patients in queue yet.","mw":"⏳ Waiting","mc":"🔔 Called","md":"✅ Done","mt":"📋 Total",
  "call_now":"📢 Call Now","called":"✅ {} called!","wa_n":"📱 Notify {} on WhatsApp",
  "mk_done":"✅ Mark Done","done_n":"✅ Done! Total served today: {}",
  "s_wait":"⏳ Waiting","s_call":"🔔 Called","s_done":"✅ Done","s_can":"❌ Cancelled",
  "pie_t":"Active Queue by Severity","pie_c":"🔍 Live severity breakdown of patients in queue.",
  "analysis":"## 📈 Data Analysis","rec":"📋 Records","avgw":"⏱ Avg Wait","acc":"🎯 Accuracy",
  "up_t":"Urgency Distribution","up_c":"🔍 Medium urgency dominates — prioritize high urgency cases.",
  "wh_t":"Wait Time Distribution","wh_c":"🔍 Right-skewed — a few patients wait much longer.",
  "wb_t":"Wait Time by Urgency","wb_c":"🔍 Higher urgency = wider variance — faster triage needed.",
  "ns_t":"Nurse Ratio vs Wait Time","ns_c":"🔍 More nurses = shorter wait time.","db":"Dashboard"},

 "தமிழ்":{"title":"ஸ்மார்ட் க்யூ கேர்","name":"உங்கள் பெயர்","phone":"தொலைபேசி எண்",
  "sev":["குறைவு","மிதமான","அதிகம்"],"hi":"வணக்கம்","fill":"பெயர் மற்றும் தொலைபேசி உள்ளிடவும்.",
  "tabs":["🏠 முகப்பு","🎫 என் டோக்கன்","📞 தொடர்புகள்","🚨 SOS"],
  "dash":["📊 கணிப்பு","📋 நேரடி வரிசை","📈 பகுப்பாய்வு"],
  "login":"மருத்துவமனை உள்நுழைவு","pwd":"கடவுச்சொல்","welcome":"வணக்கம் 👨‍⚕️",
  "hm":"⚠️ அதிக தீவிரம்!","mm":"ℹ️ மிதமான.","lm":"✅ குறைவு.",
  "mins":"நிமிடம்","hr":"மணி","portals":["🏠 நோயாளி","🏥 மருத்துவமனை"],
  "enter":"🔓 உள்ளே செல்","logout":"🚪 வெளியேறு","sev_lbl":"தீவிரம்","pred_btn":"🔮 காத்திருப்பு நேரம் கணிக்கவும்",
  "est_wait":"மதிப்பிடப்பட்ட காத்திருப்பு","tok_title":"🎫 வரிசை டோக்கன்","tok_info":"உங்கள் வரிசை டோக்கன் பெற பதிவு செய்யுங்கள்.",
  "get_tok":"🎫 என் டோக்கன் பெறு","your_tok":"உங்கள் டோக்கன்","st_lbl":"நிலை","st_wait":"⏳ காத்திருக்கிறது",
  "your_turn":"🔔 **உங்கள் முறை! தயவுசெய்து கவுண்டருக்கு செல்லுங்கள்.**",
  "visit_done":"✅ உங்கள் வருகை முடிந்தது.","cancel_tok":"❌ டோக்கன் ரத்து செய்",
  "c_note":"SOS-இல் தொடர்புகள் தானாகப் பயன்படுத்தப்படும்.","add_c":"➕ தொடர்பு சேர்",
  "c_name":"பெயர்","c_phone":"தொலைபேசி (நாட்டு குறியீட்டுடன்)","save_c":"💾 தொடர்பு சேமி",
  "saved":"✅ {} சேமிக்கப்பட்டது!","fill2":"இரண்டு புலங்களையும் நிரப்பவும்.","no_c":"இன்னும் தொடர்புகள் இல்லை.",
  "sos_note":"உங்கள் டோக்கன் மற்றும் காத்திருப்பு நேரத்துடன் அவசர வாட்ஸ்அப் அனுப்புகிறது.",
  "sos_sel":"📞 தொடர்பு","sos_to":"SOS **{}**-க்கு செல்லும்","sos_ph":"தொலைபேசி (நாட்டு குறியீட்டுடன்)",
  "sos_hint":"💡 ஒற்றை-தட்டு SOS-க்கு தொடர்புகளை சேமிக்கவும்!","preview":"👁 செய்தி முன்னோட்டம்",
  "send_sos":"🚨 இப்போது SOS அனுப்பு","sos_ok":"✅ SOS அனுப்பப்பட்டது!","need_ph":"தொலைபேசி எண்ணை உள்ளிடவும்.",
  "wrong_pwd":"❌ தவறான கடவுச்சொல்.","login_btn":"🔐 உள்நுழைவு","pred_h":"## காத்திருப்பு நேர கணிப்பு",
  "u_sl":"🚨 அவசரம் (1=குறைவு, 5=நெருக்கடி)","sp_sl":"👨‍⚕️ நிபுணர் கிடைக்கும் தன்மை",
  "nr_sl":"👩‍⚕️ நர்ஸ்-நோயாளி விகிதம்","b_sl":"🛏️ கிடைக்கும் படுக்கைகள்","pred_go":"🔮 கணிக்கவும்","cat":"🔖 வகை",
  "c_low":"🟢 குறைவு","c_mod":"🟡 மிதமான","c_high":"🔴 அதிகம்",
  "w_long":"⚠️ நீண்ட காத்திருப்பு — ஊழியர்கள்/படுக்கைகள் சேர்க்கவும்.",
  "w_mod":"ℹ️ மிதமான — ஓட்டத்தை கண்காணிக்கவும்.","w_ok":"✅ ஏற்றுக்கொள்ளத்தக்கது.",
  "live_q":"## 📋 நேரடி வரிசை டாஷ்போர்டு","sos_alert_n":"🚨 {} SOS எச்சரிக்கை(கள்) — நோயாளிகளுக்கு உடனடி கவனம் தேவை!",
  "sos_lbl":"🚨 SOS எச்சரிக்கை","p_lbl":"நோயாளி","ec_lbl":"அவசர தொடர்பு அறிவிக்கப்பட்டது",
  "dismiss":"✅ அனைத்து எச்சரிக்கைகளையும் நிராகரி","clr_q":"🗑️ வரிசையை அழி","q_done":"வரிசை அழிக்கப்பட்டது!",
  "no_pats":"இன்னும் வரிசையில் நோயாளிகள் இல்லை.","mw":"⏳ காத்திருக்கிறது","mc":"🔔 அழைக்கப்பட்டது","md":"✅ முடிந்தது","mt":"📋 மொத்தம்",
  "call_now":"📢 இப்போது அழைக்கவும்","called":"✅ {} அழைக்கப்பட்டார்!","wa_n":"📱 வாட்ஸ்அப்பில் {} அறிவிக்கவும்",
  "mk_done":"✅ முடிந்தது என குறி","done_n":"✅ முடிந்தது! இன்று மொத்தம் சேவை: {}",
  "s_wait":"⏳ காத்திருக்கிறது","s_call":"🔔 அழைக்கப்பட்டது","s_done":"✅ முடிந்தது","s_can":"❌ ரத்து செய்யப்பட்டது",
  "pie_t":"தீவிரத்தால் செயலில் உள்ள வரிசை","pie_c":"🔍 வரிசையில் உள்ள நோயாளிகளின் நேரடி தீவிர பகுப்பாய்வு.",
  "analysis":"## 📈 தரவு பகுப்பாய்வு","rec":"📋 பதிவுகள்","avgw":"⏱ சராசரி காத்திருப்பு","acc":"🎯 துல்லியம்",
  "up_t":"அவசர விநியோகம்","up_c":"🔍 நடுத்தர அவசரம் ஆதிக்கம் — உயர் அவசர நடவடிக்கைகளுக்கு முன்னுரிமை.",
  "wh_t":"காத்திருப்பு நேர விநியோகம்","wh_c":"🔍 வலது-சாய்வு — சில நோயாளிகள் மிக நீண்ட நேரம் காத்திருக்கிறார்கள்.",
  "wb_t":"அவசரத்தால் காத்திருப்பு நேரம்","wb_c":"🔍 அதிக அவசரம் = அதிக மாறுபாடு — வேகமான தர வரிசை தேவை.",
  "ns_t":"நர்ஸ் விகிதம் vs காத்திருப்பு நேரம்","ns_c":"🔍 அதிக நர்ஸ்கள் = குறைவான காத்திருப்பு நேரம்.","db":"டாஷ்போர்டு"},

 "हिंदी":{"title":"स्मार्टक्यूकेयर","name":"आपका नाम","phone":"फोन नंबर",
  "sev":["कम","मध्यम","उच्च"],"hi":"नमस्ते","fill":"नाम और फोन दर्ज करें।",
  "tabs":["🏠 होम","🎫 मेरा टोकन","📞 संपर्क","🚨 SOS"],
  "dash":["📊 पूर्वानुमान","📋 लाइव क्यू","📈 विश्लेषण"],
  "login":"अस्पताल लॉगिन","pwd":"पासवर्ड","welcome":"स्वागत है 👨‍⚕️",
  "hm":"⚠️ उच्च — तुरंत बताएं!","mm":"ℹ️ मध्यम.","lm":"✅ कम.",
  "mins":"मिनट","hr":"घंटा","portals":["🏠 मरीज","🏥 अस्पताल"],
  "enter":"🔓 प्रवेश करें","logout":"🚪 लॉगआउट","sev_lbl":"गंभीरता","pred_btn":"🔮 प्रतीक्षा समय का अनुमान लगाएं",
  "est_wait":"अनुमानित प्रतीक्षा","tok_title":"🎫 कतार टोकन","tok_info":"अपना कतार टोकन पाने के लिए नीचे पंजीकरण करें।",
  "get_tok":"🎫 मेरा टोकन प्राप्त करें","your_tok":"आपका टोकन","st_lbl":"स्थिति","st_wait":"⏳ प्रतीक्षारत",
  "your_turn":"🔔 **आपकी बारी! कृपया काउंटर पर जाएं।**",
  "visit_done":"✅ आपकी यात्रा पूरी हो गई।","cancel_tok":"❌ टोकन रद्द करें",
  "c_note":"संपर्क SOS में स्वतः उपयोग होते हैं।","add_c":"➕ संपर्क जोड़ें",
  "c_name":"नाम","c_phone":"फोन (देश कोड सहित)","save_c":"💾 संपर्क सहेजें",
  "saved":"✅ {} सहेजा गया!","fill2":"दोनों फ़ील्ड भरें।","no_c":"अभी कोई संपर्क नहीं।",
  "sos_note":"आपके टोकन और प्रतीक्षा समय के साथ आपातकालीन व्हाट्सएप भेजता है।",
  "sos_sel":"📞 संपर्क","sos_to":"SOS **{}** को जाएगा","sos_ph":"फोन (देश कोड सहित)",
  "sos_hint":"💡 एक-टैप SOS के लिए संपर्क सहेजें!","preview":"👁 संदेश पूर्वावलोकन",
  "send_sos":"🚨 अभी SOS भेजें","sos_ok":"✅ SOS भेजा गया!","need_ph":"फोन नंबर दर्ज करें।",
  "wrong_pwd":"❌ गलत पासवर्ड।","login_btn":"🔐 लॉगिन","pred_h":"## प्रतीक्षा समय पूर्वानुमानकर्ता",
  "u_sl":"🚨 तात्कालिकता (1=कम, 5=गंभीर)","sp_sl":"👨‍⚕️ विशेषज्ञ उपलब्धता",
  "nr_sl":"👩‍⚕️ नर्स-रोगी अनुपात","b_sl":"🛏️ उपलब्ध बेड","pred_go":"🔮 अनुमान लगाएं","cat":"🔖 श्रेणी",
  "c_low":"🟢 कम","c_mod":"🟡 मध्यम","c_high":"🔴 उच्च",
  "w_long":"⚠️ लंबी प्रतीक्षा — कर्मचारी/बेड बढ़ाएं।","w_mod":"ℹ️ मध्यम — प्रवाह की निगरानी करें।","w_ok":"✅ स्वीकार्य।",
  "live_q":"## 📋 लाइव कतार डैशबोर्ड","sos_alert_n":"🚨 {} SOS अलर्ट — मरीजों को तत्काल ध्यान चाहिए!",
  "sos_lbl":"🚨 SOS अलर्ट","p_lbl":"मरीज","ec_lbl":"आपातकालीन संपर्क को सूचित किया",
  "dismiss":"✅ सभी अलर्ट हटाएं","clr_q":"🗑️ कतार साफ करें","q_done":"कतार साफ हो गई!",
  "no_pats":"अभी कतार में कोई मरीज नहीं।","mw":"⏳ प्रतीक्षारत","mc":"🔔 बुलाया गया","md":"✅ पूर्ण","mt":"📋 कुल",
  "call_now":"📢 अभी बुलाएं","called":"✅ {} को बुलाया गया!","wa_n":"📱 व्हाट्सएप पर {} को सूचित करें",
  "mk_done":"✅ पूर्ण चिह्नित करें","done_n":"✅ पूर्ण! आज कुल सेवा: {}",
  "s_wait":"⏳ प्रतीक्षारत","s_call":"🔔 बुलाया गया","s_done":"✅ पूर्ण","s_can":"❌ रद्द",
  "pie_t":"गंभीरता के अनुसार सक्रिय कतार","pie_c":"🔍 कतार में मरीजों का लाइव गंभीरता विश्लेषण।",
  "analysis":"## 📈 डेटा विश्लेषण","rec":"📋 रिकॉर्ड","avgw":"⏱ औसत प्रतीक्षा","acc":"🎯 सटीकता",
  "up_t":"तात्कालिकता वितरण","up_c":"🔍 मध्यम तात्कालिकता प्रभावी — उच्च तात्कालिकता मामलों को प्राथमिकता दें।",
  "wh_t":"प्रतीक्षा समय वितरण","wh_c":"🔍 दाईं ओर झुका — कुछ मरीज बहुत लंबे समय तक प्रतीक्षा करते हैं।",
  "wb_t":"तात्कालिकता के अनुसार प्रतीक्षा समय","wb_c":"🔍 अधिक तात्कालिकता = अधिक भिन्नता — तेज़ ट्राइएज की जरूरत।",
  "ns_t":"नर्स अनुपात vs प्रतीक्षा समय","ns_c":"🔍 अधिक नर्स = कम प्रतीक्षा समय।","db":"डैशबोर्ड"},
}

lang = st.sidebar.selectbox("🌐 Language", list(L.keys()),
       index=list(L.keys()).index(st.session_state.lang))
st.session_state.lang = lang
T = L[lang]
portal = st.sidebar.radio("Portal", T["portals"])
st.sidebar.title(T["title"])

# ── MODEL ────────────────────────────────────────────────────────────
@st.cache_data
def load_model():
    try:
        df = pd.read_csv("hospital_wait_time.csv")
    except FileNotFoundError:
        st.error("❌ 'hospital_wait_time.csv' not found in the project folder.")
        st.stop()
    df["Urgency Level"] = df["Urgency Level"].map({"Low":1,"Medium":3,"High":5,"Critical":5})
    df["UxS"] = df["Urgency Level"] * df["Specialist Availability"]
    df["BpN"] = df["Facility Size (Beds)"] / (df["Nurse-to-Patient Ratio"] + 1)
    df["SS"]  = df["Specialist Availability"] + df["Nurse-to-Patient Ratio"]
    F = ["Urgency Level","Specialist Availability","Nurse-to-Patient Ratio",
         "Facility Size (Beds)","UxS","BpN","SS"]
    X, y = df[F], df["Total Wait Time (min)"]
    Xt,Xv,yt,yv = train_test_split(X, y, test_size=0.2, random_state=42)
    m = RandomForestRegressor(n_estimators=500, random_state=42, n_jobs=-1).fit(Xt, yt)
    return df, m, round(r2_score(yv, m.predict(Xv))*100, 1)

df, model, acc = load_model()

# ── HELPERS ──────────────────────────────────────────────────────────
def predict(u, sp=3, nr=4, b=100):
    row = {"Urgency Level":u,"Specialist Availability":sp,"Nurse-to-Patient Ratio":nr,
           "Facility Size (Beds)":b,"UxS":u*sp,"BpN":b/(nr+1),"SS":sp+nr}
    return int(model.predict(pd.DataFrame([row]))[0])

def fmt(m):
    return f"{m} {T['mins']}" if m < 60 else f"{m//60} {T['hr']} {m%60} {T['mins']}"

def now():
    return datetime.now(IST).strftime("%I:%M %p IST")

def get_contacts(sid):
    return c.execute("SELECT id,name,phone FROM contacts WHERE sid=?", (sid,)).fetchall()

def next_token():
    rows = c.execute("SELECT token FROM queue").fetchall()
    nums = [int(r[0].split("-")[1]) for r in rows if r[0].startswith("T-")] or [0]
    return f"T-{max(nums)+1:03d}"

# ════════════════════════════════════════════════════════════════════
#  PATIENT PORTAL
# ════════════════════════════════════════════════════════════════════
if portal == T["portals"][0]:
    st.title(f"🏥 {T['title']}")
    col1, col2 = st.columns(2)
    pname  = col1.text_input(T["name"],  key="inp_name",  placeholder="e.g. Ravi Kumar")
    pphone = col2.text_input(T["phone"], key="inp_phone", placeholder="9876543210", max_chars=10)
    if pname:  st.session_state.pname  = pname
    else:      pname  = st.session_state.pname
    if pphone: st.session_state.pphone = pphone
    else:      pphone = st.session_state.pphone

    if not st.session_state.get("patient_logged_in"):
        if st.button(T["enter"], use_container_width=True, type="primary"):
            if pname and pphone:
                st.session_state.patient_logged_in = True
                st.rerun()
            else:
                st.warning(T["fill"])
        st.stop()
    else:
        lc1, lc2 = st.columns([5,1])
        lc1.success(f"👋 {T['hi']}, {pname}!")
        with lc2:
            if st.button(T["logout"]):
                st.session_state.patient_logged_in = False
                st.session_state.pname  = ""
                st.session_state.pphone = ""
                st.session_state.token  = None
                st.rerun()

    sid = pphone
    t1, t2, t3, t4 = st.tabs(T["tabs"])

    # ── HOME ─────────────────────────────────────────────────────────
    with t1:
        sev = st.selectbox(T["sev_lbl"], T["sev"])
        urg = {T["sev"][0]:1, T["sev"][1]:3, T["sev"][2]:5}[sev]
        if st.button(T["pred_btn"], use_container_width=True):
            w = predict(urg); st.session_state.wait = w
            icon = "🟢" if w<30 else ("🟡" if w<60 else "🔴")
            st.metric(f"{icon} {T['est_wait']}", fmt(w))
            st.caption(f"⏰ {now()}")
            msg = T["hm"] if sev==T["sev"][2] else (T["mm"] if sev==T["sev"][1] else T["lm"])
            (st.warning if sev==T["sev"][2] else st.info if sev==T["sev"][1] else st.success)(msg)

    # ── TOKEN ─────────────────────────────────────────────────────────
    with t2:
        st.markdown(f"### {T['tok_title']}")
        token = st.session_state.token

        if not token:
            st.info(T["tok_info"])
            sev2 = st.selectbox(T["sev_lbl"], T["sev"], key="tok_sev")
            urg2 = {T["sev"][0]:1, T["sev"][1]:3, T["sev"][2]:5}[sev2]
            if st.button(T["get_tok"], use_container_width=True, type="primary"):
                w = predict(urg2); st.session_state.wait = w
                tk = next_token()
                c.execute("""INSERT OR IGNORE INTO queue
                    (token,patient,phone,severity,wait_mins,status,reg_at)
                    VALUES(?,?,?,?,?,?,?)""",
                    (tk, pname, pphone, sev2, w, "waiting", now()))
                conn.commit()
                st.session_state.token = tk
                st.rerun()
        else:
            row = c.execute("""SELECT token,patient,phone,severity,wait_mins,status,reg_at
                               FROM queue WHERE token=?""", (token,)).fetchone()
            if not row:
                st.session_state.token = None; st.rerun()

            tk, rname, rphone, rsev, rwait, rstatus, rtime = row
            clr = {"High":"#ef4444","Medium":"#f59e0b","Low":"#22c55e",
                   T["sev"][2]:"#ef4444",T["sev"][1]:"#f59e0b",T["sev"][0]:"#22c55e"}.get(rsev,"#3b82f6")

            st.markdown(f"""
            <div style="background:linear-gradient(135deg,{clr}22,#fff);border:2px solid {clr};
                border-radius:16px;padding:24px;text-align:center;margin-bottom:16px;">
                <div style="font-size:13px;color:#666">{T['your_tok']}</div>
                <div style="font-size:56px;font-weight:900;color:{clr};letter-spacing:4px">{tk}</div>
                <div style="color:#555;margin-top:6px">👤 {rname} &nbsp;|&nbsp; 📱 {rphone}</div>
                <div style="color:#888;font-size:13px">{T['sev_lbl']}: <b>{rsev}</b> &nbsp;|&nbsp; {rtime}</div>
            </div>""", unsafe_allow_html=True)

            if rstatus == "waiting":
                b_, bb = st.columns(2)
                b_.metric(T["est_wait"], fmt(rwait))
                bb.metric(T["st_lbl"], T["st_wait"])
            elif rstatus == "called":
                st.success(T["your_turn"])
                st.balloons()
            elif rstatus == "done":
                st.info(T["visit_done"])

            if st.button(T["cancel_tok"], use_container_width=True):
                c.execute("UPDATE queue SET status='cancelled' WHERE token=?", (tk,))
                conn.commit(); st.session_state.token = None; st.rerun()

    # ── CONTACTS ──────────────────────────────────────────────────────
    with t3:
        st.caption(T["c_note"])
        with st.expander(T["add_c"], expanded=not get_contacts(sid)):
            new_name  = st.text_input(T["c_name"], key="cn")
            new_phone = st.text_input(T["c_phone"], placeholder="919876543210", key="cp")
            if st.button(T["save_c"], use_container_width=True):
                if new_name and new_phone:
                    c.execute("INSERT INTO contacts(sid,name,phone) VALUES(?,?,?)", (sid,new_name,new_phone))
                    conn.commit(); st.success(T["saved"].format(new_name)); st.rerun()
                else: st.warning(T["fill2"])
        for cid, cname, cphone in get_contacts(sid):
            r1,r2,r3,r4 = st.columns([3,3,2,1])
            r1.write(f"👤 **{cname}**"); r2.write(f"📱 {cphone}")
            r3.markdown(f"[💬 WhatsApp](https://wa.me/{cphone})")
            with r4:
                if st.button("🗑️", key=f"d{cid}"):
                    c.execute("DELETE FROM contacts WHERE id=?", (cid,))
                    conn.commit(); st.rerun()
        if not get_contacts(sid): st.info(T["no_c"])

    # ── SOS ───────────────────────────────────────────────────────────
    with t4:
        st.warning(T["sos_note"])
        cts = get_contacts(sid)
        avg_high = c.execute("SELECT AVG(wait_mins) FROM queue WHERE severity='High' AND status IN ('waiting','called')").fetchone()[0]
        avg_high_txt = f"{int(avg_high)} {T['mins']}" if avg_high else f"approximately 30–60 {T['mins']}"
        sos_msg = (f"🚨 EMERGENCY ALERT from SmartQueueCare!\n"
                   f"Patient: {pname} | 📱 {pphone}\n"
                   f"🏥 Needs IMMEDIATE attention at the hospital!\n\n"
                   f"⏱️ Current avg wait for HIGH severity patients: {avg_high_txt}\n"
                   f"⚡ This patient requires PRIORITY treatment — please do NOT wait in queue.\n\n"
                   f"➡️ Reach the hospital within {avg_high_txt} or call the patient immediately!\n"
                   f"⏰ Alert sent at: {now()}")
        if cts:
            opts = {f"{n} ({p})": p for _,n,p in cts}
            sel  = st.selectbox(T["sos_sel"], list(opts.keys()))
            sos_phone = opts[sel]
            st.info(T["sos_to"].format(sel))
        else:
            sos_phone = st.text_input(T["sos_ph"], placeholder="919876543210")
            st.caption(T["sos_hint"])
        with st.expander(T["preview"]): st.code(sos_msg)
        if st.button(T["send_sos"], use_container_width=True, type="primary"):
            if sos_phone:
                webbrowser.open(f"https://wa.me/{sos_phone}?text={urllib.parse.quote(sos_msg)}")
                contact_label = sel if cts else sos_phone
                st.session_state.alerts.append({"Time":now(),"Patient":pname,"Phone":pphone,"EmergencyContact":contact_label})
                st.success(T["sos_ok"])
            else: st.error(T["need_ph"])

# ════════════════════════════════════════════════════════════════════
#  HOSPITAL PORTAL
# ════════════════════════════════════════════════════════════════════
elif portal == T["portals"][1]:
    st.title(f"🏥 {T['title']}")
    if not st.session_state.auth:
        st.markdown(f"### 🔒 {T['login']}")
        pwd = st.text_input(T["pwd"], type="password")
        if st.button(T["login_btn"], use_container_width=True):
            if pwd == "hospital123": st.session_state.auth = True; st.rerun()
            else: st.error(T["wrong_pwd"])
        st.stop()

    hc1, hc2 = st.columns([5,1])
    hc1.markdown(f"### {T['welcome']}")
    with hc2:
        if st.button(T["logout"]): st.session_state.auth = False; st.rerun()

    page = st.sidebar.radio(T["db"], T["dash"])

    # ── PREDICTION ───────────────────────────────────────────────────
    if page == T["dash"][0]:
        st.markdown(T["pred_h"])
        col1, col2 = st.columns(2)
        with col1:
            u  = st.slider(T["u_sl"], 1, 5, 3)
            sp = st.slider(T["sp_sl"], 1, 10, 3)
        with col2:
            nr = st.slider(T["nr_sl"], 1, 10, 4)
            b  = st.slider(T["b_sl"], 10, 500, 100, step=10)
        if st.button(T["pred_go"], use_container_width=True):
            w = predict(u, sp, nr, b)
            m1, m2, m3 = st.columns(3)
            m1.metric("⏱ " + T["est_wait"], fmt(w))
            m2.metric(T["cat"], T["c_low"] if w<30 else T["c_mod"] if w<60 else T["c_high"])
            (st.warning if w>=60 else st.info if w>=30 else st.success)(
             T["w_long"] if w>=60 else T["w_mod"] if w>=30 else T["w_ok"])

    # ── LIVE QUEUE ───────────────────────────────────────────────────
    elif page == T["dash"][1]:
        st.markdown(T["live_q"])

        if st.session_state.alerts:
            st.error(T["sos_alert_n"].format(len(st.session_state.alerts)))
            for a in reversed(st.session_state.alerts):
                st.markdown(f"""
                <div style="background:#fef2f2;border-left:5px solid #ef4444;border-radius:8px;padding:12px 16px;margin-bottom:6px">
                  <b style="color:#ef4444">{T['sos_lbl']}</b> &nbsp;|&nbsp; ⏰ {a['Time']}<br>
                  👤 <b>{T['p_lbl']}:</b> {a['Patient']} &nbsp;|&nbsp; 📱 {a['Phone']}<br>
                  📞 <b>{T['ec_lbl']}:</b> {a['EmergencyContact']}
                </div>""", unsafe_allow_html=True)
            if st.button(T["dismiss"]):
                st.session_state.alerts = []; st.rerun()
            st.divider()

        cl, _ = st.columns([1,4])
        with cl:
            if st.button(T["clr_q"]):
                c.execute("DELETE FROM queue"); conn.commit()
                st.session_state.token = None
                st.success(T["q_done"]); st.rerun()

        rows = c.execute("""SELECT token,patient,phone,severity,wait_mins,status,reg_at
                            FROM queue ORDER BY id""").fetchall()
        if not rows:
            st.info(T["no_pats"])
        else:
            waiting = [r for r in rows if r[5]=="waiting"]
            called  = [r for r in rows if r[5]=="called"]
            done    = [r for r in rows if r[5]=="done"]
            m1,m2,m3,m4 = st.columns(4)
            m1.metric(T["mw"], len(waiting))
            m2.metric(T["mc"], len(called))
            m3.metric(T["md"], len(done))
            m4.metric(T["mt"], len(rows))
            st.divider()

            for tk, pn, ph, sv, wt, st_, rt in rows:
                sclr  = {"High":"🔴","Medium":"🟡","Low":"🟢"}.get(sv,"⚪")
                badge = {"waiting":T["s_wait"],"called":T["s_call"],
                         "done":T["s_done"],"cancelled":T["s_can"]}.get(st_, st_)
                a,b_,cc,d,e,f = st.columns([2,3,2,2,2,2])
                a.markdown(f"**{tk}**"); b_.write(pn)
                cc.write(f"{sclr} {sv}"); d.write(fmt(wt)); e.write(badge)
                with f:
                    if st_ == "waiting":
                        if st.button(T["call_now"], key=f"call_{tk}", type="primary"):
                            c.execute("UPDATE queue SET status='called' WHERE token=?", (tk,))
                            conn.commit()
                            msg = f"SmartQueueCare: Token {tk} — YOUR TURN! Proceed to counter. {now()}"
                            wa  = f"https://wa.me/91{ph}?text={urllib.parse.quote(msg)}"
                            st.success(T["called"].format(pn))
                            st.markdown(f"[{T['wa_n'].format(pn)}]({wa})")
                            st.balloons()
                    elif st_ == "called":
                        if st.button(T["mk_done"], key=f"done_{tk}"):
                            c.execute("UPDATE queue SET status='done' WHERE token=?", (tk,))
                            conn.commit()
                            done_count = c.execute("SELECT COUNT(*) FROM queue WHERE status='done'").fetchone()[0]
                            st.success(T["done_n"].format(done_count))
                            st.rerun()
                st.divider()

            sdf = pd.DataFrame(rows, columns=["token","name","phone","sev","wait","status","time"])
            active = sdf[sdf["status"].isin(["waiting","called"])]
            if not active.empty:
                fig = px.pie(active, names="sev", title=T["pie_t"],
                             color_discrete_map={"High":"#ef4444","Medium":"#f59e0b","Low":"#22c55e"})
                st.plotly_chart(fig, use_container_width=True)
                st.caption(T["pie_c"])

    # ── ANALYSIS ─────────────────────────────────────────────────────
    elif page == T["dash"][2]:
        st.markdown(T["analysis"])
        m1, m2, m3 = st.columns(3)
        m1.metric(T["rec"],  len(df))
        m2.metric(T["avgw"], f"{int(df['Total Wait Time (min)'].mean())} {T['mins']}")
        m3.metric(T["acc"],  f"{acc}%")
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            f1 = px.pie(df, names="Urgency Level", title=T["up_t"],
                        color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(f1, use_container_width=True)
            st.caption(T["up_c"])
            f2 = px.histogram(df, x="Total Wait Time (min)", nbins=30,
                              title=T["wh_t"], color_discrete_sequence=["#e74c3c"])
            st.plotly_chart(f2, use_container_width=True)
            st.caption(T["wh_c"])
        with col2:
            f3 = px.box(df, x="Urgency Level", y="Total Wait Time (min)",
                        title=T["wb_t"], color_discrete_sequence=["#3b82f6"])
            st.plotly_chart(f3, use_container_width=True)
            st.caption(T["wb_c"])
            f4 = px.scatter(df, x="Nurse-to-Patient Ratio", y="Total Wait Time (min)",
                            trendline="ols", title=T["ns_t"],
                            color_discrete_sequence=["#22c55e"])
            st.plotly_chart(f4, use_container_width=True)
            st.caption(T["ns_c"])
