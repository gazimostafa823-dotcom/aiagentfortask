import os
import requests
import json
from datetime import datetime

# Load configurations from environment variables
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
IG_USER_ID = os.getenv('IG_USER_ID')
KEYWORD = os.getenv('KEYWORD', 'link').lower()
REPLY_TEXT = os.getenv('COMMENT_REPLY_TEXT', 'Sent you a DM!')
DM_TEXT = os.getenv('DM_TEXT', 'Here is the link you requested!')

DB_FILE = "processed_comments.json"
GRAPH_API_VERSION = "v19.0"

def load_processed():
    """Loads the list of already processed comment IDs."""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_processed(processed_list):
    """Saves the list of processed comment IDs back to the JSON file."""
    with open(DB_FILE, "w") as f:
        json.dump(processed_list, f, indent=4)

def main():
    if not ACCESS_TOKEN or not IG_USER_ID:
        print("❌ CONFIG ERROR: Missing ACCESS_TOKEN or IG_USER_ID Secrets.")
        return

    processed_list = load_processed()
    print(f"🤖 AGENT STARTING: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔍 Searching for keyword: '{KEYWORD}'")

    # 1. Get all Media (limit to last 50 posts)
    media_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{IG_USER_ID}/media?limit=50&access_token={ACCESS_TOKEN}"
    media_resp = requests.get(media_url).json()
    media_items = media_resp.get('data', [])

    if not media_items:
        print("Empty media list or error fetching media:", media_resp)
        return

    # 2. Iterate through posts to find comments
    for media in media_items:
        media_id = media['id']
        comments_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{media_id}/comments?access_token={ACCESS_TOKEN}"
        comments_resp = requests.get(comments_url).json()
        
        for comment in comments_resp.get('data', []):
            comment_id = comment.get('id')
            text = comment.get('text', '').lower()

            if KEYWORD in text and comment_id not in processed_list:
                print(f"🎯 Match found on comment ID: {comment_id}")

                # STEP A: Public Reply to the comment
                reply_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{comment_id}/replies"
                reply_resp = requests.post(reply_url, data={'message': REPLY_TEXT, 'access_token': ACCESS_TOKEN}).json()
                
                if 'id' in reply_resp:
                    print("  ✅ Public reply sent.")
                else:
                    print(f"  ⚠️ Reply Failed: {reply_resp.get('error', {}).get('message', 'Unknown error')}")

                # STEP B: Private DM to the user
                dm_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{comment_id}/private_replies"
                dm_resp = requests.post(dm_url, data={'message': DM_TEXT, 'access_token': ACCESS_TOKEN}).json()

                if dm_resp.get('success') or 'id' in dm_resp:
                    print("  ✅ DM sent to user.")
                else:
                    msg = dm_resp.get('error', {}).get('message', 'Unknown error')
                    print(f"  ❌ DM Failed: {msg}")
                    if "permissions" in msg.lower() or "access" in msg.lower():
                        print("  💡 TIP: Check 'Allow Access to Messages' in your IG App settings.")

                # Mark as processed regardless of success to prevent infinite spam loops on broken comments
                processed_list.append(comment_id)

    # Save progress
    save_processed(processed_list)
    print("🤖 Agent Task Completed.")

if __name__ == "__main__":
    main()
