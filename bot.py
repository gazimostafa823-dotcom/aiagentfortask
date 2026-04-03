import os
import requests
import json
import time

# ── Config from GitHub Secrets / Variables ──────────────────────────────────
ACCESS_TOKEN       = os.environ["ACCESS_TOKEN"]
IG_USER_ID         = os.environ["IG_USER_ID"]
KEYWORD            = os.environ.get("KEYWORD", "link").lower()
COMMENT_REPLY_TEXT = os.environ.get("COMMENT_REPLY_TEXT", "Check your DM! I sent it.")
DM_TEXT            = os.environ.get("DM_TEXT", "Here is the link: https://google.com")

BASE = "https://graph.facebook.com/v19.0"

# ── Helpers ──────────────────────────────────────────────────────────────────

def get_recent_media():
    """Return list of recent media objects for the IG business account."""
    url = f"{BASE}/{IG_USER_ID}/media"
    params = {
        "fields": "id,caption,timestamp",
        "access_token": ACCESS_TOKEN,
        "limit": 10,
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json().get("data", [])


def get_comments(media_id):
    """Return all top-level comments on a given media post."""
    url = f"{BASE}/{media_id}/comments"
    params = {
        "fields": "id,text,username,from,timestamp",
        "access_token": ACCESS_TOKEN,
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json().get("data", [])


def reply_to_comment(comment_id, message):
    """Post a public reply under a comment."""
    url = f"{BASE}/{comment_id}/replies"
    data = {
        "message": message,
        "access_token": ACCESS_TOKEN,
    }
    r = requests.post(url, data=data)
    r.raise_for_status()
    return r.json()


def send_dm(recipient_id, message):
    """Send a DM via the Instagram Messaging API."""
    url = f"{BASE}/{IG_USER_ID}/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message},
        "access_token": ACCESS_TOKEN,
    }
    r = requests.post(url, json=payload)
    r.raise_for_status()
    return r.json()


def load_processed():
    """Load already-handled comment IDs from local cache file."""
    try:
        with open("processed_comments.json", "r") as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()


def save_processed(ids: set):
    """Persist handled comment IDs so we never double-reply."""
    with open("processed_comments.json", "w") as f:
        json.dump(list(ids), f)


# ── Main loop ─────────────────────────────────────────────────────────────────

def run():
    print(f"[BOT] Starting — watching for keyword: '{KEYWORD}'")
    processed = load_processed()

    media_list = get_recent_media()
    print(f"[BOT] Checking {len(media_list)} recent post(s)…")

    for media in media_list:
        media_id = media["id"]
        comments = get_comments(media_id)

        for comment in comments:
            cid  = comment["id"]
            text = comment.get("text", "").lower()

            if cid in processed:
                continue  # already handled

            if KEYWORD in text:
                commenter = comment.get("from", {})
                commenter_id   = commenter.get("id")
                commenter_name = commenter.get("username", commenter_id)

                print(f"[BOT] Keyword found in comment {cid} by @{commenter_name}")

                # 1️⃣  Reply publicly on the comment
                try:
                    reply_to_comment(cid, COMMENT_REPLY_TEXT)
                    print(f"[BOT]   ✅ Replied to comment {cid}")
                except Exception as e:
                    print(f"[BOT]   ⚠️  Comment reply failed: {e}")

                # 2️⃣  Send DM with the link
                if commenter_id:
                    try:
                        send_dm(commenter_id, DM_TEXT)
                        print(f"[BOT]   ✅ DM sent to {commenter_id}")
                    except Exception as e:
                        print(f"[BOT]   ⚠️  DM failed: {e}")
                else:
                    print("[BOT]   ⚠️  No commenter ID — cannot send DM")

                processed.add(cid)
                time.sleep(1)  # gentle rate-limit buffer

    save_processed(processed)
    print("[BOT] Done.")


if __name__ == "__main__":
    run()
