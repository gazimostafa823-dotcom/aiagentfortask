import os
import requests
import sys

# --- Configuration ---
# Load credentials and config from GitHub environment variables
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
IG_USER_ID = os.getenv('IG_USER_ID')
PAGE_ID = os.getenv('PAGE_ID')
KEYWORD = os.getenv('KEYWORD', 'link').lower() # Default to 'link' if not set
COMMENT_REPLY_TEXT = os.getenv('COMMENT_REPLY_TEXT', "I've sent the link to your DM!")
DM_TEXT_TEMPLATE = os.getenv('DM_TEXT_TEMPLATE', "Hey {username}! Here's the link you requested: {link}")
YOUR_LINK = os.getenv('YOUR_LINK', 'https://www.example.com')

# File to store IDs of comments we've already replied to
PROCESSED_COMMENTS_FILE = 'processed_comments.txt'

# --- Helper Functions ---

def load_processed_comments():
    """Loads a set of processed comment IDs from a file."""
    if not os.path.exists(PROCESSED_COMMENTS_FILE):
        return set()
    with open(PROCESSED_COMMENTS_FILE, 'r') as f:
        return set(line.strip() for line in f)

def save_processed_comment(comment_id):
    """Appends a new processed comment ID to the file."""
    with open(PROCESSED_COMMENTS_FILE, 'a') as f:
        f.write(f"{comment_id}\n")

def reply_to_comment(comment_id, message):
    """Posts a reply to a specific comment."""
    url = f"https://graph.facebook.com/v18.0/{comment_id}/replies"
    params = {
        'message': message,
        'access_token': ACCESS_TOKEN
    }
    response = requests.post(url, params=params)
    if response.status_code == 200:
        print(f"Successfully replied to comment {comment_id}")
    else:
        print(f"Error replying to comment {comment_id}: {response.json()}")

def send_dm(recipient_psid, message):
    """Sends a direct message to a user."""
    url = f"https://graph.facebook.com/v18.0/me/messages"
    payload = {
        'recipient': {'id': recipient_psid},
        'message': {'text': message},
        'messaging_type': 'RESPONSE',
        'access_token': ACCESS_TOKEN
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print(f"Successfully sent DM to user {recipient_psid}")
    else:
        print(f"Error sending DM to user {recipient_psid}: {response.json()}")

# --- Main Logic ---

def main():
    """Main function to fetch comments and process them."""
    if not all([ACCESS_TOKEN, IG_USER_ID, PAGE_ID]):
        print("Error: Missing one or more required environment variables (ACCESS_TOKEN, IG_USER_ID, PAGE_ID).")
        sys.exit(1)

    processed_ids = load_processed_comments()
    print(f"Loaded {len(processed_ids)} processed comment IDs.")

    # 1. Get the user's media (posts)
    media_url = f"https://graph.facebook.com/v18.0/{IG_USER_ID}/media"
    params = {'access_token': ACCESS_TOKEN, 'fields': 'id,caption'}
    media_response = requests.get(media_url, params=params)
    
    if media_response.status_code != 200:
        print(f"Error fetching media: {media_response.json()}")
        return
        
    media_data = media_response.json().get('data', [])
    print(f"Found {len(media_data)} media posts to check.")

    for media in media_data:
        media_id = media['id']
        
        # 2. Get comments for each media item
        comments_url = f"https://graph.facebook.com/v18.0/{media_id}/comments"
        params = {
            'access_token': ACCESS_TOKEN,
            'fields': 'id,text,from,username'
        }
        comments_response = requests.get(comments_url, params=params)
        
        if comments_response.status_code != 200:
            print(f"Error fetching comments for media {media_id}: {comments_response.json()}")
            continue

        comments_data = comments_response.json().get('data', [])

        for comment in comments_data:
            comment_id = comment['id']
            comment_text = comment['text'].lower()
            commenter_username = comment['username']
            commenter_psid = comment['from']['id'] # Page-Scoped ID for messaging

            # 3. Check if we should reply
            if comment_id in processed_ids:
                continue # Skip already processed comments

            if KEYWORD in comment_text:
                print(f"Keyword '{KEYWORD}' found in comment ID {comment_id} by {commenter_username}")

                # Reply to the comment
                reply_to_comment(comment_id, COMMENT_REPLY_TEXT)

                # Format the DM text
                dm_message = DM_TEXT_TEMPLATE.format(username=commenter_username, link=YOUR_LINK)

                # Send the DM
                send_dm(commenter_psid, dm_message)
                
                # Mark as processed
                save_processed_comment(comment_id)

    print("Script finished.")


if __name__ == "__main__":
    main()
