import os
import requests
import json

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

def save_processed(comment_id):
    processed = load_processed()
    if comment_id not in processed:
        processed.append(comment_id)
        with open(DB_FILE, "w") as f:
            json.dump(processed, f)

def main():
    if not ACCESS_TOKEN or not IG_USER_ID:
        print("❌ ERROR: Missing ACCESS_TOKEN or IG_USER_ID in Secrets!")
        return

    processed_list = load_processed()
    print(f"🤖 Starting bot. Monitoring for keyword: '{KEYWORD}'")

    # 1. Get Media
    media_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media?access_token={ACCESS_TOKEN}"
    media_resp = requests.get(media_url).json()
    
    if 'data' not in media_resp:
        print(f"❌ API ERROR: Could not fetch media. Response: {media_resp}")
        return

    media_items = media_resp.get('data', [])
    print(f"📸 Found {len(media_items)} posts. Checking comments...")

    for media in media_items:
        media_id = media['id']
        comments_url = f"https://graph.facebook.com/v19.0/{media_id}/comments?access_token={ACCESS_TOKEN}"
        comments_resp = requests.get(comments_url).json()
        
        comments = comments_resp.get('data', [])
        for comment in comments:
            comment_id = comment.get('id')
            text = comment.get('text', '').lower()

            # Skip if already processed
            if comment_id in processed_list:
                continue

            # Check for keyword
            if KEYWORD in text:
                print(f"🎯 Found keyword in comment {comment_id}: '{text}'")

                # A. Public Reply to Comment
                reply_url = f"https://graph.facebook.com/v19.0/{comment_id}/replies"
                r_payload = {'message': REPLY_TEXT, 'access_token': ACCESS_TOKEN}
                r_resp = requests.post(reply_url, data=r_payload).json()
                
                if 'id' in r_resp:
                    print(f" ✅ Public reply sent!")
                else:
                    print(f" ❌ Public reply failed: {r_resp}")

                # B. Private DM Reply (The correct way for IG comments)
                dm_url = f"https://graph.facebook.com/v19.0/{comment_id}/private_replies"
                d_payload = {'message': DM_TEXT, 'access_token': ACCESS_TOKEN}
                d_resp = requests.post(dm_url, data=d_payload).json()

                if d_resp.get('success') or 'id' in d_resp:
                    print(f" ✅ Private DM sent!")
                else:
                    print(f" ❌ Private DM failed: {d_resp}")
                
                save_processed(comment_id)

if __name__ == "__main__":
    main()
