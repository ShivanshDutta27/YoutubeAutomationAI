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
    ["Overview", "Comment Analysis", "Transcript Analysis", "AI Assistant", "Competitor Analysis"]
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
# 💬 COMMENT ANALYSIS PAGE
# =========================================================
elif page == "Comment Analysis":
    st.header("💬 Comment Analysis")

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
# 🎙️ TRANSCRIPT ANALYSIS PAGE
# =========================================================
elif page == "Transcript Analysis":
    st.header("🎙️ Transcript Analysis")
    st.markdown("Analyze the script and pacing of a video using AI.")
    
    from youtube_api import get_video_transcript
    from analysis import analyze_transcript
    
    source_type = st.radio("How do you want to provide the video?", 
                           ["Select Recent Video", "Direct YouTube URL", "Upload MP4"])
                           
    transcript_text = None
    
    if source_type == "Select Recent Video":
        video_titles = [v["title"] for v in videos]
        selected_title = st.selectbox("Select a video", video_titles)
        if st.button("Fetch Transcript"):
            video = next(v for v in videos if v["title"] == selected_title)
            with st.spinner("Fetching transcript..."):
                transcript_text = get_video_transcript(video["video_id"])
                if not transcript_text:
                    st.error("Could not fetch transcript. The video might not have captions.")
                    
    elif source_type == "Direct YouTube URL":
        url = st.text_input("Enter YouTube Video URL")
        if st.button("Fetch Transcript") and url:
            with st.spinner("Extracting Video ID & Fetching Transcript..."):
                import re
                match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
                if match:
                    vid_id = match.group(1)
                    transcript_text = get_video_transcript(vid_id)
                    if not transcript_text:
                        st.error("Could not fetch transcript. The video might not have captions.")
                else:
                    st.error("Invalid YouTube URL.")
                    
    elif source_type == "Upload MP4":
        uploaded_file = st.file_uploader("Upload an MP4 video", type=["mp4", "mov"])
        if uploaded_file is not None:
            if st.button("Extract & Transcribe"):
                with st.spinner("Extracting Audio & Transcribing via Google Web Speech API..."):
                    import tempfile
                    import os
                    from moviepy import VideoFileClip
                    import speech_recognition as sr
                    import math
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_mp4:
                        tmp_mp4.write(uploaded_file.read())
                        tmp_mp4_path = tmp_mp4.name
                        
                    tmp_wav_path = tmp_mp4_path.replace(".mp4", ".wav")
                    
                    try:
                        st.info("Extracting audio from video...")
                        video_clip = VideoFileClip(tmp_mp4_path)
                        audio_clip = video_clip.audio
                        if audio_clip is None:
                            raise ValueError("The uploaded video does not contain an audio track.")
                        audio_clip.write_audiofile(tmp_wav_path, logger=None)
                        
                        st.info("Audio extracted. Transcribing in chunks...")
                        recognizer = sr.Recognizer()
                        
                        chunk_duration = 30 # seconds
                        total_duration = audio_clip.duration
                        chunks = math.ceil(total_duration / chunk_duration)
                        
                        full_transcript = []
                        my_bar = st.progress(0, text="Transcribing audio chunks...")
                        
                        with sr.AudioFile(tmp_wav_path) as source:
                            for i in range(chunks):
                                audio_data = recognizer.record(source, duration=chunk_duration)
                                try:
                                    text = recognizer.recognize_google(audio_data)
                                    full_transcript.append(text)
                                except sr.UnknownValueError:
                                    pass # Silence or unintelligible
                                my_bar.progress((i + 1) / chunks, text=f"Transcribing part {i+1}/{chunks}...")
                                
                        transcript_text = " ".join(full_transcript)
                        st.success("Transcription complete!")
                        
                    except sr.RequestError as e:
                        st.error(f"Could not request results from Google Speech Recognition service; {e}")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
                    finally:
                        try:
                            video_clip.close()
                        except:
                            pass
                        if os.path.exists(tmp_mp4_path):
                            try: os.remove(tmp_mp4_path)
                            except: pass
                        if os.path.exists(tmp_wav_path):
                            try: os.remove(tmp_wav_path)
                            except: pass

    if transcript_text:
        st.subheader("📝 Transcript Snippet")
        st.text_area("Raw Transcript", transcript_text[:1000] + ("..." if len(transcript_text)>1000 else ""), height=150)
        
        st.divider()
        st.subheader("🤖 AI Content Analysis")
        with st.spinner("AI is analyzing the transcript..."):
            analysis_result = analyze_transcript(transcript_text)
            st.markdown(analysis_result)

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

