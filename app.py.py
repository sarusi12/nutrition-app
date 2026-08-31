import streamlit as st
import requests
import urllib.parse
from datetime import date, datetime
from supabase import create_client, Client

# --- Streamlit Page Config & Mobile Viewport Fix for Safari ---
st.set_page_config(page_title="NutriFlow / מחשבון תזונה", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    """,
    unsafe_allow_html=True
)

# --- Language Dictionaries (i18n) ---
TRANSLATIONS = {
    "עברית (Hebrew)": {
        "app_title": "🥗 מחשבון תזונה, אימונים ויומן אישי",
        "login_title": "🔐 התחברות למערכת התזונה",
        "email": "אימייל",
        "password": "סיסמה",
        "remember_me": "זכור אותי תמיד",
        "login_btn": "התחבר",
        "signup_tab": "הרשמה",
        "login_tab": "התחברות",
        "signup_btn": "הירשם כעת",
        "signup_email": "אימייל להרשמה",
        "signup_pass": "סיסמה (לפחות 6 תווים)",
        "welcome": "👋 ברוך הבא! בוא נגדיר את הפרופיל שלך",
        "welcome_sub": "הכנס את הנתונים שלך כדי שנחשב עבורך את היעדים היומיים המדויקים:",
        "gender": "מין",
        "male": "גבר",
        "female": "אישה",
        "age": "גיל",
        "height": "גובה (בס\"מ)",
        "weight": "משקל (בק\"ג)",
        "activity_level": "רמת פעילות גופנית",
        "goal": "מה המטרה שלך?",
        "calc_goals": "חשב יעדים ושמור",
        "logout": "התנתק",
        "connected_as": "מחובר כ:",
        "date_header": "📅 תאריך ויעדים",
        "tab_log": "📝 יומן אכילה",
        "tab_search": "🔍 חיפוש והוספה",
        "tab_workouts": "💪 אימונים ושריפת קלוריות",
        "tab_history": "📅 היסטוריה ויומן",
        "tab_camera": "📸 סריקת תמונה",
        "tab_ai": "🤖 יועץ AI",
        "tab_settings": "⚙️ הגדרות פרופיל",
        "search_food": "חפש מאכל מהמאגר או הקלד לסינון",
        "unit_type": "יחידת מידה",
        "amount_val": "כמות",
        "meal_type": "לאיזו ארוחה?",
        "breakfast": "בוקר",
        "lunch": "צהריים",
        "dinner": "ערב",
        "snack": "נשנוש / אימון",
        "add_btn": "הוסף מאכל נבחר ליומן",
        "daily_summary": "📊 סיכום יומי (כולל קיזוז אימונים)",
        "calories": "קלוריות",
        "protein": "חלבון",
        "carbs": "פחמימות",
        "fat": "שומן",
        "workouts_header": "🏋️ תיעוד אימון חדש",
        "workout_type": "סוג האימון",
        "workout_duration": "משך האימון (בדקות)",
        "add_workout_btn": "הוסף אימון ליומן",
        "settings_header": "⚙️ הגדרות פרופיל ופרטי חשבון",
        "theme_label": "מצב תצוגה (Theme)",
        "theme_options": ["אוטומטי (לפי השעה/מערכת)", "מצב כהה (Dark)", "מצב בהיר (Light)"],
        "save_settings": "שמור שינויים בפרופיל",
        "account_update": "🔐 עדכון פרטי חשבון (אימייל וסיסמה)",
        "new_email": "אימייל חדש",
        "new_password": "סיסמה חדשה (השאר ריק אם אין ברצונך לשנות)",
        "update_account": "עדכן פרטי התחברות"
    },
    "English": {
        "app_title": "🥗 Nutrition, Workouts & Food Log",
        "login_title": "🔐 Login to Nutrition System",
        "email": "Email",
        "password": "Password",
        "remember_me": "Remember Me",
        "login_btn": "Login",
        "signup_tab": "Sign Up",
        "login_tab": "Login",
        "signup_btn": "Register Now",
        "signup_email": "Registration Email",
        "signup_pass": "Password (at least 6 chars)",
        "welcome": "👋 Welcome! Let's set up your profile",
        "welcome_sub": "Enter your details to calculate your precise daily goals:",
        "gender": "Gender",
        "male": "Male",
        "female": "Female",
        "age": "Age",
        "height": "Height (cm)",
        "weight": "Weight (kg)",
        "activity_level": "Activity Level",
        "goal": "What is your goal?",
        "calc_goals": "Calculate Goals & Save",
        "logout": "Logout",
        "connected_as": "Connected as:",
        "date_header": "📅 Date & Goals",
        "tab_log": "📝 Food Log",
        "tab_search": "🔍 Search & Add",
        "tab_workouts": "💪 Workouts & Calories",
        "tab_history": "📅 History & Calendar",
        "tab_camera": "📸 Image Scan",
        "tab_ai": "🤖 AI Advisor",
        "tab_settings": "⚙️ Profile Settings",
        "search_food": "Search food from DB or type to filter",
        "unit_type": "Unit type",
        "amount_val": "Amount",
        "meal_type": "Meal type?",
        "breakfast": "Breakfast",
        "lunch": "Lunch",
        "dinner": "Dinner",
        "snack": "Snack / Workout",
        "add_btn": "Add selected food to log",
        "daily_summary": "📊 Daily Summary",
        "calories": "Calories",
        "protein": "Protein",
        "carbs": "Carbs",
        "fat": "Fat",
        "workouts_header": "🏋️ Log New Workout",
        "workout_type": "Workout Type",
        "workout_duration": "Duration (minutes)",
        "calories_burned": "Estimated Calories Burned",
        "add_workout_btn": "Add Workout",
        "settings_header": "⚙️ Profile & Account Settings",
        "theme_label": "Display Theme",
        "theme_options": ["Automatic (Time/System based)", "Dark Mode", "Light Mode"],
        "save_settings": "Save Profile Changes",
        "account_update": "🔐 Account Update (Email & Password)",
        "new_email": "New Email",
        "new_password": "New Password (leave blank to keep)",
        "update_account": "Update Credentials"
    }
}

# Language state selection
if "lang" not in st.session_state:
    st.session_state["lang"] = "עברית (Hebrew)"

selected_lang = st.sidebar.selectbox("🌐 Choose Language / בחר שפה", list(TRANSLATIONS.keys()), index=list(TRANSLATIONS.keys()).index(st.session_state["lang"]))
st.session_state["lang"] = selected_lang
t = TRANSLATIONS[selected_lang]

# Theme state selection
if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "אוטומטי (לפי השעה/מערכת)"

current_hour = datetime.now().hour
is_automatic_dark = (current_hour < 6 or current_hour >= 19)

mode = st.session_state["theme_mode"]
if "כהה" in mode or "Dark" in mode:
    is_dark = True
elif "בהיר" in mode or "Light" in mode:
    is_dark = False
else:
    is_dark = is_automatic_dark

bg_color = "#0e1117" if is_dark else "#f8f9fa"
text_color = "#ffffff" if is_dark else "#111111"
widget_bg = "rgba(255, 255, 255, 0.05)" if is_dark else "rgba(0, 0, 0, 0.03)"
widget_border = "rgba(255, 255, 255, 0.1)" if is_dark else "rgba(0, 0, 0, 0.08)"

# --- Clean CSS Styling (תיקון מלא לתפריט צד/סרגלים שנתקעים באמצע המסך באייפון וספארי) ---
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        direction: rtl;
        text-align: right;
        -webkit-text-size-adjust: 100%;
    }}
    
    /* תיקון קריטי לסרגלים ותפריטי צד באייפון/ספארי שלא יישארו באמצע המסך */
    section[data-testid="stSidebar"] {{
        background-color: {bg_color} !important;
        position: relative !important;
        z-index: 999999 !important;
    }}
    
    div[data-testid="stSidebarNav"] {{
        direction: rtl !important;
    }}

    .ios-widget {{
        background: {widget_bg};
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid {widget_border};
        border-radius: 20px;
        padding: 16px 12px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
        margin-bottom: 12px;
        text-align: center;
        min-height: 125px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        word-break: break-word;
    }}

    .ios-widget h4 {{
        font-size: 0.95em;
        margin: 0 0 6px 0 !important;
        font-weight: 600;
    }}

    .ios-widget h2 {{
        font-size: 1.6em !important;
        margin: 4px 0 6px 0 !important;
        line-height: 1.2;
        font-weight: 700;
    }}

    .ios-widget p {{
        font-size: 0.8em !important;
        margin: 0 !important;
        opacity: 0.85;
        line-height: 1.3;
    }}

    .meal-summary-widget {{
        background: {widget_bg};
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border: 1px solid {widget_border};
        border-radius: 16px;
        padding: 8px;
        text-align: center;
        margin-bottom: 10px;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        direction: rtl;
        gap: 4px;
        background-color: {widget_bg};
        padding: 4px;
        border-radius: 16px;
        display: flex;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 12px;
        padding: 8px 12px;
        color: {text_color};
        white-space: nowrap;
        font-size: 0.85em;
        flex-shrink: 0;
    }}

    .streamlit-expanderHeader {{
        background-color: {widget_bg} !important;
        border: 1px solid {widget_border} !important;
        border-radius: 14px !important;
        direction: rtl !important;
        text-align: right !important;
    }}

    @media screen and (max-width: 768px) {{
        .row-widget.stHorizontal {{
            flex-direction: column !important;
        }}
        div[data-testid="column"] {{
            width: 100% !important;
            flex: 100% !important;
            min-width: unset !important;
            margin-bottom: 10px;
        }}
        .stButton button {{
            width: 100% !important;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# --- Supabase Initialization ---
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- מאגר מובנה ענק ועשיר (כולל מסעדות, ג'אנק פוד וצ'יטים) ---
LOCAL_DATABASE = {
    # --- בסיסי וביצים ---
    "ביצה שלמה (גדולה / L)": {"cal": 75.0, "p": 6.3, "c": 0.4, "f": 5.3},
    "חביתה (משתי ביצים מטוגנת בשמן רגיל)": {"cal": 185.0, "p": 13.0, "c": 1.0, "f": 13.5},
    "חביתה (משתי ביצים מטוגנת בשמן זית)": {"cal": 190.0, "p": 13.0, "c": 1.0, "f": 14.0},
    "חביתה (משלוש ביצים מטוגנת בשמן רגיל)": {"cal": 270.0, "p": 19.5, "c": 1.5, "f": 19.5},
    "חביתה (משלוש ביצים מטוגנת בשמן זית)": {"cal": 278.0, "p": 19.5, "c": 1.5, "f": 20.2},
    "חביתת ירק (משתי ביצים עם עשבי תיבול, בשמן רגיל)": {"cal": 195.0, "p": 13.2, "c": 2.0, "f": 14.0},
    "חביתת ירק (משתי ביצים עם עשבי תיבול, בשמן זית)": {"cal": 200.0, "p": 13.2, "c": 2.0, "f": 14.5},
    "ביצה קשה": {"cal": 75.0, "p": 6.3, "c": 0.4, "f": 5.3},
    "ביצת עין (מטוגנת בשמן רגיל)": {"cal": 92.0, "p": 6.3, "c": 0.5, "f": 7.2},
    "ביצת עין (מטוגנת בשמן זית)": {"cal": 96.0, "p": 6.3, "c": 0.5, "f": 7.6},
    "חלבון ביצה (לבן בלבד)": {"cal": 52.0, "p": 10.9, "c": 0.7, "f": 0.2},
    
    # --- רטבים וממרחים ---
    "מיונז (כף / 15 גרם)": {"cal": 105.0, "p": 0.1, "c": 0.1, "f": 11.5},
    "מיונז קל (כף / 15 גרם)": {"cal": 45.0, "p": 0.1, "c": 1.0, "f": 4.5},
    "קטשופ (כף / 15 גרם)": {"cal": 15.0, "p": 0.2, "c": 3.5, "f": 0.0},
    "רוטב סרירצ'ה (כף / 15 גרם)": {"cal": 18.0, "p": 0.3, "c": 3.8, "f": 0.2},
    "רוטב צ'ילי מתוק (כף / 15 גרם)": {"cal": 35.0, "p": 0.1, "c": 8.5, "f": 0.1},
    "רוטב שום ומיונז (כף / 15 גרם)": {"cal": 95.0, "p": 0.2, "c": 1.2, "f": 10.0},
    "רוטב אלף האיים (כף / 15 גרם)": {"cal": 75.0, "p": 0.2, "c": 2.0, "f": 7.5},
    "חרדל (כף / 15 גרם)": {"cal": 10.0, "p": 0.6, "c": 0.8, "f": 0.6},
    "רוטב ויניגרט / חרדל דבש (כף / 15 גרם)": {"cal": 45.0, "p": 0.1, "c": 2.5, "f": 4.0},
    "טחינה מוכנה (כף / 15 גרם)": {"cal": 43.0, "p": 1.3, "c": 1.6, "f": 4.0},
    "רוטב סויה (כף / 15 גרם)": {"cal": 8.0, "p": 1.2, "c": 0.8, "f": 0.0},
    "רוטב טריאקי (כף / 15 גרם)": {"cal": 25.0, "p": 0.4, "c": 5.8, "f": 0.0},
    
    # --- לחמים וטוסטים ---
    "טוסט מלחם אחיד עם גבינה צהובה 9%": {"cal": 240.0, "p": 16.0, "c": 30.0, "f": 5.0},
    "טוסט מלחם אחיד עם גבינה צהובה 28%": {"cal": 300.0, "p": 14.0, "c": 30.0, "f": 12.0},
    "טוסט מלחם קל עם גבינה צהובה 9%": {"cal": 180.0, "p": 17.0, "c": 20.0, "f": 4.0},
    "טוסט מלחם קל עם גבינה צהובה 28%": {"cal": 240.0, "p": 15.0, "c": 20.0, "f": 11.0},
    
    # --- סלטים ---
    "סלט ירקות קצוץ (עם כפית שמן זית)": {"cal": 55.0, "p": 1.2, "c": 4.5, "f": 4.0},
    "סלט ירקות קצוץ (ללא שמן)": {"cal": 20.0, "p": 1.0, "c": 4.2, "f": 0.3},
    "סלט יווני (עם בולגרית וזיתים)": {"cal": 110.0, "p": 4.5, "c": 5.0, "f": 8.5},
    "סלט כרוב לבן ומיונז": {"cal": 180.0, "p": 1.1, "c": 6.0, "f": 17.0},
    "סלט כרוב אדום בלימון ושמן זית": {"cal": 70.0, "p": 1.3, "c": 6.5, "f": 4.5},
    "סלט טונה עשיר": {"cal": 150.0, "p": 14.0, "c": 3.0, "f": 9.0},
    "סלט חסה עלי רוקט ורוטב ויניגרט": {"cal": 65.0, "p": 1.5, "c": 4.0, "f": 5.0},
    "סלט עגבניות שרי ובצל סגול": {"cal": 45.0, "p": 1.2, "c": 5.5, "f": 2.5},
    "סלט קיסר (עם קרוטונים ופרמזן)": {"cal": 190.0, "p": 6.0, "c": 12.0, "f": 13.0},
    "סלט סלק מבושל קצוץ": {"cal": 45.0, "p": 1.6, "c": 10.0, "f": 0.2},
    
    # --- חלבונים ומעדנים ---
    "טחינה גולמית": {"cal": 595.0, "p": 17.0, "c": 21.0, "f": 53.8},
    "חמאת בוטנים טבעית / רגילה": {"cal": 588.0, "p": 25.0, "c": 20.0, "f": 50.0},
    "משקה חלבון יטבתה PRO 40g": {"cal": 64.0, "p": 16.0, "c": 3.2, "f": 0.4},
    "משקה חלבון יטבתה PRO 25g": {"cal": 52.0, "p": 10.0, "c": 3.8, "f": 0.5},
    "משקה חלבון תנובה GO 25g": {"cal": 50.0, "p": 10.0, "c": 4.0, "f": 0.4},
    "משקה חלבון שטראוס 25g": {"cal": 50.0, "p": 10.0, "c": 4.0, "f": 0.5},
    "מעדן מילקי פרו": {"cal": 85.0, "p": 10.0, "c": 8.0, "f": 1.5},
    "יוגורט חלבון 20g": {"cal": 60.0, "p": 10.0, "c": 4.0, "f": 0.4},
    "אבקת חלבון (סקופ סטנדרטי)": {"cal": 400.0, "p": 80.0, "c": 6.0, "f": 3.0},
    "חזה עוף": {"cal": 165.0, "p": 31.0, "c": 0.0, "f": 3.6},
    "חזה עוף מבושל": {"cal": 165.0, "p": 31.0, "c": 0.0, "f": 3.6},
    "שניצל עוף": {"cal": 230.0, "p": 18.0, "c": 14.0, "f": 11.0},
    "פרגיות": {"cal": 209.0, "p": 24.0, "c": 0.0, "f": 12.0},
    "סטייק אנטריקוט": {"cal": 271.0, "p": 24.0, "c": 0.0, "f": 19.0},
    "בשר בקר טחון 5%": {"cal": 137.0, "p": 21.4, "c": 0.0, "f": 5.0},
    "בשר בקר טחון 15%": {"cal": 215.0, "p": 19.0, "c": 0.0, "f": 15.0},
    "הודו טחון": {"cal": 149.0, "p": 22.0, "c": 0.0, "f": 6.5},
    "סינטה בקר": {"cal": 160.0, "p": 26.0, "c": 0.0, "f": 6.0},
    "טונה במים": {"cal": 116.0, "p": 26.0, "c": 0.0, "f": 1.0},
    "טונה בשמן": {"cal": 198.0, "p": 29.0, "c": 0.0, "f": 8.2},
    "סלמון": {"cal": 206.0, "p": 22.0, "c": 0.0, "f": 12.3},
    "סלמון אפוי": {"cal": 231.0, "p": 25.0, "c": 0.0, "f": 13.4},
    "דניס": {"cal": 96.0, "p": 18.0, "c": 0.0, "f": 2.5},
    "מושט / אמנון": {"cal": 96.0, "p": 20.0, "c": 0.0, "f": 1.7},
    "בקלה": {"cal": 82.0, "p": 18.0, "c": 0.0, "f": 0.7},
    "שרימפס": {"cal": 99.0, "p": 24.0, "c": 0.2, "f": 0.3},
    "קוטג' 5%": {"cal": 95.0, "p": 11.0, "c": 1.5, "f": 5.0},
    "קוטג' 3%": {"cal": 80.0, "p": 11.0, "c": 1.5, "f": 3.0},
    "גבינה לבנה 5%": {"cal": 100.0, "p": 10.0, "c": 3.5, "f": 5.0},
    "גבינה צהובה 28%": {"cal": 350.0, "p": 25.0, "c": 1.0, "f": 28.0},
    "גבינה צהובה 9%": {"cal": 170.0, "p": 30.0, "c": 1.0, "f": 9.0},
    "יוגורט 3%": {"cal": 60.0, "p": 4.0, "c": 4.5, "f": 3.0},
    "יוגורט טבעי 0%": {"cal": 40.0, "p": 5.0, "c": 5.0, "f": 0.2},
    "חלב 3%": {"cal": 60.0, "p": 3.3, "c": 4.7, "f": 3.0},
    "חלב 1%": {"cal": 42.0, "p": 3.4, "c": 4.8, "f": 1.0},

    # --- פחמימות ותוספות ---
    "אורז לבן מבושל": {"cal": 130.0, "p": 2.7, "c": 28.0, "f": 0.3},
    "אורז מלא מבושל": {"cal": 111.0, "p": 2.6, "c": 23.0, "f": 0.9},
    "פסטה מבושלת": {"cal": 131.0, "p": 5.0, "c": 25.0, "f": 1.1},
    "תפוח אדמה מבושל": {"cal": 87.0, "p": 1.9, "c": 20.1, "f": 0.1},
    "פירה תפוחי אדמה": {"cal": 110.0, "p": 2.0, "c": 15.0, "f": 5.0},
    "בטטה מבושלת": {"cal": 86.0, "p": 1.6, "c": 20.0, "f": 0.1},
    "שיבולת שועל": {"cal": 389.0, "p": 16.9, "c": 66.3, "f": 6.9},
    "קינואה מבושלת": {"cal": 120.0, "p": 4.4, "c": 21.3, "f": 1.9},
    "כוסמת מבושלת": {"cal": 92.0, "p": 3.4, "c": 19.9, "f": 0.6},
    "בורגול מבושל": {"cal": 83.0, "p": 3.1, "c": 18.6, "f": 0.2},
    "לחם אחיד": {"cal": 245.0, "p": 9.0, "c": 48.0, "f": 2.0},
    "לחם קל": {"cal": 190.0, "p": 10.0, "c": 35.0, "f": 1.5},
    "לחם מלא / פשתן": {"cal": 250.0, "p": 12.0, "c": 41.0, "f": 3.5},
    "פרוסת לחם אחיד / מלא": {"cal": 75.0, "p": 3.0, "c": 14.0, "f": 1.0},
    "פיתה": {"cal": 275.0, "p": 8.5, "c": 55.0, "f": 1.2},
    "אורז בסמטי מבושל": {"cal": 130.0, "p": 2.8, "c": 28.0, "f": 0.2},
    "קוסקוס מבושל": {"cal": 112.0, "p": 3.8, "c": 23.2, "f": 0.2},

    # --- ירקות ופירות ---
    "שעועית ירוקה": {"cal": 31.0, "p": 1.8, "c": 7.0, "f": 0.1},
    "שעועית ירוקה מבושלת": {"cal": 35.0, "p": 1.9, "c": 7.9, "f": 0.2},
    "ברוקולי": {"cal": 34.0, "p": 2.8, "c": 6.6, "f": 0.4},
    "כרובית": {"cal": 25.0, "p": 1.9, "c": 5.0, "f": 0.3},
    "עגבנייה": {"cal": 18.0, "p": 0.9, "c": 3.9, "f": 0.2},
    "מלפפון": {"cal": 15.0, "p": 0.6, "c": 3.6, "f": 0.1},
    "חסה": {"cal": 15.0, "p": 1.4, "c": 2.9, "f": 0.2},
    "פלפל אדום": {"cal": 31.0, "p": 1.0, "c": 6.0, "f": 0.3},
    "פלפל ירוק / צהוב": {"cal": 27.0, "p": 1.0, "c": 5.3, "f": 0.2},
    "גזר": {"cal": 41.0, "p": 0.9, "c": 9.6, "f": 0.2},
    "בצל": {"cal": 40.0, "p": 1.1, "c": 9.3, "f": 0.1},
    "קישוא": {"cal": 17.0, "p": 1.2, "c": 3.1, "f": 0.3},
    "חציל אפוי": {"cal": 35.0, "p": 0.8, "c": 8.7, "f": 0.2},
    "כרוב": {"cal": 25.0, "p": 1.3, "c": 5.8, "f": 0.1},
    "אפונה ירוקה": {"cal": 81.0, "p": 5.4, "c": 14.5, "f": 0.4},
    "תירס מבושל": {"cal": 96.0, "p": 3.4, "c": 21.0, "f": 1.5},
    "פטריות": {"cal": 22.0, "p": 3.1, "c": 3.3, "f": 0.3},
    "סלק מבושל": {"cal": 44.0, "p": 1.7, "c": 9.6, "f": 0.2},
    "בננה": {"cal": 89.0, "p": 1.1, "c": 22.8, "f": 0.3},
    "תפוח": {"cal": 52.0, "p": 0.3, "c": 13.8, "f": 0.2},
    "תפוז": {"cal": 47.0, "p": 0.9, "c": 11.8, "f": 0.1},
    "אגס": {"cal": 57.0, "p": 0.4, "c": 15.2, "f": 0.1},
    "ענבים": {"cal": 69.0, "p": 0.7, "c": 18.1, "f": 0.2},
    "אבטיח": {"cal": 30.0, "p": 0.6, "c": 7.6, "f": 0.1},
    "מלון": {"cal": 34.0, "p": 0.8, "c": 8.2, "f": 0.2},
    "תות שדה": {"cal": 32.0, "p": 0.7, "c": 7.7, "f": 0.3},
    "תמר (יבש)": {"cal": 282.0, "p": 2.5, "c": 75.0, "f": 0.4},
    "שמן זית": {"cal": 884.0, "p": 0.0, "c": 0.0, "f": 100.0},
    "חמאה": {"cal": 717.0, "p": 0.9, "c": 0.1, "f": 81.0},
    "אבוקדו": {"cal": 160.0, "p": 2.0, "c": 8.5, "f": 14.7},
    "אגוזי מלך": {"cal": 654.0, "p": 15.2, "c": 13.7, "f": 65.2},
    "שקדים": {"cal": 579.0, "p": 21.1, "c": 21.6, "f": 49.9},

    # --- 🍔 ג'אנק פוד, צ'יט מייל ומסעדות ---
    "פיצה (משולש סטנדרטי)": {"cal": 270.0, "p": 12.0, "c": 30.0, "f": 11.0},
    "פיצה משפחתית (מגש שלם - ממוצע)": {"cal": 2200.0, "p": 90.0, "c": 240.0, "f": 95.0},
    "המבורגר במסעדה (כולל לחמנייה ורוטב - יחידה)": {"cal": 650.0, "p": 35.0, "c": 45.0, "f": 36.0},
    "המבורגר רשתות (כגון מקדונלד'ס / ברגר קינג - בינוני)": {"cal": 500.0, "p": 25.0, "c": 40.0, "f": 26.0},
    "צ'יפס מטוגן (מנה בינונית)": {"cal": 365.0, "p": 4.0, "c": 48.0, "f": 17.0},
    "שווארמה בלאפה (כולל טחינה וסלטים)": {"cal": 950.0, "p": 45.0, "c": 85.0, "f": 48.0},
    "שווארמה בפיתה (כולל טחינה וסלטים)": {"cal": 750.0, "p": 38.0, "c": 65.0, "f": 35.0},
    "מנת פלאפל בפיתה (עם חומוס וצ'יפס)": {"cal": 620.0, "p": 22.0, "c": 78.0, "f": 25.0},
    "סושי - רול מטוגן (רול / 8 יחידות)": {"cal": 420.0, "p": 10.0, "c": 55.0, "f": 18.0},
    "סושי - רול דג סלמון / טונה בהרכבה (רול / 8 יחידות)": {"cal": 310.0, "p": 14.0, "c": 45.0, "f": 8.0},
    "סושי - רול צמחוני (מלפפון / אבוקדו / בטטה)": {"cal": 250.0, "p": 5.0, "c": 50.0, "f": 4.0},
    "בורקס גבינה / תפוח אדמה (יחידה גדולה מהמאפייה)": {"cal": 450.0, "p": 8.0, "c": 45.0, "f": 26.0},
    "גלידה (כדור אחד במסעדה / גלידריה)": {"cal": 220.0, "p": 4.0, "c": 26.0, "f": 12.0},
    "חטיף שוקולד סטנדרטי (כגון טוויקס / פפס / סניקרס)": {"cal": 250.0, "p": 4.0, "c": 30.0, "f": 13.0},
    "בורגר צ'יקן / שניצל בלחמנייה (פאסט פוד)": {"cal": 550.0, "p": 28.0, "c": 50.0, "f": 24.0},
    "כנפי עוף מטוגנות ברוטב ברביקיו / צ'ילי (6 יחידות)": {"cal": 480.0, "p": 26.0, "c": 15.0, "f": 35.0},
}

# --- פונקציות עזר גלובליות לחישוב יחידות חכמות ---
def get_unit_options(item_name):
    if not item_name or item_name == "-- ללא --":
        return ["גרם", "יחידות", "כפות"], 0
        
    if "פיצה" in item_name and "מגש" not in item_name:
        return ["יחידות (משולשים)", "גרם"], 0
    if "המבורגר" in item_name or "שווארמה" in item_name or "פלאפל" in item_name or "בורקס" in item_name or "חטיף שוקולד" in item_name or "גלידה" in item_name:
        return ["יחידות", "גרם"], 0
    if "סושי" in item_name:
        return ["רולים / יחידות", "גרם"], 0
    if "צ'יפס" in item_name or "כנפי עוף" in item_name:
        return ["מנה", "גרם"], 0

    if any(k in item_name for k in ["מיונז", "קטשופ", "סרירצ'ה", "צ'ילי", "שום", "אלף האיים", "חרדל", "ויניגרט", "סויה", "טריאקי"]):
        return ["כפות", "גרם"], 0

    if any(k in item_name for k in ["טוסט", "פרוסת", "פיתה", "לחם", "ביצה", "חביתה", "בננה", "תפוח", "תפוז", "אגס", "עגבנייה", "מלפפון", "גבינה צהובה"]):
        return ["יחידות", "גרם"], 0
        
    if any(k in item_name for k in ["משקה חלבון", "תנובה", "יטבתה", "שטראוס", "מילקי"]):
        return ["בקבוק", "גרם"], 0
        
    if "אבקת חלבון" in item_name:
        return ["סקופ", "גרם"], 0
        
    if any(k in item_name for k in ["אורז", "פסטה", "קוסקוס", "בורגול", "קינואה", "כוסמת", "שיבולת שועל", "טחינה מוכנה"]):
        return ["כפות", "גרם", "כפיות"], 0
        
    if "סלט" in item_name:
        return ["קערה / מנה", "גרם", "כפות"], 0
        
    if any(k in item_name for k in ["טונה", "קוטג'", "גבינה", "יוגורט", "חלב"]):
        return ["גרם", "כפות", "אריזה / יחידה"], 0
        
    if any(k in item_name for k in ["חזה עוף", "שניצל", "סלמון", "סטייק", "פרגיות", "בקר", "דניס", "מושט", "בקלה", "שרימפס"]):
        return ["גרם", "יחידות"], 0
        
    return ["גרם", "כפות", "יחידות"], 0

def calc_grams(item_name, unit, raw_amount):
    if not item_name or item_name == "-- ללא --": return raw_amount
    if unit == "כפות": return raw_amount * 15.0
    elif unit == "כפיות": return raw_amount * 5.0
    elif unit == "קערה / מנה" or unit == "מנה": return raw_amount * 200.0
    elif unit == "בקבוק": return raw_amount * 250.0 
    elif unit == "סקופ": return raw_amount * 30.0
    elif unit in ["יחידות", "אריזה / יחידה", "יחידות (משולשים)", "רולים / יחידות"]:
        if "פיצה (משולש" in item_name: return raw_amount * 100.0
        elif "המבורגר" in item_name: return raw_amount * 250.0
        elif "שווארמה" in item_name: return raw_amount * 350.0
        elif "פלאפל" in item_name: return raw_amount * 250.0
        elif "סושי" in item_name: return raw_amount * 200.0
        elif "בורקס" in item_name: return raw_amount * 150.0
        elif "גלידה" in item_name: return raw_amount * 80.0
        elif "חטיף שוקולד" in item_name: return raw_amount * 50.0
        elif "חביתה (משתי ביצים" in item_name: return raw_amount * 120.0
        elif "חביתה (משלוש ביצים" in item_name: return raw_amount * 180.0
        elif "חביתת ירק" in item_name: return raw_amount * 130.0
        elif "ביצה קשה" in item_name or "ביצה שלמה" in item_name or "ביצת עין" in item_name: return raw_amount * 50.0
        elif "טוסט" in item_name: return raw_amount * 100.0  
        elif "גבינה צהובה" in item_name: return raw_amount * 25.0  
        elif "פרוסת לחם" in item_name: return raw_amount * 35.0
        elif "פיתה" in item_name: return raw_amount * 100.0
        elif any(k in item_name for k in ["בננה", "תפוח", "תפוז", "אגס"]): return raw_amount * 120.0
        elif "עגבנייה" in item_name or "מלפפון" in item_name: return raw_amount * 100.0
        elif "טונה" in item_name: return raw_amount * 112.0
        elif "קוטג'" in item_name or "גבינה" in item_name: return raw_amount * 250.0
        elif any(k in item_name for k in ["חזה עוף", "שניצל", "סלמון", "סטייק", "פרגיות"]): return raw_amount * 150.0
        elif any(k in item_name for k in ["דניס", "מושט", "בקלה"]): return raw_amount * 200.0
        else: return raw_amount * 100.0
    return raw_amount

def fetch_nutrition_data(query):
    query_clean = query.strip()
    if query_clean in LOCAL_DATABASE:
        data = LOCAL_DATABASE[query_clean]
        return {"name": query_clean, "cal": data["cal"], "p": data["p"], "c": data["c"], "f": data["f"]}
    try:
        encoded_query = urllib.parse.quote(query_clean)
        url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={encoded_query}&search_simple=1&action=process&json=1"
        headers = {'User-Agent': 'NutritionApp - Streamlit - Version 1.0'}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            products = data.get("products", [])
            for p in products:
                nutriments = p.get("nutriments", {})
                cal = nutriments.get("energy-kcal_100g", nutriments.get("energy-kcal_value", 0))
                protein = nutriments.get("proteins_100g", nutriments.get("proteins_value", 0))
                carbs = nutriments.get("carbohydrates_100g", nutriments.get("carbohydrates_value", 0))
                fat = nutriments.get("fat_100g", nutriments.get("fat_value", 0))
                if cal or protein or carbs or fat:
                    name = p.get("product_name_he", p.get("product_name", query_clean))
                    return {"name": name, "cal": float(cal or 0), "p": float(protein or 0), "c": float(carbs or 0), "f": float(fat or 0)}
    except Exception:
        pass
    return None

# --- Persistent Auth Logic ---
if "user" not in st.session_state:
    st.session_state["user"] = None

current_session = supabase.auth.get_session()
if current_session and current_session.user:
    st.session_state["user"] = current_session.user

def login_user(email, password, remember_me=True):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state["user"] = res.user
        st.success("התחברת בהצלחה!")
        st.rerun()
    except Exception as e:
        st.error(f"שגיאה בהתחברות: {e}")

def signup_user(email, password):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            st.success("ההרשמה בוצעה בהצלחה! כעת תוכל להתחבר.")
    except Exception as e:
        st.error(f"שגיאה בהרשמה: {e}")

def logout_user():
    supabase.auth.sign_out()
    st.session_state["user"] = None
    st.rerun()

# --- Auth UI ---
if not st.session_state["user"]:
    st.title(t["login_title"])
    auth_tab1, auth_tab2 = st.tabs([t["login_tab"], t["signup_tab"]])
    
    with auth_tab1:
        with st.form("login_form"):
            email = st.text_input(t["email"], key="login_email")
            password = st.text_input(t["password"], type="password", key="login_pass")
            remember_me = st.checkbox(t["remember_me"], value=True)
            submit_login = st.form_submit_button(t["login_btn"])
            
            if submit_login:
                if email and password:
                    login_user(email.strip(), password, remember_me)
                else:
                    st.error("נא להזין אימייל וסיסמה")
    with auth_tab2:
        with st.form("signup_form"):
            reg_email = st.text_input(t["signup_email"], key="reg_email")
            reg_password = st.text_input(t["signup_pass"], type="password", key="reg_pass")
            submit_signup = st.form_submit_button(t["signup_btn"])
            
            if submit_signup:
                if reg_email and reg_password:
                    signup_user(reg_email.strip(), reg_password)
                else:
                    st.error("נא להזין אימייל וסיסמה תקינים")
            
    st.stop()

# --- Main App (Logged In) ---
user_id = st.session_state["user"].id

profile_res = supabase.table("user_profiles").select("*").eq("user_id", user_id).execute()
profile_data = profile_res.data[0] if profile_res.data else None

# --- ONBOARDING FORM ---
if not profile_data:
    st.title(t["welcome"])
    st.write(t["welcome_sub"])
    
    with st.form("onboarding_form"):
        gender = st.radio(t["gender"], [t["male"], t["female"]])
        age = st.number_input(t["age"], min_value=12, max_value=120, value=30)
        height = st.number_input(t["height"], min_value=100.0, max_value=230.0, value=175.0)
        weight = st.number_input(t["weight"], min_value=30.0, max_value=250.0, value=75.0)
        activity_str = st.selectbox(t["activity_level"], ["יושבנית (ללא אימונים)", "קל (1-2 אימונים בשבוע)", "בינוני (3-4 אימונים בשבוע)", "גבוהה (5+ אימונים בשבוע)"])
        goal_str = st.selectbox(t["goal"], ["חיטוב / ירידה במשקל", "שמירה על המשקל", "מסה / עליה במסת שריר"])
        submit_profile = st.form_submit_button(t["calc_goals"])
        
        if submit_profile:
            act_map = {"יושבנית (ללא אימונים)": 1.2, "קל (1-2 אימונים בשבוע)": 1.375, "בינוני (3-4 אימונים בשבוע)": 1.55, "גבוהה (5+ אימונים בשבוע)": 1.725}
            act_val = act_map[activity_str]
            gender_val = "גבר" if gender == t["male"] else "אישה"
            supabase.table("user_profiles").insert({"user_id": user_id, "gender": gender_val, "age": int(age), "height": float(height), "weight": float(weight), "activity_level": act_val, "goal": goal_str}).execute()
            
            bmr = (10 * weight) + (6.25 * height) - (5 * age) + (5 if gender_val == "גבר" else -161)
            tdee = bmr * act_val
            
            if goal_str == "חיטוב / ירידה במשקל":
                target_cal, target_p = tdee - 500, weight * 2.0
            elif goal_str == "מסה / עליה במסת שריר":
                target_cal, target_p = tdee + 300, weight * 2.0
            else:
                target_cal, target_p = tdee, weight * 1.8
                
            target_f = weight * 0.9
            target_c = (target_cal - (target_p * 4) - (target_f * 9)) / 4
            
            today_str = date.today().strftime("%Y-%m-%d")
            supabase.table("daily_goals").upsert({"user_id": user_id, "date": today_str, "target_calories": round(target_cal), "target_protein": round(target_p), "target_carbs": round(target_c), "target_fat": round(target_f)}).execute()
            st.rerun()
    st.stop()

# Existing User Layout
st.sidebar.write(f"{t['connected_as']} **{st.session_state['user'].email}**")
if st.sidebar.button(t["logout"]):
    logout_user()

st.title(t["app_title"])

st.sidebar.header(t["date_header"])
selected_date = st.sidebar.date_input("בחר תאריך", date.today()).strftime("%Y-%m-%d")

goals_res = supabase.table("daily_goals").select("*").eq("user_id", user_id).eq("date", selected_date).execute()
user_goals = goals_res.data[0] if goals_res.data else {"target_calories": 2200, "target_protein": 170, "target_carbs": 220, "target_fat": 60}

# יצירת הלשוניות
tab_log, tab_auto_add, tab_workouts, tab_history, tab_camera, tab_ai, tab_settings = st.tabs([t["tab_log"], t["tab_search"], t["tab_workouts"], t["tab_history"], t["tab_camera"], t["tab_ai"], t["tab_settings"]])

with tab_auto_add:
    st.subheader("🔍 חיפוש והוספת מאכל או ארוחה שלמה (כולל ג'אנק פוד, פיצה, המבורגרים וצ'יט מייל)")
    
    add_mode = st.radio("בחר אופן הוספה:", ["מאכל בודד", "🍽️ הוספת ארוחה שלמה בבת אחת"])
    
    food_options = ["-- בחר מאכל מהרשימה (הקלד לסינון) --"] + sorted(list(LOCAL_DATABASE.keys()))
    meal_type_sel = st.selectbox(t["meal_type"], [t["breakfast"], t["lunch"], t["dinner"], t["snack"]])

    if add_mode == "מאכל בודד":
        selected_from_db = st.selectbox(t["search_food"], options=food_options, key="food_selectbox_autocomplete")
        custom_search = st.text_input("או הקלד כל מוצר אחר שתרצה מהסופר או ממסעדה:", key="custom_food_input")
        
        active_search_name = custom_search.strip() if custom_search.strip() else (selected_from_db if selected_from_db != "-- בחר מאכל מהרשימה (הקלד לסינון) --" else "")
        
        u_opts, def_idx = get_unit_options(active_search_name)

        col_u1, col_u2 = st.columns(2)
        with col_u1:
            chosen_unit = st.selectbox(t["unit_type"], u_opts, index=def_idx, key="food_unit_selection")
        with col_u2:
            default_val = 1.0 if chosen_unit in ["בקבוק", "סקופ", "יחידות", "כפות", "קערה / מנה", "כפיות", "אריזה / יחידה", "יחידות (משולשים)", "רולים / יחידות", "מנה"] else 100.0
            raw_amount = st.number_input(t["amount_val"], min_value=0.1, value=default_val, step=1.0 if chosen_unit != "גרם" else 10.0, key=f"food_amount_input_{chosen_unit}")

        amount_input = calc_grams(active_search_name, chosen_unit, raw_amount)

        if st.button(t["add_btn"]):
            search_q = active_search_name
            if search_q:
                data = fetch_nutrition_data(search_q)
                if data:
                    item_name = data["name"]
                    existing = supabase.table("food_items").select("*").eq("user_id", user_id).eq("name", item_name).execute()
                    food_id = existing.data[0]["id"] if existing.data else supabase.table("food_items").insert({"user_id": user_id, "name": item_name, "calories_per_100g": data["cal"], "protein_per_100g": data["p"], "carbs_per_100g": data["c"], "fat_per_100g": data["f"]}).execute().data[0]["id"]

                    supabase.table("food_log").insert({"user_id": user_id, "date": selected_date, "food_id": food_id, "amount_grams": amount_input, "meal_type": meal_type_sel}).execute()
                    st.success(f"✅ הצלחה! המאכל '{item_name}' ({raw_amount} {chosen_unit}) התווסף בהצלחה לארוחת {meal_type_sel}.")
                else:
                    st.error("לא נמצאו נתונים תזונתיים עבור מאכל זה במאגר.")
            else:
                st.warning("נא לבחור מאכל מהרשימה או להקליד חיפוש חופשי.")

    else:
        st.info("בחר עד 4 מרכיבים שונים כדי להרכיב ארוחה שלמה ולהוסיף הכל בלחיצה אחת:")
        
        def render_meal_item(idx):
            item_sel = st.selectbox(f"רכיב {idx}", options=["-- ללא --"] + sorted(list(LOCAL_DATABASE.keys())), key=f"meal_item_{idx}")
            u_opts, def_idx = get_unit_options(item_sel)
            c1, c2 = st.columns(2)
            unit_sel = c1.selectbox(f"סוג ({idx})", u_opts, index=def_idx, key=f"meal_unit_{idx}", label_visibility="collapsed")
            
            d_val = 1.0 if unit_sel in ["בקבוק", "סקופ", "יחידות", "כפות", "קערה / מנה", "כפיות", "אריזה / יחידה", "יחידות (משולשים)", "רולים / יחידות", "מנה"] else 100.0
            
            amt_val = c2.number_input(f"כמות ({idx})", min_value=0.1, value=d_val, step=1.0 if unit_sel != "גרם" else 10.0, key=f"meal_amt_{idx}_{unit_sel}", label_visibility="collapsed")
            return item_sel, unit_sel, amt_val
            
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            i1, u1, a1 = render_meal_item(1)
            st.markdown("<br>", unsafe_allow_html=True)
            i2, u2, a2 = render_meal_item(2)
        with col_m2:
            i3, u3, a3 = render_meal_item(3)
            st.markdown("<br>", unsafe_allow_html=True)
            i4, u4, a4 = render_meal_item(4)
            
        if st.button("🚀 הוסף את כל הארוחה ליומן"):
            selected_items = [
                (i1, calc_grams(i1, u1, a1)),
                (i2, calc_grams(i2, u2, a2)),
                (i3, calc_grams(i3, u3, a3)),
                (i4, calc_grams(i4, u4, a4))
            ]
            
            added_count = 0
            for item_name_sel, final_amt in selected_items:
                if item_name_sel != "-- ללא --":
                    data = fetch_nutrition_data(item_name_sel)
                    if data:
                        item_name = data["name"]
                        existing = supabase.table("food_items").select("*").eq("user_id", user_id).eq("name", item_name).execute()
                        food_id = existing.data[0]["id"] if existing.data else supabase.table("food_items").insert({"user_id": user_id, "name": item_name, "calories_per_100g": data["cal"], "protein_per_100g": data["p"], "carbs_per_100g": data["c"], "fat_per_100g": data["f"]}).execute().data[0]["id"]

                        supabase.table("food_log").insert({"user_id": user_id, "date": selected_date, "food_id": food_id, "amount_grams": final_amt, "meal_type": meal_type_sel}).execute()
                        added_count += 1
                        
            if added_count > 0:
                st.success(f"✅ הצלחה! הארוחה המלאה הכוללת {added_count} רכיבים התוספה בהצלחה לארוחת {meal_type_sel}!")
                for k in list(st.session_state.keys()):
                    if "meal_item_" in k:
                        st.session_state[k] = "-- ללא --"
                st.rerun()
            else:
                st.warning("נא לבחור לפחות מאכל אחד להוספה.")

with tab_workouts:
    st.subheader(t["workouts_header"])
    
    w_type = st.selectbox(t["workout_type"], ["פאדל (Padel)", "חדר כושר / משקולות", "ריצה / אירובי", "כדורגל / ספורט קבוצתי", "אופניים", "שחייה", "אחר"])
    w_duration = st.number_input(t["workout_duration"], min_value=5, max_value=300, value=60, step=5)
    
    if "משקולות" in w_type:
        burn_rate_active = 6.3
    elif "פאדל" in w_type:
        burn_rate_active = 8.5
    elif "ריצה" in w_type:
        burn_rate_active = 11.2
    elif "כדורגל" in w_type:
        burn_rate_active = 10.0
    elif "אופניים" in w_type:
        burn_rate_active = 8.8
    elif "שחייה" in w_type:
        burn_rate_active = 9.5
    else:
        burn_rate_active = 7.5

    calc_active = int(w_duration * burn_rate_active)
    calc_total = int(calc_active * 1.35)

    c_inp1, c_inp2 = st.columns(2)
    with c_inp1:
        st.markdown(f"""
        <div class="ios-widget" style="min-height: 90px; margin-bottom: 0px;">
            <h4>🔥 קלוריות פעילות</h4>
            <h2 style="font-size: 1.4em !important;">{calc_active}</h2>
        </div>
        """, unsafe_allow_html=True)
    with c_inp2:
        st.markdown(f"""
        <div class="ios-widget" style="min-height: 90px; margin-bottom: 0px;">
            <h4>⚡ סה''כ קלוריות (טוטאל)</h4>
            <h2 style="font-size: 1.4em !important;">{calc_total}</h2>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button(t["add_workout_btn"], use_container_width=True):
        try:
            supabase.table("workouts").insert({
                "user_id": user_id,
                "date": selected_date,
                "workout_type": w_type,
                "duration_minutes": int(w_duration),
                "calories_burned": int(calc_active),
                "total_calories": int(calc_total)
            }).execute()
            st.success("האימון נוסף בהצלחה!")
            st.rerun()
        except Exception as e:
            try:
                supabase.table("workouts").insert({
                    "user_id": user_id,
                    "date": selected_date,
                    "workout_type": w_type,
                    "duration_minutes": int(w_duration),
                    "calories_burned": int(calc_active)
                }).execute()
                st.success("האימון נוסף בהצלחה!")
                st.rerun()
            except Exception as ex:
                st.error(f"שגיאה בהוספת האימון: {ex}")

    st.divider()
    st.subheader("📋 אימונים מתועדים לתאריך הנבחר")
    workouts_res = supabase.table("workouts").select("*").eq("user_id", user_id).eq("date", selected_date).execute()
    workout_entries = workouts_res.data
    
    if workout_entries:
        total_workout_cals = sum(w.get("calories_burned", 0) for w in workout_entries)
        st.info(f"סה''כ קלוריות פעילות שנשרפו באימונים היום: **{total_workout_cals} קלוריות** 🔥")
        
        for w in workout_entries:
            tot_cals_val = w.get('total_calories', w['calories_burned'] + int(w['duration_minutes'] * 2.2))
            c_type, c_dur, c_cals, c_del = st.columns([3, 2, 2, 1])
            c_type.write(f"🏋️ {w['workout_type']}")
            c_dur.write(f"⏱️ {w['duration_minutes']} דקות")
            c_cals.write(f"🔥 פעילות: {w['calories_burned']} | טוטאל: {tot_cals_val}")
            if c_del.button("🗑️", key=f"del_w_{w['id']}"):
                supabase.table("workouts").delete().eq("id", w["id"]).execute()
                st.rerun()
    else:
        st.info("אין אימונים מתועדים לתאריך זה.")

# --- מסך היסטוריה ויומן חדש ---
with tab_history:
    st.subheader("📅 יומן היסטוריה ובדיקת עמידה ביעדים לפי תאריך")
    history_date = st.date_input("בחר תאריך לבדיקה:", date.today(), key="history_calendar_picker")
    history_date_str = history_date.strftime("%Y-%m-%d")

    st.markdown(f"### סיכום עבור תאריך: **{history_date_str}**")

    hist_log_res = supabase.table("food_log").select("*, food_items(*)").eq("user_id", user_id).eq("date", history_date_str).execute()
    hist_entries = hist_log_res.data

    h_cal = sum(e["food_items"]["calories_per_100g"] * e["amount_grams"] / 100.0 for e in hist_entries)
    h_p = sum(e["food_items"]["protein_per_100g"] * e["amount_grams"] / 100.0 for e in hist_entries)
    h_c = sum(e["food_items"]["carbs_per_100g"] * e["amount_grams"] / 100.0 for e in hist_entries)
    h_f = sum(e["food_items"]["fat_per_100g"] * e["amount_grams"] / 100.0 for e in hist_entries)

    hist_workouts_res = supabase.table("workouts").select("*").eq("user_id", user_id).eq("date", history_date_str).execute()
    hist_workouts = hist_workouts_res.data
    h_burned = sum(w.get("calories_burned", 0) for w in hist_workouts) if hist_workouts else 0

    hist_goals_res = supabase.table("daily_goals").select("*").eq("user_id", user_id).eq("date", history_date_str).execute()
    h_goals = hist_goals_res.data[0] if hist_goals_res.data else user_goals

    hc1, hc2, hc3, hc4 = st.columns(4)
    with hc1:
        st.markdown(f"""
        <div class="ios-widget">
            <h4>🔥 קלוריות שאכלת</h4>
            <h2>{round(h_cal, 1)}</h2>
            <p>יעד: {h_goals['target_calories']} | אימונים: -{h_burned}</p>
        </div>
        """, unsafe_allow_html=True)
    with hc2:
        st.markdown(f"""
        <div class="ios-widget">
            <h4>🥩 חלבון</h4>
            <h2>{round(h_p, 1)}g</h2>
            <p>יעד: {h_goals['target_protein']}g</p>
        </div>
        """, unsafe_allow_html=True)
    with hc3:
        st.markdown(f"""
        <div class="ios-widget">
            <h4>🍞 פחמימות</h4>
            <h2>{round(h_c, 1)}g</h2>
            <p>יעד: {h_goals['target_carbs']}g</p>
        </div>
        """, unsafe_allow_html=True)
    with hc4:
        st.markdown(f"""
        <div class="ios-widget">
            <h4>🥑 שומנים</h4>
            <h2>{round(h_f, 1)}g</h2>
            <p>יעד: {h_goals['target_fat']}g</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.subheader("🏋️ סטטוס אימונים בתאריך זה:")
    if hist_workouts:
        st.success(f"✅ התאמנת ב-{history_date_str}! בוצעו {len(hist_workouts)} אימונים.")
        
        w_cols = st.columns(len(hist_workouts))
        for idx, hw in enumerate(hist_workouts):
            tot_val = hw.get('total_calories', hw['calories_burned'] + int(hw['duration_minutes'] * 2.2))
            with w_cols[idx]:
                st.markdown(f"""
                <div class="ios-widget">
                    <h4>🏋️ {hw['workout_type']}</h4>
                    <h2>{hw['calories_burned']} פעילות</h2>
                    <p>טוטאל: {tot_val} | {hw['duration_minutes']} דק'</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ לא דווחו אימונים בתאריך {history_date_str}.")

    st.divider()

    st.subheader("🎯 סטטוס עמידה ביעדי תזונה:")
    cal_diff = h_cal - h_goals['target_calories']
    if abs(cal_diff) <= 150:
        st.info(f"🎯 הצלחה מעולה! היית קרוב מאוד ליעד הקלורי (הפרש של {round(cal_diff)} קלוריות).")
    elif cal_diff > 150:
        st.warning(f"⚠️ חריגה מהיעד הקלורי בכ-{round(cal_diff)} קלוריות.")
    else:
        st.info(f"💡 היית מתחת ליעד הקלורי בכ-{round(abs(cal_diff))} קלוריות.")

with tab_camera:
    st.subheader("📸 סריקת תמונה")
    uploaded_file = st.file_uploader("בחר תמונה", type=["jpg", "jpeg", "png"])
    meal_type_img = st.selectbox(t["meal_type"], [t["breakfast"], t["lunch"], t["dinner"], t["snack"]], key="img_meal")

    if uploaded_file is not None:
        st.image(uploaded_file, width=300)
        if st.button("זהה רכיבים והוסף ליומן"):
            est_name = "ארוחה מצולמת (משוערת)"
            existing = supabase.table("food_items").select("*").eq("user_id", user_id).eq("name", est_name).execute()
            food_id = existing.data[0]["id"] if existing.data else supabase.table("food_items").insert({"user_id": user_id, "name": est_name, "calories_per_100g": 450.0, "protein_per_100g": 30.0, "carbs_per_100g": 45.0, "fat_per_100g": 15.0}).execute().data[0]["id"]
            supabase.table("food_log").insert({"user_id": user_id, "date": selected_date, "food_id": food_id, "amount_grams": 100.0, "meal_type": meal_type_img}).execute()
            st.success("הארוחה נוספה!")
            st.rerun()

# --- מסך יומן אכילה ראשי ---
with tab_log:
    st.subheader(f"תיעוד ארוחות לתאריך: {selected_date}")
    log_res = supabase.table("food_log").select("*, food_items(*)").eq("user_id", user_id).eq("date", selected_date).execute()
    entries = log_res.data
    
    consumed_cal = sum(e["food_items"]["calories_per_100g"] * e["amount_grams"] / 100.0 for e in entries)
    consumed_p = sum(e["food_items"]["protein_per_100g"] * e["amount_grams"] / 100.0 for e in entries)
    consumed_c = sum(e["food_items"]["carbs_per_100g"] * e["amount_grams"] / 100.0 for e in entries)
    consumed_f = sum(e["food_items"]["fat_per_100g"] * e["amount_grams"] / 100.0 for e in entries)

    workouts_res_summary = supabase.table("workouts").select("*").eq("user_id", user_id).eq("date", selected_date).execute()
    total_burned_cals = sum(w.get("calories_burned", 0) for w in workouts_res_summary.data) if workouts_res_summary.data else 0

    st.divider()
    st.subheader(t["daily_summary"])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="ios-widget">
            <h4>🔥 קלוריות</h4>
            <h2>{round(consumed_cal, 1)}</h2>
            <p>יעד: {user_goals['target_calories']} | אימונים: -{total_burned_cals}</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="ios-widget">
            <h4>🥩 חלבון</h4>
            <h2>{round(consumed_p, 1)}g</h2>
            <p>יעד: {user_goals['target_protein']}g</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="ios-widget">
            <h4>🍞 פחמימות</h4>
            <h2>{round(consumed_c, 1)}g</h2>
            <p>יעד: {user_goals['target_carbs']}g</p>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="ios-widget">
            <h4>🥑 שומנים</h4>
            <h2>{round(consumed_f, 1)}g</h2>
            <p>יעד: {user_goals['target_fat']}g</p>
        </div>
        """, unsafe_allow_html=True)

    if workouts_res_summary.data:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        w_log_cols = st.columns(len(workouts_res_summary.data))
        for idx, w_item in enumerate(workouts_res_summary.data):
            tot_val = w_item.get('total_calories', w_item['calories_burned'] + int(w_item['duration_minutes'] * 2.2))
            with w_log_cols[idx]:
                st.markdown(f"""
                <div class="ios-widget">
                    <h4>🏋️ {w_item['workout_type']}</h4>
                    <h2>{w_item['calories_burned']} פעילות</h2>
                    <p>טוטאל: {tot_val} | {w_item['duration_minutes']} דק'</p>
                </div>
                """, unsafe_allow_html=True)

    st.divider()
    
    if entries:
        meals_map = {
            t["breakfast"]: [],
            t["lunch"]: [],
            t["dinner"]: [],
            t["snack"]: []
        }
        
        for e in entries:
            m_type = e.get("meal_type", t["breakfast"])
            if m_type in meals_map:
                meals_map[m_type].append(e)
            else:
                if t["breakfast"] in meals_map:
                    meals_map[t["breakfast"]].append(e)

        for meal_name, meal_items in meals_map.items():
            meal_cals = sum(item["food_items"]["calories_per_100g"] * item["amount_grams"] / 100.0 for item in meal_items)
            meal_p = sum(item["food_items"]["protein_per_100g"] * item["amount_grams"] / 100.0 for item in meal_items)
            meal_c = sum(item["food_items"]["carbs_per_100g"] * item["amount_grams"] / 100.0 for item in meal_items)
            meal_f = sum(item["food_items"]["fat_per_100g"] * item["amount_grams"] / 100.0 for item in meal_items)

            expander_title = f"🍽️ **{meal_name}** &nbsp;&nbsp;|&nbsp;&nbsp; 🔥 {round(meal_cals, 1)} קל' | 🥩 {round(meal_p, 1)}g חלבון | 🍞 {round(meal_c, 1)}g פח' | 🥑 {round(meal_f, 1)}g שומן"

            with st.expander(expander_title):
                if meal_items:
                    mc1, mc2, mc3, mc4 = st.columns(4)
                    with mc1:
                        st.markdown(f"""
                        <div class="meal-summary-widget">
                            <span style="font-size: 0.8em; opacity: 0.8;">🔥 קלוריות</span>
                            <div style="font-size: 1.2em; font-weight: bold;">{round(meal_cals, 1)}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with mc2:
                        st.markdown(f"""
                        <div class="meal-summary-widget">
                            <span style="font-size: 0.8em; opacity: 0.8;">🥩 חלבון</span>
                            <div style="font-size: 1.2em; font-weight: bold;">{round(meal_p, 1)}g</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with mc3:
                        st.markdown(f"""
                        <div class="meal-summary-widget">
                            <span style="font-size: 0.8em; opacity: 0.8;">🍞 פחמימות</span>
                            <div style="font-size: 1.2em; font-weight: bold;">{round(meal_c, 1)}g</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with mc4:
                        st.markdown(f"""
                        <div class="meal-summary-widget">
                            <span style="font-size: 0.8em; opacity: 0.8;">🥑 שומן</span>
                            <div style="font-size: 1.2em; font-weight: bold;">{round(meal_f, 1)}g</div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

                    for e in meal_items:
                        food_item = e["food_items"]
                        amt = e["amount_grams"]
                        
                        item_cal = food_item['calories_per_100g'] * amt / 100.0
                        item_p = food_item['protein_per_100g'] * amt / 100.0
                        item_c = food_item['carbs_per_100g'] * amt / 100.0
                        item_f = food_item['fat_per_100g'] * amt / 100.0

                        if amt == 250.0 and ("משקה חלבון" in food_item['name'] or "תנובה" in food_item['name'] or "יטבתה" in food_item['name'] or "שטראוס" in food_item['name']):
                            display_amt = "1 בקבוק (250 מ\"ל)"
                        elif amt == 112.0 and "טונה" in food_item['name']:
                            display_amt = "1 קופסת טונה"
                        elif "חביתה" in food_item['name']:
                            if amt == 120.0: display_amt = "1 חביתה (2 ביצים)"
                            elif amt == 180.0: display_amt = "1 חביתה (3 ביצים)"
                            elif amt == 130.0: display_amt = "1 חביתת ירק"
                            elif amt % 120.0 == 0: display_amt = f"{int(amt / 120.0)} חביתיות"
                            else: display_amt = f"{amt} גרם"
                        elif "ביצה" in food_item['name'] or "ביצת עין" in food_item['name']:
                            if amt == 50.0: display_amt = "1 ביצה"
                            elif amt % 50.0 == 0: display_amt = f"{int(amt / 50.0)} ביצים"
                            else: display_amt = f"{amt} גרם"
                        elif any(k in food_item['name'] for k in ["מיונז", "קטשופ", "סרירצ'ה", "צ'ילי", "שום", "אלף האיים", "חרדל", "ויניגרט", "סויה", "טריאקי", "טחינה מוכנה"]) and amt % 15.0 == 0:
                            display_amt = f"{int(amt / 15.0)} כפות"
                        elif "גבינה צהובה" in food_item['name']:
                            if amt == 25.0: display_amt = "1 פרוסה"
                            elif amt % 25.0 == 0: display_amt = f"{int(amt / 25.0)} פרוסות"
                            else: display_amt = f"{amt} גרם"
                        elif "טוסט" in food_item['name']:
                            if amt == 100.0: display_amt = "1 טוסט"
                            elif amt % 100.0 == 0: display_amt = f"{int(amt / 100.0)} טוסטים"
                            else: display_amt = f"{amt} גרם"
                        elif "פרוסת לחם" in food_item['name']:
                            if amt == 35.0: display_amt = "1 פרוסה"
                            elif amt % 35.0 == 0: display_amt = f"{int(amt / 35.0)} פרוסות"
                            else: display_amt = f"{amt} גרם"
                        elif any(k in food_item['name'] for k in ["חזה עוף", "שניצל", "סלמון", "סטייק", "פרגיות"]) and amt % 150.0 == 0:
                            display_amt = f"{int(amt / 150.0)} יחידות"
                        elif amt % 15.0 == 0 and amt <= 150.0:
                            display_amt = f"{int(amt / 15.0)} כפות"
                        else:
                            display_amt = f"{amt} גרם"

                        edit_key_state = f"editing_{e['id']}"
                        if edit_key_state not in st.session_state:
                            st.session_state[edit_key_state] = False

                        c_food, c_amt, c_edit, c_del = st.columns([3, 2, 1, 1])
                        c_food.markdown(f"**• {food_item['name']}**<br><span style='font-size: 0.85em; opacity: 0.8;'>🔥 {round(item_cal, 1)} קל | 🥩 חלבון: {round(item_p, 1)}g | 🍞 פחמימות: {round(item_c, 1)}g | 🥑 שומן: {round(item_f, 1)}g</span>", unsafe_allow_html=True)
                        c_amt.write(display_amt)
                        
                        if c_edit.button("✏️", key=f"edit_btn_{e['id']}"):
                            st.session_state[edit_key_state] = not st.session_state[edit_key_state]
                            st.rerun()
                            
                        if c_del.button("🗑️", key=f"del_exp_{e['id']}"):
                            supabase.table("food_log").delete().eq("id", e["id"]).execute()
                            if edit_key_state in st.session_state:
                                del st.session_state[edit_key_state]
                            st.rerun()

                        if st.session_state[edit_key_state]:
                            with st.form(key=f"form_edit_{e['id']}"):
                                new_amt = st.number_input("עדכן כמות חדשה (בגרמים):", min_value=1.0, value=float(e['amount_grams']), step=10.0)
                                
                                available_meals = [t["breakfast"], t["lunch"], t["dinner"], t["snack"]]
                                current_meal_idx = available_meals.index(e.get("meal_type", t["breakfast"])) if e.get("meal_type") in available_meals else 0
                                new_meal_type = st.selectbox("שייך לארוחה:", available_meals, index=current_meal_idx)

                                submitted_edit = st.form_submit_button("שמור שינוי")
                                if submitted_edit:
                                    supabase.table("food_log").update({
                                        "amount_grams": new_amt,
                                        "meal_type": new_meal_type
                                    }).eq("id", e['id']).execute()
                                    st.session_state[edit_key_state] = False
                                    st.success("הפרטים עודכנו בהצלחה!")
                                    st.rerun()
                        st.divider()
                else:
                    st.info("אין מאכלים בארוחה זו.")
    else:
        st.info("No logs for today.")

with tab_ai:
    st.subheader("🤖 AI Advisor")
    user_query = st.text_area("Ask anything:")
    if st.button("Send"):
        st.markdown("### 💡 AI Response\nKeep up the great work and maintain high protein intake!")

with tab_settings:
    st.subheader(t["settings_header"])
    with st.form("settings_form"):
        s_age = st.number_input(t["age"], min_value=12, max_value=120, value=int(profile_data.get("age", 30)))
        s_height = st.number_input(t["height"], min_value=100.0, max_value=230.0, value=float(profile_data.get("height", 175.0)))
        s_weight = st.number_input(t["weight"], min_value=30.0, max_value=250.0, value=float(profile_data.get("weight", 75.0)))
        
        theme_choice = st.selectbox(t["theme_label"], t["theme_options"], index=t["theme_options"].index(st.session_state["theme_mode"]) if st.session_state["theme_mode"] in t["theme_options"] else 0)
        
        submit_settings = st.form_submit_button(t["save_settings"])
        
        if submit_settings:
            st.session_state["theme_mode"] = theme_choice
            supabase.table("user_profiles").update({
                "age": int(s_age), "height": float(s_height), "weight": float(s_weight)
            }).eq("user_id", user_id).execute()
            st.success("Updated successfully!")
            st.rerun()

    st.divider()
    st.markdown(t["account_update"])
    with st.form("account_update_form"):
        new_email = st.text_input(t["new_email"], value=st.session_state["user"].email)
        new_password = st.text_input(t["new_password"], type="password")
        submit_account = st.form_submit_button(t["update_account"])
        
        if submit_account:
            update_attrs = {}
            if new_email and new_email != st.session_state["user"].email:
                update_attrs["email"] = new_email.strip()
            if new_password:
                if len(new_password) >= 6:
                    update_attrs["password"] = new_password
                else:
                    st.error("Password must be at least 6 characters.")
            
            if update_attrs:
                try:
                    supabase.auth.update_user(update_attrs)
                    st.success("Account updated successfully!")
                except Exception as e:
                    st.error(f"Error updating account: {e}")
            else:
                st.info("No changes made.")
