import streamlit as st
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

# --- Authentication Logic ---
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
        email = st.text_input("אימייל", key="login_email")
        password = st.text_input("סיסמה", type="password", key="login_pass")
        if st.button("התחבר"):
            login_user(email, password)
            
    with auth_tab2:
        reg_email = st.text_input("אימייל להרשמה", key="reg_email")
        reg_password = st.text_input("סיסמה (לפחות 6 תווים)", type="password", key="reg_pass")
        if st.button("ירשם כעת"):
            signup_user(reg_email, reg_password)
            
    st.stop()

# --- Main App (Logged In) ---
user_id = st.session_state["user"].id

st.sidebar.write(f"👤 מחובר כ: **{st.session_state['user'].email}**")
if st.sidebar.button("התנתק"):
    logout_user()

st.title("🥗 מחשבון תזונה ויומן אכילה אישי")

st.sidebar.header("📅 תאריך ויעדים")
selected_date = st.sidebar.date_input("בחר תאריך", date.today()).strftime("%Y-%m-%d")

# Fetch goals from Supabase
goals_res = supabase.table("daily_goals").select("*").eq("user_id", user_id).eq("date", selected_date).execute()
user_goals = goals_res.data[0] if goals_res.data else {"target_calories": 2200, "target_protein": 170, "target_carbs": 220, "target_fat": 60}

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

tab_log, tab_add_food = st.tabs(["📝 יומן אכילה", "➕ הוספת מאכל למאגר"])

with tab_add_food:
    st.subheader("הוספת מאכל חדש למאגר האישי שלך (ל-100 גרם)")
    with st.form("add_food_form"):
        food_name = st.text_input("שם המאכל")
        col_a, col_b = st.columns(2)
        with col_a:
            cal = st.number_input("קלוריות ל-100ג", min_value=0.0, step=1.0)
            p = st.number_input("חלבון ל-100ג", min_value=0.0, step=0.1)
        with col_b:
            c = st.number_input("פחמימות ל-100ג", min_value=0.0, step=0.1)
            f = st.number_input("שומן ל-100ג", min_value=0.0, step=0.1)
            
        submitted = st.form_submit_button("שמור מאכל")
        if submitted and food_name:
            supabase.table("food_items").insert({
                "user_id": user_id,
                "name": food_name,
                "calories_per_100g": cal,
                "protein_per_100g": p,
                "carbs_per_100g": c,
                "fat_per_100g": f
            }).execute()
            st.success(f"המאכל '{food_name}' נשמר בהצלחה!")

with tab_log:
    st.subheader(f"תיעוד ארוחות לתאריך: {selected_date}")
    
    foods_res = supabase.table("food_items").select("*").eq("user_id", user_id).order("name").execute()
    foods = foods_res.data
    
    if not foods:
        st.warning("אין עדיין מאכלים במאגר שלך. עבור ללשונית 'הוספת מאכל' כדי להתחיל!")
    else:
        food_dict = {f["name"]: f for f in foods}
        
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        with col1:
            selected_food_name = st.selectbox("בחר מאכל", list(food_dict.keys()))
        with col2:
            amount_g = st.number_input("כמות בגרמים", min_value=1.0, value=100.0, step=10.0)
        with col3:
            meal_type = st.selectbox("ארוחה", ["בוקר", "צהריים", "ערב", "נשנוש / אימון"])
        with col4:
            st.write("")
            st.write("")
            if st.button("הוסף ליומן"):
                food_obj = food_dict[selected_food_name]
                supabase.table("food_log").insert({
                    "user_id": user_id,
                    "date": selected_date,
                    "food_id": food_obj["id"],
                    "amount_grams": amount_g,
                    "meal_type": meal_type
                }).execute()
                st.rerun()

    # Get log entries
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

    if entries:
        st.subheader("📋 פירוט ארוחות שנרשמו")
        display_data = [{
            "מאכל": e["food_items"]["name"],
            "כמות (גרם)": e["amount_grams"],
            "ארוחה": e["meal_type"],
            "קלוריות": round(e["food_items"]["calories_per_100g"] * e["amount_grams"] / 100.0, 1),
            "חלבון": round(e["food_items"]["protein_per_100g"] * e["amount_grams"] / 100.0, 1)
        } for e in entries]
        st.table(display_data)
