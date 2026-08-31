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

# --- מאגר מובנה מהיר בעברית למאכלי בסיס ---
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
    
    # 1. בדיקה במאגר המקומי המהיר
    if query_clean in LOCAL_DATABASE:
        data = LOCAL_DATABASE[query_clean]
        return {
            "name": query_clean,
            "cal": data["cal"],
            "p": data["p"],
            "c": data["c"],
            "f": data["f"]
        }
        
    # 2. חיפוש ברשת במידה ולא נמצא במאגר המקומי
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
                    return {
                        "name": name,
                        "cal": float(cal or 0),
                        "p": float(protein or 0),
                        "c": float(carbs or 0),
                        "f": float(fat or 0)
                    }
    except Exception:
        pass
    return None

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

# Fetch goals
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

tab_log, tab_auto_add = st.tabs(["📝 יומן אכילה", "🔍 חיפוש והוספה מהירה"])

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
                st.error("לא נמאסו נתונים תזונתיים. נסה לחפש מאכל מתוך הרשימה הבסיסית או באנגלית (Chicken breast).")

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
        
        # כותרת הטבלה
        cols = st.columns([3, 2, 2, 2, 2, 1])
        cols[0].markdown("**מאכל**")
        cols[1].markdown("**ארוחה**")
        cols[2].markdown("**כמות (גרם)**")
        cols[3].markdown("**קלוריות**")
        cols[4].markdown("**חלבון (ג')**")
        cols[5].markdown("**פעולה**")
        
        for e in entries:
            food_item = e["food_items"]
            cal_item = round(food_item["calories_per_100g"] * e["amount_grams"] / 100.0, 1)
            prot_item = round(food_item["protein_per_100g"] * e["amount_grams"] / 100.0, 1)
            
            c_food, c_meal, c_amt, c_cal, c_p, c_del = st.columns([3, 2, 2, 2, 2, 1])
            c_food.write(food_item["name"])
            c_meal.write(e["meal_type"])
            c_amt.write(f"{e['amount_grams']} ג'")
            c_cal.write(f"{cal_item}")
            c_p.write(f"{prot_item}")
            
            # לחצן מחיקה
            if c_del.button("🗑️", key=f"del_{e['id']}"):
                supabase.table("food_log").delete().eq("id", e["id"]).execute()
                st.success(f"נמחק: {food_item['name']}")
                st.rerun()
    else:
        st.info("עדיין לא נרשמו ארוחות ליום זה.")