# =========================================================
# 🕵️ COMPETITOR ANALYSIS PAGE
# =========================================================
elif page == "Competitor Analysis":
    st.header("🕵️ Competitor Analysis")
    st.markdown("Analyze competitors by directly entering their info or letting AI find them for you.")
    
    from youtube_api import resolve_channel, get_channel_stats, get_videos
    from analysis import analyze_channel_strategy
    from competitor_agent import competitor_agent_executor
    from langchain_core.messages import HumanMessage
    
    input_type = st.radio("How do you want to find competitors?", ["Direct Input (URL or Handle)", "AI-Assisted Niche Discovery"])
    
    # We will use st.session_state to store the active competitor ID because Streamlit re-runs on every input
    if "comp_channel_id" not in st.session_state:
        st.session_state.comp_channel_id = None
    
    if input_type == "Direct Input (URL or Handle)":
        query = st.text_input("Enter YouTube Channel URL, Handle (e.g. @MrBeast), or Name")
        if st.button("Find Channel") and query:
            with st.spinner("Resolving channel..."):
                cid = resolve_channel(query)
                if cid:
                    st.success(f"Channel resolved! ID: {cid}")
                    st.session_state.comp_channel_id = cid
                else:
                    st.error("Could not resolve channel. Try a URL or Exact Handle.")
    
    else:
        st.info("Ask the AI to find competitors. E.g., 'Find tech review channels'")
        if "comp_messages" not in st.session_state:
            st.session_state.comp_messages = []
            
        for msg in st.session_state.comp_messages:
            role = "assistant" if isinstance(msg, AIMessage) else "user"
            with st.chat_message(role):
                st.markdown(msg.content)
                
        if prompt := st.chat_input("What is your niche?"):
            st.session_state.comp_messages.append(HumanMessage(content=prompt))
            with st.chat_message("user"):
                st.markdown(prompt)
                
            with st.chat_message("assistant"):
                with st.spinner("Agent is searching..."):
                    config = {"configurable": {"thread_id": "competitor_thread_1"}}
                    response = competitor_agent_executor.invoke({"messages": [HumanMessage(content=prompt)]}, config=config)
                    bot_msg = response["messages"][-1]
                    st.markdown(bot_msg.content)
                    st.session_state.comp_messages.append(bot_msg)
        
        st.divider()
        st.write("Once you find a channel from the list above, enter its ID below:")
        manual_id = st.text_input("Competitor Channel ID")
        if st.button("Set Competitor"):
            st.session_state.comp_channel_id = manual_id
        
    if st.session_state.comp_channel_id:
        st.divider()
        st.subheader("📊 Competitor Dashboard")
        with st.spinner("Fetching channel stats and top videos..."):
            c_stats = get_channel_stats(st.session_state.comp_channel_id)
            if c_stats:
                col1, col2, col3 = st.columns(3)
                col1.metric("Subscribers", f"{c_stats['subscriberCount']:,}")
                col2.metric("Total Views", f"{c_stats['viewCount']:,}")
                col3.metric("Total Videos", f"{c_stats['videoCount']:,}")
                
                st.write(f"**Description:** {c_stats['description'][:300]}...")
                
                st.subheader("🎯 Top Recent Videos")
                recent_vids = get_videos(st.session_state.comp_channel_id)
                for v in recent_vids:
                    st.write(f"- 🎥 {v['title']}")
                
                st.subheader("🧠 Strategy Insights")
                if st.button("Generate Strategy Analysis"):
                    with st.spinner("AI is analyzing competitor strategy..."):
                        insights = analyze_channel_strategy(c_stats, recent_vids)
                        st.markdown(insights)
            else:
                st.warning("Could not fetch stats for this channel. Check the ID.")