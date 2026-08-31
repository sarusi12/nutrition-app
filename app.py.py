import streamlit as st
import requests
import urllib.parse
from datetime import date
from supabase import create_client, Client

# --- Supabase Initialization ---
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

st.set_page_config(page_title="מחשבון תזונה ויומן אכילה", layout="wide")

# --- מאגר מובנה מהיר בעברית ---
LOCAL_DATABASE = {
    "חזה עוף": {"cal": 165.0, "p": 31.0, "c": 0.0, "f": 3.6},
    "חזה עוף מבושל": {"cal": 165.0, "p": 31.0, "c": 0.0, "f": 3.6},
    "אורז לבן מבושל": {"cal": 130.0, "p": 2.7, "c": 28.0, "f": 0.3},
    "אורז מלא מבושל": {"cal": 111.0, "p": 2.6, "c": 23.0, "f": 0.9},
    "בננה": {"cal": 89.0, "p": 1.1, "c": 22.8, "f": 0.3},
    "טונה במים": {"cal": 116.0, "p": 26.0, "c": 0.0, "f": 1.0},
    "טונה בשמן": {"cal": 198.0, "p": 29.0, "c": 0.0, "f": 8.2},
    "ביצה": {"cal": 155.0, "p": 12.6, "c": 1.1, "f": 10.6},
    "שיבולת שועל": {"cal": 389.0, "p": 16.9, "c": 66.3, "f": 6.9},
    "קוטג' 5%": {"cal": 95.0, "p": 11.0, "c": 1.5, "f": 5.0},
    "תפוח אדמה מבושל": {"cal": 87.0, "p": 1.9, "c": 20.1, "f": 0.1},
    "בשר בקר טחון 5%": {"cal": 137.0, "p": 21.4, "c": 0.0, "f": 5.0},
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

def login_user(email, password):
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
    st.title("🔐 התחברות למערכת התזונה")
    auth_tab1, auth_tab2 = st.tabs(["התחברות", "הרשמה"])
    
    with auth_tab1:
        with st.form("login_form"):
            email = st.text_input("אימייל", key="login_email")
            password = st.text_input("סיסמה", type="password", key="login_pass")
            submit_login = st.form_submit_button("התחבר")
            
            if submit_login:
                if email and password:
                    login_user(email.strip(), password)
                else:
                    st.error("נא להזין אימייל וסיסמה")
            
    with auth_tab2:
        with st.form("signup_form"):
            reg_email = st.text_input("אימייל להרשמה", key="reg_email")
            reg_password = st.text_input("סיסמה (לפחות 6 תווים)", type="password", key="reg_pass")
            submit_signup = st.form_submit_button("ירשם כעת")
            
            if submit_signup:
                if reg_email and reg_password:
                    signup_user(reg_email.strip(), reg_password)
                else:
                    st.error("נא להזין אימייל וסיסמה תקינים")
            
    st.stop()

# --- Main App (Logged In) ---
user_id = st.session_state["user"].id

# Check profile
profile_res = supabase.table("user_profiles").select("*").eq("user_id", user_id).execute()
profile_data = profile_res.data[0] if profile_res.data else None

# --- ONBOARDING FORM ---
if not profile_data:
    st.title("👋 ברוך הבא! בוא נגדיר את הפרופיל שלך")
    st.write("הכנס את הנתונים שלך כדי שנחשב עבורך את היעדים היומיים המדויקים:")
    
    with st.form("onboarding_form"):
        gender = st.radio("מין", ["גבר", "אישה"])
        age = st.number_input("גיל", min_value=12, max_value=120, value=30)
        height = st.number_input("גובה (בס\"מ)", min_value=100.0, max_value=230.0, value=175.0)
        weight = st.number_input("משקל (בק\"ג)", min_value=30.0, max_value=250.0, value=75.0)
        
        activity_str = st.selectbox("רמת פעילות גופנית", [
            "יושבנית (ללא אימונים)",
            "קל (1-2 אימונים בשבוע)",
            "בינוני (3-4 אימונים בשבוע)",
            "גבוהה (5+ אימונים בשבוע)"
        ])
        
        goal_str = st.selectbox("מה המטרה שלך?", [
            "חיטוב / ירידה במשקל",
            "שמירה על המשקל",
            "מסה / עליה במסת שריר"
        ])
        
        submit_profile = st.form_submit_button("חשב יעדים ושמור")
        
        if submit_profile:
            act_map = {
                "יושבנית (ללא אימונים)": 1.2,
                "קל (1-2 אימונים בשבוע)": 1.375,
                "בינוני (3-4 אימונים בשבוע)": 1.55,
                "גבוהה (5+ אימונים בשבוע)": 1.725
            }
            act_val = act_map[activity_str]
            
            supabase.table("user_profiles").insert({
                "user_id": user_id,
                "gender": gender,
                "age": int(age),
                "height": float(height),
                "weight": float(weight),
                "activity_level": act_val,
                "goal": goal_str
            }).execute()
            
            # BMR Calculation (Mifflin-St Jeor)
            bmr = (10 * weight) + (6.25 * height) - (5 * age) + (5 if gender == "גבר" else -161)
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
            supabase.table("daily_goals").upsert({
                "user_id": user_id,
                "date": today_str,
                "target_calories": round(target_cal),
                "target_protein": round(target_p),
                "target_carbs": round(target_c),
                "target_fat": round(target_f)
            }).execute()
            
            st.success("הפרופיל והיעדים הוגדרו בהצלחה!")
            st.rerun()
    st.stop()

# --- APP FOR EXISTING USER ---
st.sidebar.write(f"👤 מחובר כ: **{st.session_state['user'].email}**")
if st.sidebar.button("התנתק"):
    logout_user()

st.title("🥗 מחשבון תזונה ויומן אכילה אישי")

st.sidebar.header("📅 תאריך ויעדים")
selected_date = st.sidebar.date_input("בחר תאריך", date.today()).strftime("%Y-%m-%d")

goals_res = supabase.table("daily_goals").select("*").eq("user_id", user_id).eq("date", selected_date).execute()
user_goals = goals_res.data[0] if goals_res.data else {
    "target_calories": 2200, "target_protein": 170, "target_carbs": 220, "target_fat": 60
}

with st.sidebar.expander("הגדר/עדכן יעדים ליום זה"):
    target_cal = st.number_input("יעד קלוריות", value=float(user_goals["target_calories"]), step=50.0)
    target_p = st.number_input("יעד חלבון (ג')", value=float(user_goals["target_protein"]), step=5.0)
    target_c = st.number_input("יעד פחמימות (ג')", value=float(user_goals["target_carbs"]), step=5.0)
    target_f = st.number_input("יעד שומן (ג')", value=float(user_goals["target_fat"]), step=5.0)
    if st.button("שמור יעדים"):
        supabase.table("daily_goals").upsert({
            "user_id": user_id,
            "date": selected_date,
            "target_calories": target_cal,
            "target_protein": target_p,
            "target_carbs": target_c,
            "target_fat": target_f
        }).execute()
        st.success("היעדים נשמרו!")
        st.rerun()

tab_log, tab_auto_add, tab_ai = st.tabs(["📝 יומן אכילה", "🔍 חיפוש והוספה מהירה", "🤖 יועץ תזונה AI"])

with tab_auto_add:
    st.subheader("חפש מאכל (למשל: חזה עוף, אורז לבן מבושל, בננה, טונה במים)")
    search_q = st.text_input("שם המאכל לחיפוש")
    amount_input = st.number_input("כמות בגרמים", min_value=1.0, value=100.0, step=10.0)
    meal_type_sel = st.selectbox("לאיזו ארוחה?", ["בוקר", "צהריים", "ערב", "נשנוש / אימון"])

    if st.button("חפש והוסף ליומן"):
        if search_q:
            data = fetch_nutrition_data(search_q)
            if data:
                item_name = data["name"]
                existing = supabase.table("food_items").select("*").eq("user_id", user_id).eq("name", item_name).execute()
                
                if existing.data:
                    food_id = existing.data[0]["id"]
                else:
                    new_item = supabase.table("food_items").insert({
                        "user_id": user_id,
                        "name": item_name,
                        "calories_per_100g": data["cal"],
                        "protein_per_100g": data["p"],
                        "carbs_per_100g": data["c"],
                        "fat_per_100g": data["f"]
                    }).execute()
                    food_id = new_item.data[0]["id"]

                supabase.table("food_log").insert({
                    "user_id": user_id,
                    "date": selected_date,
                    "food_id": food_id,
                    "amount_grams": amount_input,
                    "meal_type": meal_type_sel
                }).execute()
                st.success(f"התווסף בהצלחה! ({item_name} - {amount_input} גרם)")
                st.rerun()
            else:
                st.error("לא נמאסו נתונים תזונתיים. נסה לחפש מאכל מתוך הרשימה הבסיסית או באנגלית.")

with tab_log:
    st.subheader(f"תיעוד ארוחות לתאריך: {selected_date}")
    log_res = supabase.table("food_log").select("*, food_items(*)").eq("user_id", user_id).eq("date", selected_date).execute()
    entries = log_res.data
    
    consumed_cal = sum(e["food_items"]["calories_per_100g"] * e["amount_grams"] / 100.0 for e in entries)
    consumed_p = sum(e["food_items"]["protein_per_100g"] * e["amount_grams"] / 100.0 for e in entries)
    consumed_c = sum(e["food_items"]["carbs_per_100g"] * e["amount_grams"] / 100.0 for e in entries)
    consumed_f = sum(e["food_items"]["fat_per_100g"] * e["amount_grams"] / 100.0 for e in entries)

    st.divider()
    st.subheader("📊 סיכום יומי")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("קלוריות", f"{round(consumed_cal, 1)} / {user_goals['target_calories']}", f"נותרו {round(user_goals['target_calories'] - consumed_cal, 1)}")
    c2.metric("חלבון", f"{round(consumed_p, 1)}g / {user_goals['target_protein']}g", f"נותרו {round(user_goals['target_protein'] - consumed_p, 1)}g")
    c3.metric("פחמימות", f"{round(consumed_c, 1)}g / {user_goals['target_carbs']}g", f"נותרו {round(user_goals['target_carbs'] - consumed_c, 1)}g")
    c4.metric("שומן", f"{round(consumed_f, 1)}g / {user_goals['target_fat']}g", f"נותרו {round(user_goals['target_fat'] - consumed_f, 1)}g")

    st.divider()
    if entries:
        st.subheader("📋 פירוט ארוחות שנרשמו")
        for e in entries:
            food_item = e["food_items"]
            cal_item = round(food_item["calories_per_100g"] * e["amount_grams"] / 100.0, 1)
            prot_item = round(food_item["protein_per_100g"] * e["amount_grams"] / 100.0, 1)
            
            c_food, c_meal, c_amt, c_cal, c_p, c_del = st.columns([3, 2, 2, 2, 2, 1])
            c_food.write(food_item["name"])
            c_meal.write(e["meal_type"])
            c_amt.write(f"{e['amount_grams']} ג'")
            c_cal.write(f"{cal_item} קל'")
            c_p.write(f"{prot_item} ג' חלבון")
            
            if c_del.button("🗑️", key=f"del_{e['id']}"):
                supabase.table("food_log").delete().eq("id", e["id"]).execute()
                st.rerun()
    else:
        st.info("עדיין לא נרשמו ארוחות ליום זה.")

# --- TAB: AI ADVISOR ---
with tab_ai:
    st.subheader("🤖 עוזר תזונה ואימונים אישי")
    st.write("שאל כל שאלה לגבי תכנון ימי פינוק, חריגות בארוחות, התמודדות עם מסעדות או התאמת תזונה למטרה שלך.")
    
    q_option = st.selectbox("בחר נושא התייעצות מהירה:", [
        "מתי מומלץ לשלב יום פינוק (Cheat Day)?",
        "אכלתי יותר מדי היום, איך לאזן את זה מחר?",
        "יש לי אירוע/חתונה בערב, איך להתכונן?",
        "אחר (הקלד שאלה חופשית)"
    ])
    
    custom_q = ""
    if q_option == "אחר (הקלד שאלה חופשית)":
        custom_q = st.text_area("פרט את השאלה שלך:")
        
    if st.button("שאל את העוזר"):
        prompt = custom_q if q_option == "אחר (הקלד שאלה חופשית)" else q_option
        
        with st.spinner("מעבד תשובה..."):
            if "יום פינוק" in prompt or "Cheat Day" in prompt:
                st.markdown("""
                ### 🍕 הנחיות לשילוב יום פינוק (Refeed / Cheat Meal):
                * **תדירות מומלצת:** פעם בשבועיים (בחיטוב קפדני) או פעם בשבוע (בשמירה על המשקל).
                * **איך לבצע נכון:** עדיף להתמקד ב-**Refeed פחמימות** (העלאת פחמימות תוך שמירה על חלבון ומינימום שומן).
                * **ביום הפינוק:** שמור על יעד החלבון היומי שלך כדי למנוע פירוק שריר.
                * **טיפ זהב:** תזמן את יום הפינוק ביום של אימון כוח קשה – כך הקלוריות יופנו לשיקום השריר.
                """)
            elif "אכלתי יותר מדי" in prompt:
                st.markdown("""
                ### ⚖️ איך לאזן חריגה קלורית:
                1. **אל תרעיב את עצמך מחר!** הרעבה מובילה למעגל סגור של בולמוסים.
                2. **קזז מעט פחמימות ושומן:** ביום-יומיים הבאים קצץ כ-200-300 קלוריות, אך **שמור על החלבון גבוה**.
                3. **שתייה ומים:** שתה 3-4 ליטר מים ביום למחרת כדי לנער נוזלים.
                4. **הוסף צעדים:** הליכה של 20–30 דקות תסייע לשרוף חלק מהעודף.
                """)
            elif "אירוע" in prompt:
                st.markdown("""
                ### 🥂 איך להתכונן לאירוע / מסעדה:
                * **במהלך היום:** תאכל בעיקר חלבון רזה וירקות. תחסוך את רוב הפחמימות והשומן לערב.
                * **באירוע:** התחל עם מנת חלבון (בשר/דג) וירקות.
                * **אל תתעד בלחץ:** תיהנה מהאירוע, ותחזור ליומן הרגיל למחרת בבוקר.
                """)
            else:
                st.markdown(f"""
                ### 💡 המלצת תזונה מותאמת:
                עבור המטרה שלך (**{profile_data.get('goal', 'תזונה מאוזנת')}**):
                * הקפד על פיזור החלבון לאורך 3-4 ארוחות ביום.
                * התאוששות ושינה של 7–8 שעות בלילה קריטיות להתקדמות.
                """)
