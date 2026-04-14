import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

def get_youtube_service():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("client_secret.json"):
                raise Exception("Missing client_secret.json! Please download it from Google Cloud Console.")
            flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    # Build a fresh YouTube service object every time to prevent stale httplib2 SSL connections
    return build("youtube", "v3", credentials=creds, cache_discovery=False)

def get_videos(channel_id):
    youtube = get_youtube_service()
    request = youtube.search().list(
        part="snippet",
        channelId=channel_id,
        maxResults=10,
        order="date"
    )
    response = request.execute()
    
    videos = []
    for item in response.get("items", []):
        if item["id"]["kind"] == "youtube#video":
            videos.append({
                "title": item["snippet"]["title"],
                "video_id": item["id"]["videoId"]
            })
    return videos

def get_video_stats(video_ids):
    if not video_ids: return {"items": []}
    youtube = get_youtube_service()
    request = youtube.videos().list(
        part="statistics",
        id=",".join(video_ids)
    )
    return request.execute()

def get_comments(video_id):
    youtube = get_youtube_service()
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=50
        )
        response = request.execute()

        comments = []
        for item in response.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "comment_id": item["id"],
                "author": snippet.get("authorDisplayName", "Unknown"),
                "text": snippet.get("textOriginal", snippet.get("textDisplay", ""))
            })

        return comments

    except HttpError as e:
        if "commentsDisabled" in str(e):
            print(f"Comments disabled for video: {video_id}")
            return []
        else:
            raise e

def reply_to_comment(parent_comment_id, text):
    youtube = get_youtube_service()
    try:
        request = youtube.comments().insert(
            part="snippet",
            body={
                "snippet": {
                    "parentId": parent_comment_id,
                    "textOriginal": text
                }
            }
        )
        response = request.execute()
        return f"Success! Replied to {parent_comment_id} with ID: {response['id']}"
    except HttpError as e:
        return f"Failed to reply. Ensure you are authorized. Error: {e}"

def post_top_level_comment(video_id, text):
    youtube = get_youtube_service()
    try:
        request = youtube.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": text
                        }
                    }
                }
            }
        )
        response = request.execute()
        return f"Success! Announcement posted on video {video_id}. Comment ID: {response['id']}"
    except HttpError as e:
        return f"Failed to post announcement. Ensure you are authorized. Error: {e}"