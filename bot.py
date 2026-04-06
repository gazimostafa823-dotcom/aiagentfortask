import os
import requests
import json
from datetime import datetime

ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
DB_FILE = "processed_comments.json"
RULES_FILE = "rules.json"
GRAPH_API_VERSION = "v19.0"

def load_json(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {} if filepath == RULES_FILE else []
    return {} if filepath == RULES_FILE else []

def save_processed(processed_list):
    with open(DB_FILE, "w") as f:
        json.dump(processed_list, f, indent=4)

def main():
    rules = load_json(RULES_FILE)
    if not rules:
        print("No active rules found in rules.json. Exiting.")
        return

    processed_list = load_json(DB_FILE)
    print(f"🤖 AGENT STARTING: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Loop through only the posts that have active rules set up in the dashboard
    for post_id, rule in rules.items():
        keyword = rule['keyword']
        reply_text = rule['reply_text']
        print(f"🔍 Checking Post ID: {post_id} for keyword '{keyword}'")

        comments_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{post_id}/comments?access_token={ACCESS_TOKEN}"
        comments_resp = requests.get(comments_url).json()
        
        for comment in comments_resp.get('data', []):
            comment_id = comment.get('id')
            text = comment.get('text', '').lower()

            if keyword in text and comment_id not in processed_list:
                print(f"🎯 Match found on comment ID: {comment_id}")

                reply_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{comment_id}/replies"
                reply_resp = requests.post(reply_url, data={'message': reply_text, 'access_token': ACCESS_TOKEN}).json()
                
                if 'id' in reply_resp:
                    print("  ✅ Public reply sent.")
                else:
                    print(f"  ⚠️ Reply Failed: {reply_resp.get('error', {}).get('message')}")

                processed_list.append(comment_id)

    save_processed(processed_list)
    print("🤖 Agent Task Completed.")

if __name__ == "__main__":
    main()
