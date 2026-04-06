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
        print("❌ Empty media list or error:", media_resp)
        return

    for media in media_items:
        media_id = media['id']
        
        # Added 'username' to the fields request
        comments_url = f"https://graph.facebook.com/v19.0/{media_id}/comments?fields=id,text,username&access_token={ACCESS_TOKEN}"
        comments_resp = requests.get(comments_url).json()
        
        # Safely handle API errors if they occur
        if 'error' in comments_resp:
            print(f"⚠️ Error fetching comments for post {media_id}: {comments_resp['error']['message']}")
            continue

        for comment in comments_resp.get('data', []):
            comment_id = comment.get('id')
            text = comment.get('text', '').lower()
            username = comment.get('username', 'there') # Fallback to 'there' if hidden

            if KEYWORD in text and comment_id not in processed_list:
                print(f"\n🎯 Match found on comment ID: {comment_id} | User: @{username}")

                # STEP A: Public Reply (Now mentions their username)
                reply_url = f"https://graph.facebook.com/v19.0/{comment_id}/replies"
                final_reply_text = f"@{username} {REPLY_TEXT}"
                
                reply_resp = requests.post(reply_url, data={'message': final_reply_text, 'access_token': ACCESS_TOKEN}).json()
                
                if 'id' in reply_resp:
                    print(f"  ✅ Comment Reply sent publicly to @{username}")
                else:
                    print(f"  ❌ Comment Reply Failed: {reply_resp.get('error', {}).get('message', reply_resp)}")
                
                # STEP B: Private DM (Your original working method)
                dm_url = f"https://graph.facebook.com/v19.0/{comment_id}/private_replies"
                dm_resp = requests.post(dm_url, data={'message': DM_TEXT, 'access_token': ACCESS_TOKEN}).json()

                if dm_resp.get('success') or 'id' in dm_resp:
                    print(f"  ✅ DM Link sent successfully to @{username}")
                else:
                    msg = dm_resp.get('error', {}).get('message', '')
                    print(f"  ❌ DM Failed to @{username}: {msg}")
                    print(f"  🔍 RAW DM ERROR DATA: {dm_resp}") # This will tell us EXACTLY why the link fails

                # Add to processed list regardless so it doesn't loop forever on a failed comment
                processed_list.append(comment_id)

    save_processed(processed_list)
    print("\n🤖 Agent Task Completed.")

if __name__ == "__main__":
    main()
