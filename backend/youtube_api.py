import os
import pickle
import re
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi

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
            part="snippet,replies",
            videoId=video_id,
            maxResults=50
        )
        response = request.execute()

        comments = []
        for item in response.get("items", []):
            # Top-level comment
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "comment_id": item["id"],
                "author": snippet.get("authorDisplayName", "Unknown"),
                "text": snippet.get("textOriginal", snippet.get("textDisplay", "")),
                "is_reply": False
            })
            
            # Nested replies
            if "replies" in item:
                for reply in item["replies"].get("comments", []):
                    rep_snippet = reply["snippet"]
                    comments.append({
                        "comment_id": reply["id"],
                        "author": rep_snippet.get("authorDisplayName", "Unknown"),
                        "text": rep_snippet.get("textOriginal", rep_snippet.get("textDisplay", "")),
                        "is_reply": True
                    })

        return comments

    except HttpError as e:
        if "commentsDisabled" in str(e):
            print(f"Comments disabled for video: {video_id}")
            return []
        elif e.resp.status == 404 or "videoNotFound" in str(e):
            print(f"Video not found (404): {video_id}")
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

def delete_comment(comment_id):
    youtube = get_youtube_service()
    try:
        request = youtube.comments().delete(id=comment_id)
        request.execute()
        return f"Success! Deleted comment {comment_id}."
    except HttpError as e:
        return f"Failed to delete comment. Ensure you are authorized. Error: {e}"

def resolve_channel(query):
    youtube = get_youtube_service()
    
    # Check if it's a known URL format
    if "youtube.com/channel/" in query:
        return query.split("youtube.com/channel/")[-1].split("/")[0].split("?")[0]
    
    # Extract handle if starting with @, or from URL
    handle = None
    if query.startswith("@"):
        handle = query
    elif "youtube.com/@" in query:
        handle = "@" + query.split("youtube.com/@")[-1].split("/")[0].split("?")[0]
    
    if handle:
        # Search by handle
        request = youtube.search().list(
            part="snippet",
            q=handle,
            type="channel",
            maxResults=1
        )
        response = request.execute()
        if response.get("items"):
            return response["items"][0]["snippet"]["channelId"]
    
    # Generic search
    request = youtube.search().list(
        part="snippet",
        q=query,
        type="channel",
        maxResults=1
    )
    response = request.execute()
    if response.get("items"):
        return response["items"][0]["snippet"]["channelId"]
        
    return None

def get_channel_stats(channel_id):
    youtube = get_youtube_service()
    request = youtube.channels().list(
        part="statistics,snippet",
        id=channel_id
    )
    response = request.execute()
    if response.get("items"):
        item = response["items"][0]
        return {
            "channel_id": channel_id,
            "title": item["snippet"]["title"],
            "description": item["snippet"]["description"],
            "customUrl": item["snippet"].get("customUrl", ""),
            "subscriberCount": int(item["statistics"].get("subscriberCount", 0)),
            "videoCount": int(item["statistics"].get("videoCount", 0)),
            "viewCount": int(item["statistics"].get("viewCount", 0))
        }
    return None

def search_channels_by_niche(niche, max_results=5):
    youtube = get_youtube_service()
    # Search for top videos in that niche, which naturally bubbles up the most popular/relevant creators
    request = youtube.search().list(
        part="snippet",
        q=niche,
        type="video",
        maxResults=max_results * 5,
        order="relevance"
    )
    response = request.execute()
    
    seen_channels = set()
    channels = []
    
    for item in response.get("items", []):
        snippet = item["snippet"]
        channel_id = snippet["channelId"]
        
        if channel_id not in seen_channels:
            seen_channels.add(channel_id)
            channels.append({
                "title": snippet["channelTitle"],
                "channel_id": channel_id,
                "description": f"Found via popular video: {snippet['title']}"
            })
            
            if len(channels) >= max_results:
                break
                
    return channels

def get_video_transcript(video_id):
    try:
        # Fetch transcript using the class instance method
        transcript_list = YouTubeTranscriptApi().fetch(video_id)
        # Combine all parts into a single text block
        transcript_text = " ".join([t.text for t in transcript_list])
        return transcript_text
    except Exception as e:
        print(f"Error fetching transcript for {video_id}: {e}")
        return None