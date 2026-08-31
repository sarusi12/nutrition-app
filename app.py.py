st.markdown(
    f"""
    <style>
    /* הגדרת RTL רק לאזור התוכן המרכזי ולא לאלמנטים צפים */
    .stApp {{
        direction: {direction};
        text-align: {'right' if direction == 'rtl' else 'left'};
        background-color: {bg_color};
        color: {text_color};
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}

    /* מניעת שבירה של פופאפים, תפריטים צפים וטולטיפים של הדפדפן */
    [data-baseweb="popover"], [data-baseweb="tooltip"], [data-baseweb="menu"], div[role="dialog"] {{
        direction: ltr !important;
        text-align: left !important;
    }}

    .ios-widget {{
        background: {widget_bg};
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid {widget_border};
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
        margin-bottom: 15px;
        transition: transform 0.2s ease;
    }}
    .ios-widget:hover {{
        transform: translateY(-2px);
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
