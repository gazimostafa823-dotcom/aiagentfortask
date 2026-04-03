import os
import requests
import json
from datetime import datetime

# Load configurations
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
IG_USER_ID = os.getenv('IG_USER_ID')
KEYWORD = os.getenv('KEYWORD', 'link').lower()
REPLY_TEXT = os.getenv('COMMENT_REPLY_TEXT', 'Sent you a DM!')
DM_TEXT = os.getenv('DM_TEXT', 'Here is the link you requested!')

DB_FILE = "processed_comments.json"

def load_processed():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_processed(processed_list):
    with open(DB_FILE, "w") as f:
        json.dump(processed_list, f)

def main():
    if not ACCESS_TOKEN or not IG_USER_ID:
        print("❌ CONFIG ERROR: Missing Secrets.")
        return

    processed_list = load_processed()
    print(f"🤖 AGENT STARTING: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔍 Searching for keyword: '{KEYWORD}'")

    # 1. Get all Media (limit to last 50 posts)
    media_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media?limit=50&access_token={ACCESS_TOKEN}"
    media_resp = requests.get(media_url).json()
    media_items = media_resp.get('data', [])

    if not media_items:
        print("Empty media list or error:", media_resp)
        return

    for media in media_items:
        media_id = media['id']
        comments_url = f"https://graph.facebook.com/v19.0/{media_id}/comments?access_token={ACCESS_TOKEN}"
        comments_resp = requests.get(comments_url).json()
        
        for comment in comments_resp.get('data', []):
            comment_id = comment.get('id')
            text = comment.get('text', '').lower()

            if KEYWORD in text and comment_id not in processed_list:
                print(f"🎯 Match found on comment ID: {comment_id}")

                # STEP A: Public Reply
                reply_url = f"https://graph.facebook.com/v19.0/{comment_id}/replies"
                requests.post(reply_url, data={'message': REPLY_TEXT, 'access_token': ACCESS_TOKEN})
                
                # STEP B: Private DM
                dm_url = f"https://graph.facebook.com/v19.0/{comment_id}/private_replies"
                dm_resp = requests.post(dm_url, data={'message': DM_TEXT, 'access_token': ACCESS_TOKEN}).json()

                if dm_resp.get('success') or 'id' in dm_resp:
                    print(f"  ✅ DM sent to user.")
                else:
                    # Specific error help
                    msg = dm_resp.get('error', {}).get('message', '')
                    print(f"  ❌ DM Failed: {msg}")
                    if "permissions" in msg:
                        print("  💡 TIP: Check 'Allow Access to Messages' in your IG App settings.")

                processed_list.append(comment_id)

    save_processed(processed_list)
    print("🤖 Agent Task Completed.")

if __name__ == "__main__":
    main()
