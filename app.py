import streamlit as st
from youtube_api import get_videos, get_comments, get_video_stats, reply_to_comment, post_top_level_comment
from analysis import analyze_comments
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

st.set_page_config(page_title="YouTube AI Analyst", layout="wide")

# 🎯 Title
st.title("📊 YouTube AI Analyst")

# 🎛️ Sidebar (acts like routing)
st.sidebar.title("Navigation")

channel_id = st.sidebar.text_input("Enter Channel ID")

page = st.sidebar.radio(
    "Go to",
    ["Overview", "Video Analysis", "AI Assistant"]
)

# 🚫 If no channel id
if not channel_id:
    st.warning("Enter a Channel ID to begin")
    st.stop()

# 📦 Fetch videos
@st.cache_data
def load_videos(channel_id):
    return get_videos(channel_id)

@st.cache_data
def load_comments(video_id):
    return get_comments(video_id)

videos = load_videos(channel_id)

if not videos:
    st.error("No videos found")
    st.stop()

# =========================================================
# 📊 OVERVIEW PAGE
# =========================================================
if page == "Overview":
    st.header("📊 Channel Overview")

    video_ids = [v["video_id"] for v in videos]
    stats = get_video_stats(video_ids)

    data = []
    for item in stats.get("items", []):
        data.append({
            "video_id": item["id"],
            "views": int(item["statistics"].get("viewCount", 0)),
            "likes": int(item["statistics"].get("likeCount", 0)),
        })

    # Merge with titles
    for v in videos:
        for d in data:
            if v["video_id"] == d["video_id"]:
                d["title"] = v["title"]

    # 📈 Show metrics
    total_views = sum(d["views"] for d in data)
    total_likes = sum(d["likes"] for d in data)

    col1, col2 = st.columns(2)
    col1.metric("Total Views", total_views)
    col2.metric("Total Likes", total_likes)

    st.divider()

    # 📋 Table
    st.subheader("📋 Video Performance")
    st.dataframe(data)

# =========================================================
# 🎬 VIDEO ANALYSIS PAGE
# =========================================================
elif page == "Video Analysis":
    st.header("🎬 Video Analysis")

    video_titles = [v["title"] for v in videos]

    selected_title = st.selectbox("Select a video", video_titles)

    video = next(v for v in videos if v["title"] == selected_title)

    st.subheader(f"🎥 {video['title']}")

    # 📊 Fetch stats
    stats = get_video_stats([video["video_id"]])
    if stats.get("items"):
        item = stats["items"][0]["statistics"]
        col1, col2 = st.columns(2)
        col1.metric("Views", item.get("viewCount", "N/A"))
        col2.metric("Likes", item.get("likeCount", "N/A"))
    else:
        st.warning("Stats unavailable")

    st.divider()

    # 💬 Fetch comments
    comments = load_comments(video["video_id"])

    if not comments:
        st.warning("No comments available for this video")
        st.stop()

    st.write(f"💬 Showing {min(len(comments), 30)} comments for analysis")

    # 🤖 Analyze
    if st.button("Analyze Comments"):
        with st.spinner("AI is thinking... 🧠"):
            result = analyze_comments(comments[:30])

        st.divider()
        st.subheader("🧠 AI Insights")

        st.text_area("Analysis Output", result, height=400)

# =========================================================
# 🤖 AI ASSISTANT PAGE
# =========================================================
elif page == "AI Assistant":
    st.header("🤖 AI YouTube Assistant")
    st.markdown("💬 Chat with your LangChain agent. It can analyze comments, list them, and **reply directly** to users.")
    from agent import agent_executor
    import os

    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.info("⚠️ The first agent action will open a popup Google Login if you aren't authorized.")
    with col2:
        if st.button("🔄 Force Re-Login"):
            if os.path.exists("token.pickle"):
                os.remove("token.pickle")
            # Clear youtube_api's global variable by reloading module or just giving user feedback
            import youtube_api
            youtube_api._youtube_service = None
            st.success("Auth cleared! Next search will re-prompt.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        role = "assistant" if isinstance(msg, AIMessage) else "user"
        with st.chat_message(role):
            st.markdown(msg.content)


    if prompt := st.chat_input("E.g., Analyze the latest video on my channel..."):
        # UI only gets the clean user prompt
        st.session_state.messages.append(HumanMessage(content=prompt))
        
        with st.chat_message("user"):
            st.markdown(prompt)

        # Under the hood, inject context into the prompt
        augmented_prompt = prompt
        # We always enforce the active channel_id so the AI NEVER forgets it across long threads
        augmented_prompt += f"\n\n[System Note: The active channel ID selected by the user is '{channel_id}'. Implicitly use this for tasks unless asked otherwise.]"

        with st.chat_message("assistant"):
            with st.spinner("Agent is working..."):
                try:
                    # Agent invoke using memory configuration, passing ONLY the new augmented message
                    config = {"configurable": {"thread_id": "youtube_agent_session"}}
                    response = agent_executor.invoke({
                        "messages": [HumanMessage(content=augmented_prompt)]
                    }, config=config)

                    # Iterate over the messages that happened AFTER the last human interaction
                    # so we don't repeat toasts for old actions.
                    last_user_idx = len(response["messages"]) - 1
                    while last_user_idx >= 0 and not isinstance(response["messages"][last_user_idx], HumanMessage):
                        last_user_idx -= 1

                    new_messages = response["messages"][last_user_idx:]
                    for msg in new_messages:
                        if isinstance(msg, ToolMessage):
                            if msg.name in ["post_comment_reply", "post_top_level_comment"]:
                                st.success(f"✅ Action Executed -> Result: {msg.content}")
                            else:
                                st.toast(f"🤖 Tool Executed: {msg.name}")
                                
                    bot_msg = response["messages"][-1]
                    st.markdown(bot_msg.content)
                    st.session_state.messages.append(bot_msg)
                except Exception as e:
                    reason = str(e)
                    st.error(f"Error during agent execution: {reason}")
                    if "Missing client_secret.json" in reason:
                        st.error("Please download 'client_secret.json' from Google Cloud Console and place it in the project root.")