from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from youtube_api import get_comments, get_videos, reply_to_comment, post_top_level_comment as api_post_top_level
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
def post_comment_reply(comment_id: str, reply_text: str):
    """Replies to a specific YouTube comment. Needs the exact comment_id (found using fetch_video_comments tool)."""
    return reply_to_comment(comment_id, reply_text)

@tool
def post_top_level_comment(video_id: str, text: str):
    """Posts a top-level announcement comment on a video (NOT a reply to an existing comment). Use this for making general announcements."""
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

tools = [fetch_recent_videos, fetch_video_comments, post_comment_reply, post_top_level_comment, analyze_video_by_id]

from langchain_core.messages import SystemMessage

system_prompt = """You are an expert YouTube Channel AI Manager.
You have the following core capabilities. When a user asks what you can do, explicitly list these out:
- List the 10 most recent videos on the channel
- View the latest comments on any specific video
- Summarize and analyze comments using structured AI insights
- Reply directly to user comments on behalf of the channel owner
- Create top-level standalone announcement comments on videos

CRITICAL RULES:
1. If the user asks a conversational question (like "what can you do?"), simply reply with text and DO NOT use any tools.
2. If the user asks you to perform an action on YouTube, you MUST use your available tools. Always execute your tool calls internally.
3. DO NOT guess comment IDs or video IDs. If you don't know the exact ID, you MUST use the fetch_recent_videos tool.
4. After you use a tool, read the actual results and then take further action or respond with your analysis.

WORKFLOW FOR REPLYING TO A COMMENT:
Step 1. Find `video_id` via `fetch_recent_videos`.
Step 2. Find exact `comment_id` via `fetch_video_comments`.
Step 3. Use `post_comment_reply` to actually post the reply.

WORKFLOW FOR MAKING A NEW ANNOUNCEMENT (TOP-LEVEL) COMMENT:
Step 1. Find `video_id` via `fetch_recent_videos`.
Step 2. Use `post_top_level_comment` to actually post the text directly on the video.

"""

agent_executor = create_react_agent(llm, tools, prompt=system_prompt, checkpointer=memory)
