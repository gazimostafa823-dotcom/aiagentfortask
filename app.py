import streamlit as st
import requests
import json
import os

# --- Configuration ---
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN', 'YOUR_ACCESS_TOKEN_HERE')
IG_USER_ID = os.getenv('IG_USER_ID', 'YOUR_IG_USER_ID_HERE')
RULES_FILE = "rules.json"

def load_rules():
    if os.path.exists(RULES_FILE):
        with open(RULES_FILE, "r") as f:
            return json.load(f)
    return {}

def save_rules(rules):
    with open(RULES_FILE, "w") as f:
        json.dump(rules, f, indent=4)

# --- Fetch Instagram Posts ---
@st.cache_data(ttl=300)
def get_recent_posts():
    if not ACCESS_TOKEN or not IG_USER_ID:
        return []
    url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media?fields=id,shortcode,caption,media_url&limit=20&access_token={ACCESS_TOKEN}"
    response = requests.get(url).json()
    return response.get('data', [])

# --- Dashboard UI ---
st.set_page_config(page_title="My IG Bot Dashboard", page_icon="🤖")
st.title("🤖 Instagram Auto-Reply Dashboard")

posts = get_recent_posts()

if not posts:
    st.error("Could not fetch posts. Check your ACCESS_TOKEN and IG_USER_ID.")
else:
    st.write("### 1. Select a Post to Automate")
    
    # Create a visual selector for posts
    post_options = {}
    for p in posts:
        caption = p.get('caption', 'No caption')[:60] + "..."
        post_options[p['id']] = f"{p['shortcode']} - {caption}"

    selected_post_id = st.selectbox("Choose a post:", options=list(post_options.keys()), format_func=lambda x: post_options[x])

    st.write("### 2. Set Up Your Rule")
    rules = load_rules()
    
    # Pre-fill with existing rule if it exists
    existing_rule = rules.get(selected_post_id, {"keyword": "", "reply_text": ""})
    
    keyword = st.text_input("Trigger Keyword:", value=existing_rule.get("keyword"))
    reply_text = st.text_area("Public Reply Text:", value=existing_rule.get("reply_text"))

    if st.button("Save Automation"):
        if keyword and reply_text:
            rules[selected_post_id] = {
                "shortcode": [p['shortcode'] for p in posts if p['id'] == selected_post_id][0],
                "keyword": keyword.lower().strip(),
                "reply_text": reply_text.strip()
            }
            save_rules(rules)
            st.success(f"✅ Automation saved for post {rules[selected_post_id]['shortcode']}!")
        else:
            st.warning("Please enter both a keyword and a reply text.")

    # Show active rules
    st.write("---")
    st.write("### Active Automations")
    if rules:
        for pid, rule in rules.items():
            st.info(f"**Post:** {rule['shortcode']} | **Keyword:** {rule['keyword']} | **Reply:** {rule['reply_text']}")
    else:
        st.write("No active automations yet.")
