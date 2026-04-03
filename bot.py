import os
import requests
import json

# Load configurations from environment variables
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
IG_USER_ID = os.getenv('IG_USER_ID')
KEYWORD = os.getenv('KEYWORD', 'link').lower()
REPLY_TEXT = os.getenv('COMMENT_REPLY_TEXT', 'Sent you a DM!')
DM_TEXT = os.getenv('DM_TEXT', 'Here is the link you requested!')

# File to track processed comments
DB_FILE = "processed_comments.json"

def load_processed():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return []

def save_processed(comment_id):
    processed = load_processed()
    processed.append(comment_id)
    with open(DB_FILE, "w") as f:
        json.dump(processed, f)

def get_media():
    url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media?access_token={ACCESS_TOKEN}"
    response = requests.get(url).json()
    return response.get('data', [])

def get_comments(media_id):
    url = f"https://graph.facebook.com/v19.0/{media_id}/comments?access_token={ACCESS_TOKEN}"
    response = requests.get(url).json()
    return response.get('data', [])

def reply_to_comment(comment_id):
    url = f"https://graph.facebook.com/v19.0/{comment_id}/replies"
    payload = {'message': REPLY_TEXT, 'access_token': ACCESS_TOKEN}
    requests.post(url, data=payload)

def send_dm(recipient_id):
    # Note: recipient_id for IG DMs via API is the 'from' ID in the comment
    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": DM_TEXT}
    }
    requests.post(url, json=payload)

def main():
    processed_list = load_processed()
    media_items = get_media()
    
    for media in media_items:
        comments = get_comments(media['id'])
        for comment in comments:
            comment_id = comment.get('id')
            text = comment.get('text', '').lower()
            sender_id = comment.get('from', {}).get('id')

            if KEYWORD in text and comment_id not in processed_list:
                print(f"Processing comment: {comment_id}")
                
                # 1. Reply to Comment
                reply_to_comment(comment_id)
                
                # 2. Send DM
                if sender_id:
                    send_dm(sender_id)
                
                # 3. Mark as done
                save_processed(comment_id)

if __name__ == "__main__":
    main()
