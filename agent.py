from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from youtube_api import get_comments, get_videos, get_video_stats, reply_to_comment, post_top_level_comment as api_post_top_level
from analysis import analyze_comments

from langgraph.checkpoint.memory import MemorySaver

llm = ChatOllama(model="llama3.2", temperature=0)
memory = MemorySaver()
@tool
def fetch_recent_videos(channel_id: str):
    """Fetches the 10 most recent videos from a YouTube channel. Returns a list of dictionaries with 'title' and 'video_id'. 
    Store the 'video_id' in your memory, as you MUST use this 11-character ID (NOT the title) for down-stream tools."""
    return get_videos(channel_id)

@tool
def fetch_video_comments(video_id: str):
    """Fetches the latest comments from a specific YouTube video. 
    ALWAYS pass the exact 11-character video_id (e.g. 'abc123xyz45'). NEVER pass the video title.
    Returns a list of dictionaries containing comment_id, author, and text."""
    if len(video_id) > 20: 
        return "ERROR: You passed a title instead of a video_id. You must use exactly the 11-character video_id."
    return get_comments(video_id)

@tool
def filter_recent_videos(channel_id: str, min_likes: int = 0):
    """Fetches the latest 10 videos and filters them to return only ones with at least `min_likes` likes."""
    videos = get_videos(channel_id)
    if not videos: return "No videos found."
    v_ids = [v["video_id"] for v in videos]
    stats = get_video_stats(v_ids)
    
    # Map likes to videos
    results = []
    for stat in stats.get("items", []):
        likes = int(stat["statistics"].get("likeCount", 0))
        if likes >= min_likes:
            # find matching title
            title = next((v["title"] for v in videos if v["video_id"] == stat["id"]), "Unknown")
            results.append({"video_id": stat["id"], "title": title, "likes": likes})
    return results

@tool
def find_frequent_commenters(video_id: str, min_comments: int):
    """Finds exact comment IDs of users who have commented on a video at least `min_comments` times."""
    if len(video_id) != 11 or "[" in video_id or "cXYZ" in video_id: 
        return "ERROR: You passed an invalid or placeholder video_id. You must use the EXACT 11-character video_id array element found earlier."
    comments = get_comments(video_id)
    from collections import defaultdict
    author_counts = defaultdict(list)
    
    for c in comments:
        author_counts[c["author"]].append({
            "comment_id": c["comment_id"], 
            "text": c["text"]
        })
        
    results = []
    for author, items in author_counts.items():
        if len(items) >= min_comments:
            results.append({
                "author": author,
                "total_comments": len(items),
                "comments": items
            })
    return results if results else "No commenters found meeting the threshold."

@tool
def post_comment_reply(comment_id: str, reply_text: str):
    """Replies to a specific YouTube comment. Needs the exact comment_id (found using fetch_video_comments tool)."""
    return reply_to_comment(comment_id, reply_text)

@tool
def post_top_level_comment(video_id: str, text: str):
    """Posts a top-level announcement comment on a video (NOT a reply to an existing comment). Use this for making general announcements."""
    if len(video_id) != 11 or "[" in video_id or "cXYZ" in video_id: 
        return "ERROR: You passed a placeholder video_id. You must use the actual 11-character ID."
    return api_post_top_level(video_id, text)

@tool
def analyze_video_by_id(video_id: str):
    """Fetches comments for a specific YouTube video and immediately generates structured AI insights on them.
    ALWAYS pass the exact 11-character video_id. NEVER pass the video title."""
    if len(video_id) > 20: 
        return "ERROR: You passed a title instead of a video_id. You must use exactly the 11-character video_id. If you don't know it, run fetch_recent_videos first."
    if "dQw4w9WgXcQ" in video_id:
        return "ERROR: You used the dummy Rick Astley ID. Use fetch_recent_videos to find the ACTUAL video ID for the requested video."
    
    comments = get_comments(video_id)
    return analyze_comments(comments)

tools = [fetch_recent_videos, fetch_video_comments, filter_recent_videos, find_frequent_commenters, post_comment_reply, post_top_level_comment, analyze_video_by_id]

from langchain_core.messages import SystemMessage

system_prompt = """You are an expert YouTube Channel AI Manager.
You have the following core capabilities. When a user asks what you can do, explicitly list these out:
- List the 10 most recent videos on the channel
- View the latest comments on any specific video
- Summarize and analyze comments using structured AI insights
- Reply directly to user comments on behalf of the channel owner
- Create top-level standalone announcement comments on videos
- Filter videos by like count criteria
- Find frequent commenters (super-fans) on a video

CRITICAL RULES:
1. If the user asks a conversational question (like "what can you do?"), simply reply with text and DO NOT use any tools.
2. If the user asks you to perform an action on YouTube, you MUST use your available tools. Always execute your tool calls internally.
3. DO NOT guess comment IDs or video IDs. NEVER pass placeholders or dummy variables. You must ONLY pass the exact string value returned to you by previous tool executions.
4. YOU MUST execute tools ONE AT A TIME. DO NOT execute multiple tools in parallel if one depends on the output of another. Wait for the result of step 1 before starting step 2!
5. After you use a tool, read the actual results and then take further action or respond with your analysis.

WORKFLOW FOR REPLYING TO A SPECIFIC COMMENT:
Step 1. Find `video_id` via `fetch_recent_videos`.
Step 2. Find exact `comment_id` via `fetch_video_comments`.
Step 3. Use `post_comment_reply` to actually post the reply.

WORKFLOW FOR FINDING & REPLYING TO FREQUENT COMMENTERS (SUPER-FANS):
Step 1. Find exact `video_id` (use `fetch_recent_videos` or `filter_recent_videos` if criteria is given).
Step 2. Use the `find_frequent_commenters` tool to automatically parse the JSON and return matching comment IDs. Do NOT use fetch_video_comments for this!
Step 3. Use `post_comment_reply` to reply to them natively.

WORKFLOW FOR MAKING A NEW ANNOUNCEMENT (TOP-LEVEL) COMMENT:
Step 1. Find `video_id` via `fetch_recent_videos` or `filter_recent_videos`.
Step 2. Use `post_top_level_comment` to actually post the text directly on the video.

"""

agent_executor = create_react_agent(llm, tools, prompt=system_prompt, checkpointer=memory)
