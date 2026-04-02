from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from youtube_api import get_comments, reply_to_comment, get_videos
from analysis import analyze_comments

llm = ChatOllama(model="llama3.2")

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
def post_comment_reply(comment_id: str, reply_text: str):
    """Replies to a specific YouTube comment. Needs the exact comment_id (found using fetch_video_comments tool)."""
    return reply_to_comment(comment_id, reply_text)

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

tools = [fetch_recent_videos, fetch_video_comments, post_comment_reply, analyze_video_by_id]

from langchain_core.messages import SystemMessage

system_prompt = SystemMessage(content="""You are an expert YouTube Channel AI Manager.
CRITICAL RULES:
1. You MUST use your available tools to accomplish the user's request.
2. DO NOT write out raw JSON tool calls in your chat messages! You must execute them natively using your tool calling abilities!
3. DO NOT guess comment IDs or video IDs. If you don't know the exact ID, you MUST use the fetch_recent_videos tool.
4. After you use a tool, read the actual results and then take further action or respond.
""")

agent_executor = create_react_agent(llm, tools, prompt=system_prompt)
