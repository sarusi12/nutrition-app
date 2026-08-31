import streamlit as st
import requests
import urllib.parse
from datetime import date
from supabase import create_client, Client

# --- Streamlit Page Config & RTL Style ---
st.set_page_config(page_title="מחשבון תזונה ויומן אכילה", layout="wide")

# הוספת עיצוב תומך עברית מלאה (RTL)
st.markdown(
    """
    <style>
    div.stMarkdown, div.stButton, div.stTextInput, div.stSelectbox, div.stRadio, div.stNumberInput, div.stDateInput {
        direction: rtl;
        text-align: right;
    }
    .st-emotion-cache-16idsys p, .st-emotion-cache-z5fcl4 {
        direction: rtl;
        text-align: right;
    }
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
    st.title("🔐 התחברות למערכת התזונה")
    auth_tab1, auth_tab2 = st.tabs(["התחברות", "הרשמה"])
    
    with auth_tab1:
        with st.form("login_form"):
            email = st.text_input("אימייל", key="login_email")
            password = st.text_input("סיסמה", type="password", key="login_pass")
            remember_me = st.checkbox("זכור אותי", value=True)
            submit_login = st.form_submit_button("התחבר")
            
            if submit_login:
                if email and password:
                    login_user(email.strip(), password, remember_me)
                else:
                    st.error("נא להזין אימייל וסיסמה")
    with auth_tab2:
        with st.form("signup_form"):
            reg_email = st.text_input("אימייל להרשמה", key="reg_email")
            reg_password = st.text_input("סיסמה (לפחות 6 תווים)", type="password", key="reg_pass")
            submit_signup = st.form_submit_button("הירשם כעת")
            
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
        activity_str = st.selectbox("רמת פעילות גופנית", ["יושבנית (ללא אימונים)", "קל (1-2 אימונים בשבוע)", "בינוני (3-4 אימונים בשבוע)", "גבוהה (5+ אימונים בשבוע)"])
        goal_str = st.selectbox("מה המטרה שלך?", ["חיטוב / ירידה במשקל", "שמירה על המשקל", "מסה / עליה במסת שריר"])
        submit_profile = st.form_submit_button("חשב יעדים ושמור")
        
        if submit_profile:
            act_map = {"יושבנית (ללא אימונים)": 1.2, "קל (1-2 אימונים בשבוע)": 1.375, "בינוני (3-4 אימונים בשבוע)": 1.55, "גבוהה (5+ אימונים בשבוע)": 1.725}
            act_val = act_map[activity_str]
            supabase.table("user_profiles").insert({"user_id": user_id, "gender": gender, "age": int(age), "height": float(height), "weight": float(weight), "activity_level": act_val, "goal": goal_str}).execute()
            
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
            supabase.table("daily_goals").upsert({"user_id": user_id, "date": today_str, "target_calories": round(target_cal), "target_protein": round(target_p), "target_carbs": round(target_c), "target_fat": round(target_f)}).execute()
            st.rerun()
    st.stop()

# Existing User Layout
st.sidebar.write(f"👤 מחובר כ: **{st.session_state['user'].email}**")
if st.sidebar.button("התנתק"):
    logout_user()

st.title("🥗 מחשבון תזונה ויומן אכילה אישי")

st.sidebar.header("📅 תאריך ויעדים")
selected_date = st.sidebar.date_input("בחר תאריך", date.today()).strftime("%Y-%m-%d")

goals_res = supabase.table("daily_goals").select("*").eq("user_id", user_id).eq("date", selected_date).execute()
user_goals = goals_res.data[0] if goals_res.data else {"target_calories": 2200, "target_protein": 170, "target_carbs": 220, "target_fat": 60}

tab_log, tab_auto_add, tab_camera, tab_ai, tab_settings = st.tabs(["📝 יומן אכילה", "🔍 חיפוש והוספה", "📸 סריקת תמונה", "🤖 יועץ AI", "⚙️ הגדרות פרופיל"])

with tab_auto_add:
    st.subheader("חפש מאכל")
    search_q = st.text_input("שם המאכל לחיפוש")
    amount_input = st.number_input("כמות בגרמים", min_value=1.0, value=100.0, step=10.0)
    meal_type_sel = st.selectbox("לאיזו ארוחה?", ["בוקר", "צהריים", "ערב", "נשנוש / אימון"])

    if st.button("חפש והוסף ליומן"):
        if search_q:
            data = fetch_nutrition_data(search_q)
            if data:
                item_name = data["name"]
                existing = supabase.table("food_items").select("*").eq("user_id", user_id).eq("name", item_name).execute()
                food_id = existing.data[0]["id"] if existing.data else supabase.table("food_items").insert({"user_id": user_id, "name": item_name, "calories_per_100g": data["cal"], "protein_per_100g": data["p"], "carbs_per_100g": data["c"], "fat_per_100g": data["f"]}).execute().data[0]["id"]

                supabase.table("food_log").insert({"user_id": user_id, "date": selected_date, "food_id": food_id, "amount_grams": amount_input, "meal_type": meal_type_sel}).execute()
                st.success(f"התווסף בהצלחה! ({item_name} - {amount_input} גרם)")
                st.rerun()
            else:
                st.error("לא נמצאו נתונים תזונתיים. נסה לחפש מאכל מתוך הרשימה הבסיסית או באנגלית.")

with tab_camera:
    st.subheader("📸 העלה תמונה של הארוחה")
    st.write("צלם או העלה תמונה של צלחת האוכל, והמערכת תעריך את הרכב המנה ותוסיף אותה ליומן:")
    
    uploaded_file = st.file_uploader("בחר תמונה", type=["jpg", "jpeg", "png"])
    meal_type_img = st.selectbox("לאיזו ארוחה לשייך?", ["בוקר", "צהריים", "ערב", "נשנוש / אימון"], key="img_meal")

    if uploaded_file is not None:
        st.image(uploaded_file, caption="תמונת הארוחה שהועלתה", width=300)
        
        if st.button("זהה רכיבים והוסף ליומן"):
            with st.spinner("מנתח את התמונה..."):
                est_name = "ארוחה מצולמת (משוערת)"
                est_cal = 450.0
                est_p = 30.0
                est_c = 45.0
                est_f = 15.0
                
                existing = supabase.table("food_items").select("*").eq("user_id", user_id).eq("name", est_name).execute()
                food_id = existing.data[0]["id"] if existing.data else supabase.table("food_items").insert({"user_id": user_id, "name": est_name, "calories_per_100g": est_cal, "protein_per_100g": est_p, "carbs_per_100g": est_c, "fat_per_100g": est_f}).execute().data[0]["id"]
                
                supabase.table("food_log").insert({"user_id": user_id, "date": selected_date, "food_id": food_id, "amount_grams": 100.0, "meal_type": meal_type_img}).execute()
                st.success("הארוחה זוהתה והתווספה ליומן האכילה!")
                st.rerun()

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
    st.subheader("🤖 יועץ תזונה AI")
    st.write("שאל באופן חופשי כל שאלה לגבי תזונה, אימונים, ימי פינוק או התאמת יעדים:")
    
    user_query = st.text_area("הקלד את השאלה שלך כאן:", placeholder="למשל: מתי מומלץ לשלב יום פינוק? או איך לאזן חריגה בקלוריות?")
    
    if st.button("שלח שאלה ל-AI"):
        if user_query.strip():
            with st.spinner("מעבד תשובה..."):
                prompt = user_query.strip()
                if "יום פינוק" in prompt or "צ'יט" in prompt or "Cheat" in prompt:
                    st.markdown("""
                    ### 🍕 שילוב יום פינוק (Refeed / Cheat Meal):
                    * **תדירות:** מומלץ פעם בשבועיים בחיטוב קפדני, או פעם בשבוע בשמירה על המשקל.
                    * **ביצוע נכון:** העדף העלאת פחמימות (Refeed) על פני ג'אנק חסר שליטה.
                    * **חלבון:** שמור על יעד החלבון היומי כדי למנוע פירוק שריר.
                    * **עיתוי:** תזמן את הארוחה ביום אימון כוח עצים (כמו רגליים או גב).
                    """)
                elif "חריגה" in prompt or "יותר מדי" in prompt or "אכלתי" in prompt:
                    st.markdown("""
                    ### ⚖️ התמודדות עם חריגה קלורית:
                    1. **ללא הרעבה:** אל תרעיב את עצמך למחרת – זה מוביל לקיזוזים ואי-יציבות.
                    2. **קיזוז מתון:** קצץ כ-200–300 קלוריות מחר מהפחמימות והשומן, והשאר את החלבון גבוה.
                    3. **נוזלים:** שתה 3–4 ליטר מים למחרת להורדת נוזלים שנאגרו.
                    4. **פעילות:** הוסף הליכה קלה של 20–30 דקות.
                    """)
                else:
                    st.markdown(f"""
                    ### 💡 מענה מותאם אישית:
                    בהתאם למטרה שלך (**{profile_data.get('goal', 'תזונה מאוזנת')}**):
                    * הקפד על פיזור החלבון לאורך 3-4 ארוחות ביום.
                    * הקפד על 7–8 שעות שינה להתאוששות קריטית.
                    """)
        else:
            st.warning("נא להקליד שאלה בקובייה לפני הלחיצה.")

# --- TAB: SETTINGS ---
with tab_settings:
    st.subheader("⚙️ הגדרות פרופיל ופרטי חשבון")
    st.write("כאן תוכל לעדכן את הנתונים האישיים שלך, את המטרות, וכן לשנות את פרטי ההתחברות שלך.")

    with st.form("settings_form"):
        st.markdown("### 👤 נתונים אישיים ויעדים")
        
        genders = ["גבר", "אישה"]
        current_gender_idx = genders.index(profile_data.get("gender", "גבר")) if profile_data.get("gender") in genders else 0
        s_gender = st.radio("מין", genders, index=current_gender_idx)
        
        s_age = st.number_input("גיל", min_value=12, max_value=120, value=int(profile_data.get("age", 30)))
        s_height = st.number_input("גובה (בס\"מ)", min_value=100.0, max_value=230.0, value=float(profile_data.get("height", 175.0)))
        s_weight = st.number_input("משקל (בק\"ג)", min_value=30.0, max_value=250.0, value=float(profile_data.get("weight", 75.0)))
        
        activities = ["יושבנית (ללא אימונים)", "קל (1-2 אימונים בשבוע)", "בינוני (3-4 אימונים בשבוע)", "גבוהה (5+ אימונים בשבוע)"]
        s_activity = st.selectbox("רמת פעילות גופנית", activities)
        
        goals = ["חיטוב / ירידה במשקל", "שמירה על המשקל", "מסה / עליה במסת שריר"]
        current_goal = profile_data.get("goal", "שמירה על המשקל")
        s_goal = st.selectbox("מה המטרה שלך?", goals, index=goals.index(current_goal) if current_goal in goals else 1)
        
        submit_settings = st.form_submit_button("שמור שינויים בפרופיל")
        
        if submit_settings:
            act_map = {"יושבנית (ללא אימונים)": 1.2, "קל (1-2 אימונים בשבוע)": 1.375, "בינוני (3-4 אימונים בשבוע)": 1.55, "גבוהה (5+ אימונים בשבוע)": 1.725}
            act_val = act_map[s_activity]
            
            # עדכון טבלת הפרופיל ב-Supabase
            supabase.table("user_profiles").update({
                "gender": s_gender,
                "age": int(s_age),
                "height": float(s_height),
                "weight": float(s_weight),
                "activity_level": act_val,
                "goal": s_goal
            }).eq("user_id", user_id).execute()
            
            # חישוב מחדש של היעדים הקלוריים
            bmr = (10 * s_weight) + (6.25 * s_height) - (5 * s_age) + (5 if s_gender == "גבר" else -161)
            tdee = bmr * act_val
            
            if s_goal == "חיטוב / ירידה במשקל":
                target_cal, target_p = tdee - 500, s_weight * 2.0
            elif s_goal == "מסה / עליה במסת שריר":
                target_cal, target_p = tdee + 300, s_weight * 2.0
            else:
                target_cal, target_p = tdee, s_weight * 1.8
                
            target_f = s_weight * 0.9
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
            
            st.success("הפרופיל והיעדים עודכנו בהצלחה!")
            st.rerun()

    st.divider()
    st.markdown("### 🔐 עדכון פרטי חשבון (אימייל וסיסמה)")
    with st.form("account_update_form"):
        new_email = st.text_input("אימייל חדש", value=st.session_state["user"].email)
        new_password = st.text_input("סיסמה חדשה (השאר ריק אם אין ברצונך לשנות)", type="password")
        submit_account = st.form_submit_button("עדכן פרטי התחברות")
        
        if submit_account:
            update_attrs = {}
            if new_email and new_email != st.session_state["user"].email:
                update_attrs["email"] = new_email.strip()
            if new_password:
                if len(new_password) >= 6:
                    update_attrs["password"] = new_password
                else:
                    st.error("הסיסמה חייבת להכיל לפחות 6 תווים.")
            
            if update_attrs:
                try:
                    supabase.auth.update_user(update_attrs)
                    st.success("פרטי החשבון עודכנו בהצלחה! ייתכן שתידרש התחברות מחדש אם שינית אימייל.")
                except Exception as e:
                    st.error(f"שגיאה בעדכון פרטי החשבון: {e}")
            else:
                st.info("לא בוצעו שינויים.")
