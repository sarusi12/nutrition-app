import streamlit as st
import requests
import urllib.parse
from datetime import date, datetime
from supabase import create_client, Client

# --- Streamlit Page Config ---
st.set_page_config(page_title="NutriFlow / מחשבון תזונה", layout="wide", initial_sidebar_state="expanded")

# --- Language Dictionaries (i18n) ---
TRANSLATIONS = {
    "עברית (Hebrew)": {
        "app_title": "🥗 מחשבון תזונה, אימונים ויומן אישי",
        "login_title": "🔐 התחברות למערכת התזונה",
        "email": "אימייל",
        "password": "סיסמה",
        "remember_me": "זכור אותי",
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
        "daily_summary": "📊 סיכום יומי",
        "calories": "קלוריות",
        "protein": "חלבון",
        "carbs": "פחמימות",
        "fat": "שומן",
        "workouts_header": "🏋️ תיעוד אימון חדש",
        "workout_type": "סוג האימון",
        "workout_duration": "משך האימון (בדקות)",
        "calories_burned": "קלוריות שנשרפו (הערכה)",
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

# --- Clean CSS Styling ---
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}
    
    .ios-widget {{
        background: {widget_bg};
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid {widget_border};
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
        margin-bottom: 10px;
        text-align: center;
        min-height: 140px;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: {widget_bg};
        padding: 6px;
        border-radius: 16px;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 12px;
        padding: 10px 16px;
        color: {text_color};
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

# --- מאגר מובנה ענק ומקיף ---
LOCAL_DATABASE = {
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
    "ביצה": {"cal": 155.0, "p": 12.6, "c": 1.1, "f": 10.6},
    "חלבון ביצה (לבן)": {"cal": 52.0, "p": 10.9, "c": 0.7, "f": 0.2},
    "קוטג' 5%": {"cal": 95.0, "p": 11.0, "c": 1.5, "f": 5.0},
    "קוטג' 3%": {"cal": 80.0, "p": 11.0, "c": 1.5, "f": 3.0},
    "גבינה לבנה 5%": {"cal": 100.0, "p": 10.0, "c": 3.5, "f": 5.0},
    "גבינה צהובה 28%": {"cal": 350.0, "p": 25.0, "c": 1.0, "f": 28.0},
    "גבינה צהובה 9%": {"cal": 170.0, "p": 30.0, "c": 1.0, "f": 9.0},
    "יוגורט 3%": {"cal": 60.0, "p": 4.0, "c": 4.5, "f": 3.0},
    "יוגורט טבעי 0%": {"cal": 40.0, "p": 5.0, "c": 5.0, "f": 0.2},
    "יוגורט חלבון 20g": {"cal": 70.0, "p": 10.0, "c": 4.0, "f": 0.4},
    "חלב 3%": {"cal": 60.0, "p": 3.3, "c": 4.7, "f": 3.0},
    "חלב 1%": {"cal": 42.0, "p": 3.4, "c": 4.8, "f": 1.0},
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
    "פיתה": {"cal": 275.0, "p": 8.5, "c": 55.0, "f": 1.2},
    "אורז בסמטי מבושל": {"cal": 130.0, "p": 2.8, "c": 28.0, "f": 0.2},
    "קוסקוס מבושל": {"cal": 112.0, "p": 3.8, "c": 23.2, "f": 0.2},
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
    "טחינה גולמית": {"cal": 595.0, "p": 17.0, "c": 21.0, "f": 53.8},
    "אגוזי מלך": {"cal": 654.0, "p": 15.2, "c": 13.7, "f": 65.2},
    "שקדים": {"cal": 579.0, "p": 21.1, "c": 21.6, "f": 49.9},
    "חמאת בוטנים": {"cal": 588.0, "p": 25.0, "c": 20.0, "f": 50.0},
}

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

# --- Auth Logic ---
if "user" not in st.session_state:
    st.session_state["user"] = None

def login_user(email, password, remember_me=False):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state["user"] = res.user
        if remember_me:
            st.session_state["remember_user"] = res.user.id
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
    if "remember_user" in st.session_state:
        del st.session_state["remember_user"]
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
tab_log, tab_auto_add, tab_workouts, tab_camera, tab_ai, tab_settings = st.tabs([t["tab_log"], t["tab_search"], t["tab_workouts"], t["tab_camera"], t["tab_ai"], t["tab_settings"]])

with tab_auto_add:
    st.subheader("🔍 חיפוש והוספת מאכל")
    st.caption("הקלד אותיות בתיבת הבחירה למטה כדי לסנן אוטומטית מתוך מאגר המאכלים הענק שלנו:")
    
    food_options = ["-- בחר מאכל מהרשימה (הקלד לסינון) --"] + sorted(list(LOCAL_DATABASE.keys()))
    selected_from_db = st.selectbox(t["search_food"], options=food_options, key="food_selectbox_autocomplete")
    
    custom_search = st.text_input("או הקלד שם מאכל אחר לחיפוש חופשי (אם לא נמצא ברשימה):", key="custom_food_input")
    
    # זיהוי סוג המאכל כדי להתאים את יחידות המידה בצורה חכמה
    active_search_name = custom_search.strip() if custom_search.strip() else (selected_from_db if selected_from_db != "-- בחר מאכל מהרשימה (הקלד לסינון) --" else "")
    
    # התאמת יחידות לפי סוג המזון
    if any(k in active_search_name for k in ["אורז", "פסטה", "קוסקוס", "בורגול", "קינואה", "כוסמת", "שיבולת שועל"]):
        unit_options = ["גרם", "כפות", "כפיות"]
    elif any(k in active_search_name for k in ["טונה", "קוטג'", "גבינה", "יוגורט", "חלב"]):
        unit_options = ["גרם", "כפות", "קופסה / יחידה"]
    elif any(k in active_search_name for k in ["עגבנייה", "מלפפון", "בננה", "תפוח", "תפוז", "אגס", "ביצה", "פיתה", "לחם"]):
        unit_options = ["גרם", "יחידות"]
    else:
        unit_options = ["גרם", "כפות", "יחידות"]

    col_u1, col_u2 = st.columns(2)
    with col_u1:
        chosen_unit = st.selectbox(t["unit_type"], unit_options, key="food_unit_selection")
    with col_u2:
        raw_amount = st.number_input(t["amount_val"], min_value=0.1, value=100.0 if chosen_unit == "גרם" else 1.0, step=1.0 if chosen_unit != "גרם" else 10.0)

    # המרת הכמות לגרמים לצורך חישוב תזונתי מדויק מאחורי הקלעים
    if chosen_unit == "כפות":
        amount_input = raw_amount * 15.0  # כף סטנדרטית מכילה כ-15 גרם
    elif chosen_unit == "כפיות":
        amount_input = raw_amount * 5.0   # כפית סטנדרטית מכילה כ-5 גרם
    elif chosen_unit == "קופסה / יחידה":
        if "טונה" in active_search_name:
            amount_input = raw_amount * 112.0 # קופסת טונה סטנדרטית מסוננת
        elif "קוטג'" in active_search_name or "גבינה" in active_search_name:
            amount_input = raw_amount * 250.0 # גביע קוטג' / גבינה סטנדרטי
        else:
            amount_input = raw_amount * 100.0
    elif chosen_unit == "יחידות":
        if "ביצה" in active_search_name:
            amount_input = raw_amount * 50.0  # ביצה ממוצעת שוקלת כ-50 גרם
        elif any(k in active_search_name for k in ["בננה", "תפוח", "תפוז", "אגס"]):
            amount_input = raw_amount * 120.0 # פרי ממוצע שוקל כ-120 גרם
        elif "עגבנייה" in active_search_name or "מלפפון" in active_search_name:
            amount_input = raw_amount * 100.0 # ירק בינוני שוקל כ-100 גרם
        else:
            amount_input = raw_amount * 100.0
    else:
        amount_input = raw_amount # גרמים רגילים

    meal_type_sel = st.selectbox(t["meal_type"], [t["breakfast"], t["lunch"], t["dinner"], t["snack"]])

    if st.button(t["add_btn"]):
        search_q = active_search_name
        if search_q:
            data = fetch_nutrition_data(search_q)
            if data:
                item_name = data["name"]
                existing = supabase.table("food_items").select("*").eq("user_id", user_id).eq("name", item_name).execute()
                food_id = existing.data[0]["id"] if existing.data else supabase.table("food_items").insert({"user_id": user_id, "name": item_name, "calories_per_100g": data["cal"], "protein_per_100g": data["p"], "carbs_per_100g": data["c"], "fat_per_100g": data["f"]}).execute().data[0]["id"]

                supabase.table("food_log").insert({"user_id": user_id, "date": selected_date, "food_id": food_id, "amount_grams": amount_input, "meal_type": meal_type_sel}).execute()
                st.success(f"המאכל '{item_name}' ({raw_amount} {chosen_unit}) התווסף בהצלחה!")
                st.rerun()
            else:
                st.error("לא נמצאו נתונים תזונתיים עבור מאכל זה.")
        else:
            st.warning("נא לבחור מאכל מהרשימה או להקליד חיפוש חופשי.")

with tab_workouts:
    st.subheader(t["workouts_header"])
    
    with st.form("workout_form"):
        w_type = st.selectbox(t["workout_type"], ["פאדל (Padel)", "חדר כושר / משקולות", "ריצה / אירובי", "כדורגל / ספורט קבוצתי", "אופניים", "שחייה", "אחר"])
        w_duration = st.number_input(t["workout_duration"], min_value=5, max_value=300, value=60, step=5)
        
        base_burn_rate = 8.0
        if "משקולות" in w_type: base_burn_rate = 6.0
        elif "ריצה" in w_type: base_burn_rate = 11.0
        elif "פאדל" in w_type: base_burn_rate = 9.0
        elif "אופניים" in w_type: base_burn_rate = 8.5
        elif "שחייה" in w_type: base_burn_rate = 10.0
        
        default_calc_cals = int(w_duration * base_burn_rate)
        w_calories = st.number_input(t["calories_burned"], min_value=10, max_value=3000, value=default_calc_cals, step=10)
        
        submit_workout = st.form_submit_button(t["add_workout_btn"])
        
        if submit_workout:
            try:
                supabase.table("workouts").insert({
                    "user_id": user_id,
                    "date": selected_date,
                    "workout_type": w_type,
                    "duration_minutes": int(w_duration),
                    "calories_burned": int(w_calories)
                }).execute()
                st.success("האימון נוסף בהצלחה!")
                st.rerun()
            except Exception as e:
                st.error(f"שגיאה בהוספת האימון: {e}")

    st.divider()
    st.subheader("📋 אימונים מתועדים לתאריך הנבחר")
    workouts_res = supabase.table("workouts").select("*").eq("user_id", user_id).eq("date", selected_date).execute()
    workout_entries = workouts_res.data
    
    if workout_entries:
        total_workout_cals = sum(w["calories_burned"] for w in workout_entries)
        st.info(f"סה''כ קלוריות שנשרפו באימונים היום: **{total_workout_cals} קלוריות** 🔥")
        
        for w in workout_entries:
            c_type, c_dur, c_cals, c_del = st.columns([3, 2, 2, 1])
            c_type.write(f"🏋️ {w['workout_type']}")
            c_dur.write(f"⏱️ {w['duration_minutes']} דקות")
            c_cals.write(f"🔥 {w['calories_burned']} קלוריות")
            if c_del.button("🗑️", key=f"del_w_{w['id']}"):
                supabase.table("workouts").delete().eq("id", w["id"]).execute()
                st.rerun()
    else:
        st.info("אין אימונים מתועדים לתאריך זה.")

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

    workouts_res_summary = supabase.table("workouts").select("calories_burned").eq("user_id", user_id).eq("date", selected_date).execute()
    total_burned_cals = sum(w["calories_burned"] for w in workouts_res_summary.data) if workouts_res_summary.data else 0

    st.divider()
    st.subheader(t["daily_summary"])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="ios-widget">
            <h4 style="margin: 0 0 10px 0;">🔥 קלוריות</h4>
            <h2 style="margin: 0 0 10px 0; font-size: 1.8em;">{round(consumed_cal, 1)}</h2>
            <p style="margin: 0; font-size: 0.85em; opacity: 0.8;">יעד: {user_goals['target_calories']} | אימונים: -{total_burned_cals}</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="ios-widget">
            <h4 style="margin: 0 0 10px 0;">🥩 חלבון</h4>
            <h2 style="margin: 0 0 10px 0; font-size: 1.8em;">{round(consumed_p, 1)}g</h2>
            <p style="margin: 0; font-size: 0.85em; opacity: 0.8;">יעד: {user_goals['target_protein']}g</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="ios-widget">
            <h4 style="margin: 0 0 10px 0;">🍞 פחמימות</h4>
            <h2 style="margin: 0 0 10px 0; font-size: 1.8em;">{round(consumed_c, 1)}g</h2>
            <p style="margin: 0; font-size: 0.85em; opacity: 0.8;">יעד: {user_goals['target_carbs']}g</p>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="ios-widget">
            <h4 style="margin: 0 0 10px 0;">🥑 שומנים</h4>
            <h2 style="margin: 0 0 10px 0; font-size: 1.8em;">{round(consumed_f, 1)}g</h2>
            <p style="margin: 0; font-size: 0.85em; opacity: 0.8;">יעד: {user_goals['target_fat']}g</p>
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
            with st.expander(f"🍽️ {meal_name} (קלוריות: {round(meal_cals, 1)}) — לחץ לפתיחה"):
                if meal_items:
                    for e in meal_items:
                        food_item = e["food_items"]
                        c_food, c_amt, c_del = st.columns([4, 2, 1])
                        c_food.write(f"• {food_item['name']}")
                        c_amt.write(f"{e['amount_grams']} גרם")
                        if c_del.button("🗑️", key=f"del_exp_{e['id']}"):
                            supabase.table("food_log").delete().eq("id", e["id"]).execute()
                            st.rerun()
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
