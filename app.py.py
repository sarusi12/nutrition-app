import sqlite3
import streamlit as st
from datetime import date
from typing import List, Tuple

# --- Persistent Data Layer (SQLite Repository) ---
class NutritionRepository:
    def __init__(self, db_path: str = "nutrition_tracker.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS food_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                calories_per_100g REAL NOT NULL,
                protein_per_100g REAL NOT NULL,
                carbs_per_100g REAL NOT NULL,
                fat_per_100g REAL NOT NULL
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_goals (
                date TEXT PRIMARY KEY,
                target_calories REAL NOT NULL,
                target_protein REAL NOT NULL,
                target_carbs REAL NOT NULL,
                target_fat REAL NOT NULL
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS food_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                food_id INTEGER NOT NULL,
                amount_grams REAL NOT NULL,
                meal_type TEXT DEFAULT 'כללי',
                FOREIGN KEY (food_id) REFERENCES food_items (id)
            );
            """)
            conn.commit()

    def add_food_item(self, name: str, cal: float, p: float, c: float, f: float) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO food_items (name, calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g)
            VALUES (?, ?, ?, ?, ?)
            """, (name, cal, p, c, f))
            conn.commit()
            return cursor.lastrowid

    def set_daily_goal(self, log_date: str, calories: float, protein: float, carbs: float, fat: float):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO daily_goals (date, target_calories, target_protein, target_carbs, target_fat)
            VALUES (?, ?, ?, ?, ?)
            """, (log_date, calories, protein, carbs, fat))
            conn.commit()

    def log_meal(self, log_date: str, food_id: int, amount_grams: float, meal_type: str = "כללי"):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO food_log (date, food_id, amount_grams, meal_type)
            VALUES (?, ?, ?, ?)
            """, (log_date, food_id, amount_grams, meal_type))
            conn.commit()

    def get_daily_summary(self, log_date: str) -> dict:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT target_calories, target_protein, target_carbs, target_fat FROM daily_goals WHERE date = ?", (log_date,))
            goal_row = cursor.fetchone()
            targets = {
                "calories": goal_row[0] if goal_row else 2000,
                "protein": goal_row[1] if goal_row else 150,
                "carbs": goal_row[2] if goal_row else 200,
                "fat": goal_row[3] if goal_row else 60
            }

            cursor.execute("""
            SELECT f.name, l.amount_grams, l.meal_type,
                   (f.calories_per_100g * l.amount_grams / 100.0) as cal,
                   (f.protein_per_100g * l.amount_grams / 100.0) as p,
                   (f.carbs_per_100g * l.amount_grams / 100.0) as c,
                   (f.fat_per_100g * l.amount_grams / 100.0) as fat
            FROM food_log l
            JOIN food_items f ON l.food_id = f.id
            WHERE l.date = ?
            ORDER BY l.id ASC
            """, (log_date,))
            
            entries = cursor.fetchall()
            consumed_cal = sum(e[3] for e in entries)
            consumed_p = sum(e[4] for e in entries)
            consumed_c = sum(e[5] for e in entries)
            consumed_f = sum(e[6] for e in entries)

            return {
                "date": log_date,
                "targets": targets,
                "consumed": {
                    "calories": round(consumed_cal, 1),
                    "protein": round(consumed_p, 1),
                    "carbs": round(consumed_c, 1),
                    "fat": round(consumed_f, 1)
                },
                "remaining": {
                    "calories": round(targets["calories"] - consumed_cal, 1),
                    "protein": round(targets["protein"] - consumed_p, 1),
                    "carbs": round(targets["carbs"] - consumed_c, 1),
                    "fat": round(targets["fat"] - consumed_f, 1)
                },
                "entries": [
                    {"מאכל": e[0], "כמות (גרם)": e[1], "ארוחה": e[2], "קלוריות": round(e[3], 1), "חלבון (ג')": round(e[4], 1), "פחמימות (ג')": round(e[5], 1), "שומן (ג')": round(e[6], 1)}
                    for e in entries
                ]
            }

    def get_all_foods(self) -> List[Tuple[int, str]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM food_items ORDER BY name ASC")
            return cursor.fetchall()

# --- Streamlit UI App ---
db = NutritionRepository()

st.set_page_config(page_title="מחשבון תזונה ויומן אכילה", layout="wide")
st.title("🥗 מחשבון תזונה ויומן אכילה יומי")

st.sidebar.header("📅 תאריך ויעדים")
selected_date = st.sidebar.date_input("בחר תאריך", date.today()).strftime("%Y-%m-%d")

with st.sidebar.expander("הגדר/עדכן יעדים ליום זה"):
    target_cal = st.number_input("יעד קלוריות", value=2200, step=50)
    target_p = st.number_input("יעד חלבון (ג')", value=170, step=5)
    target_c = st.number_input("יעד פחמימות (ג')", value=220, step=5)
    target_f = st.number_input("יעד שומן (ג')", value=60, step=5)
    if st.button("שמור יעדים"):
        db.set_daily_goal(selected_date, target_cal, target_p, target_c, target_f)
        st.success("היעדים נשמרו בהצלחה!")

tab_log, tab_add_food = st.tabs(["📝 יומן אכילה", "➕ הוספת מאכל למאגר"])

with tab_log:
    st.subheader(f"תיעוד ארוחות לתאריך: {selected_date}")
    
    foods = db.get_all_foods()
    if not foods:
        st.warning("אין מאכלים במסד הנתונים. עבור ללשונית 'הוספת מאכל' כדי להתחיל.")
    else:
        food_dict = {f"{name} (ID: {fid})": fid for fid, name in foods}
        
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        with col1:
            selected_food_str = st.selectbox("בחר מאכל", list(food_dict.keys()))
        with col2:
            amount_g = st.number_input("כמות בגרמים", min_value=1.0, value=100.0, step=10.0)
        with col3:
            meal_type = st.selectbox("ארוחה", ["בוקר", "צהריים", "ערב", "נשנוש / אימון"])
        with col4:
            st.write("")
            st.write("")
            if st.button("הוסף ליומן"):
                food_id = food_dict[selected_food_str]
                db.log_meal(selected_date, food_id, amount_g, meal_type)
                st.rerun()

    summary = db.get_daily_summary(selected_date)
    
    st.divider()
    st.subheader("📊 סיכום יומי")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("קלוריות", f"{summary['consumed']['calories']} / {summary['targets']['calories']}", f"נותרו {summary['remaining']['calories']}")
    c2.metric("חלבון", f"{summary['consumed']['protein']}g / {summary['targets']['protein']}g", f"נותרו {summary['remaining']['protein']}g")
    c3.metric("פחמימות", f"{summary['consumed']['carbs']}g / {summary['targets']['carbs']}g", f"נותרו {summary['remaining']['carbs']}g")
    c4.metric("שומן", f"{summary['consumed']['fat']}g / {summary['targets']['fat']}g", f"נותרו {summary['remaining']['fat']}g")

    if summary["entries"]:
        st.subheader("📋 פירוט ארוחות שנרשמו")
        st.table(summary["entries"])

with tab_add_food:
    st.subheader("הוספת מאכל חדש למאגר (לערכים של 100 גרם)")
    with st.form("add_food_form"):
        name = st.text_input("שם המאכל")
        col_a, col_b = st.columns(2)
        with col_a:
            cal = st.number_input("קלוריות ל-100ג", min_value=0.0, step=1.0)
            p = st.number_input("חלבון ל-100ג", min_value=0.0, step=0.1)
        with col_b:
            c = st.number_input("פחמימות ל-100ג", min_value=0.0, step=0.1)
            f = st.number_input("שומן ל-100ג", min_value=0.0, step=0.1)
            
        submitted = st.form_submit_button("שמור מאכל")
        if submitted and name:
            db.add_food_item(name, cal, p, c, f)
            st.success(f"המאכל '{name}' נשמר בהצלחה במסד הנתונים!")