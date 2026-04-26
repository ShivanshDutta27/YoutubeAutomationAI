from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import tempfile
import os
import math
import shutil

# Import from backend logic
from backend.youtube_api import get_videos, get_comments, get_video_stats, get_video_transcript, resolve_channel, get_channel_stats
from backend.analysis import analyze_comments, analyze_transcript, analyze_channel_strategy
from backend.agent import agent_executor
from backend.competitor_agent import competitor_agent_executor
from langchain_core.messages import HumanMessage

app = FastAPI(title="YouTube AI Analyst API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class VideoStatsRequest(BaseModel):
    video_ids: List[str]

class AnalyzeCommentsRequest(BaseModel):
    comments: List[Dict[str, Any]]

class AnalyzeTranscriptRequest(BaseModel):
    transcript: str

class ChatRequest(BaseModel):
    message: str
    channel_id: str
    thread_id: str = "youtube_agent_session"

class CompetitorChatRequest(BaseModel):
    message: str
    thread_id: str = "competitor_thread_1"

class CompetitorAnalyzeRequest(BaseModel):
    channel_stats: Dict[str, Any]
    recent_videos: List[Dict[str, Any]]

@app.get("/api/videos/{channel_id}")
def api_get_videos(channel_id: str):
    videos = get_videos(channel_id)
    if not videos:
        raise HTTPException(status_code=404, detail="No videos found")
    return {"videos": videos}

@app.post("/api/videos/stats")
def api_get_video_stats(req: VideoStatsRequest):
    stats = get_video_stats(req.video_ids)
    return {"stats": stats}

@app.get("/api/comments/{video_id}")
def api_get_comments(video_id: str):
    comments = get_comments(video_id)
    if comments is None:
        return {"comments": []}
    return {"comments": comments}

@app.post("/api/analyze/comments")
def api_analyze_comments(req: AnalyzeCommentsRequest):
    result = analyze_comments(req.comments)
    return {"analysis": result}

@app.get("/api/transcript/{video_id}")
def api_get_transcript(video_id: str):
    transcript = get_video_transcript(video_id)
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return {"transcript": transcript}

@app.post("/api/transcript/upload")
async def api_upload_transcript(file: UploadFile = File(...)):
    if not file.filename.endswith((".mp4", ".mov")):
        raise HTTPException(status_code=400, detail="Only MP4 or MOV files are supported")
    
    import speech_recognition as sr
    from moviepy import VideoFileClip
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_mp4:
        shutil.copyfileobj(file.file, tmp_mp4)
        tmp_mp4_path = tmp_mp4.name
        
    tmp_wav_path = tmp_mp4_path.replace(".mp4", ".wav")
    
    try:
        video_clip = VideoFileClip(tmp_mp4_path)
        audio_clip = video_clip.audio
        if audio_clip is None:
            raise HTTPException(status_code=400, detail="Uploaded video has no audio track")
        audio_clip.write_audiofile(tmp_wav_path, logger=None)
        
        recognizer = sr.Recognizer()
        chunk_duration = 30
        total_duration = audio_clip.duration
        chunks = math.ceil(total_duration / chunk_duration)
        
        full_transcript = []
        with sr.AudioFile(tmp_wav_path) as source:
            for i in range(chunks):
                audio_data = recognizer.record(source, duration=chunk_duration)
                try:
                    text = recognizer.recognize_google(audio_data)
                    full_transcript.append(text)
                except sr.UnknownValueError:
                    pass
                    
        transcript_text = " ".join(full_transcript)
        return {"transcript": transcript_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try: video_clip.close()
        except: pass
        if os.path.exists(tmp_mp4_path):
            try: os.remove(tmp_mp4_path)
            except: pass
        if os.path.exists(tmp_wav_path):
            try: os.remove(tmp_wav_path)
            except: pass

@app.post("/api/analyze/transcript")
def api_analyze_transcript(req: AnalyzeTranscriptRequest):
    result = analyze_transcript(req.transcript)
    return {"analysis": result}

@app.post("/api/agent/chat")
def api_agent_chat(req: ChatRequest):
    augmented_prompt = req.message
    augmented_prompt += f"\n\n[System Note: The active channel ID selected by the user is '{req.channel_id}'. Implicitly use this for tasks unless asked otherwise.]"
    
    config = {"configurable": {"thread_id": req.thread_id}}
    try:
        response = agent_executor.invoke({
            "messages": [HumanMessage(content=augmented_prompt)]
        }, config=config)
        
        # Get new messages
        new_messages = []
        for msg in response["messages"]:
            if getattr(msg, "name", "") in ["post_comment_reply", "post_top_level_comment"] and getattr(msg, "content", ""):
                new_messages.append({"role": "system", "content": f"Action Executed: {msg.content}"})
            elif getattr(msg, "name", ""):
                new_messages.append({"role": "system", "content": f"Tool Executed: {msg.name}"})
        
        bot_msg = response["messages"][-1]
        return {"reply": bot_msg.content, "events": new_messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/competitor/resolve")
def api_competitor_resolve(query: str):
    cid = resolve_channel(query)
    if not cid:
        raise HTTPException(status_code=404, detail="Channel not found")
    return {"channel_id": cid}

@app.get("/api/competitor/stats/{channel_id}")
def api_competitor_stats(channel_id: str):
    c_stats = get_channel_stats(channel_id)
    if not c_stats:
        raise HTTPException(status_code=404, detail="Stats not found")
    recent_vids = get_videos(channel_id)
    return {"stats": c_stats, "recent_videos": recent_vids}

@app.post("/api/competitor/analyze")
def api_competitor_analyze(req: CompetitorAnalyzeRequest):
    insights = analyze_channel_strategy(req.channel_stats, req.recent_videos)
    return {"analysis": insights}

@app.post("/api/competitor/chat")
def api_competitor_chat(req: CompetitorChatRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    try:
        response = competitor_agent_executor.invoke({"messages": [HumanMessage(content=req.message)]}, config=config)
        bot_msg = response["messages"][-1]
        return {"reply": bot_msg.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
