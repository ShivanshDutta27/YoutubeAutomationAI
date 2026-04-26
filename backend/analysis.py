from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

llm = OllamaLLM(model="llama3.2")

prompt = PromptTemplate.from_template("""
You are a sharp YouTube growth strategist.

Analyze the following comments:

{comments}

Return output STRICTLY in this format:

LIKES:
- (specific things users liked)

DISLIKES:
- (specific complaints or issues)

PATTERNS:
- (repeat themes, words, behavior)

VIDEO IDEAS:
- (5 very specific video ideas, not generic)

CREATOR ADVICE:
- (actionable improvements)

IMPORTANT:
- Do NOT give generic advice
- Be specific and concrete
""")

def analyze_comments(comments):
    chain = prompt | llm
    if not comments: return "No comments to analyze."
    
    # Check if comments are dicts (new format) or strings (old format fallback)
    text_list = []
    for c in comments:
        if isinstance(c, dict):
            text_list.append(f"{c.get('author', 'User')}: {c.get('text', '')}")
        else:
            text_list.append(str(c))
            
    return chain.invoke({"comments": "\n".join(text_list)})

competitor_prompt = PromptTemplate.from_template("""
You are a sharp YouTube growth strategist.

Analyze the following competitor channel:

CHANNEL INFO:
{channel_info}

TOP RECENT VIDEOS:
{top_videos}

Return output STRICTLY in this format using Markdown:

### 📈 What Works for this Channel
- (Why are people watching? What's the main draw?)
- (Specific hook styles or thumbnail concepts)

### 🧩 Content Patterns
- (Themes in the titles, pacing, or formats)
- (Topics that generate the most interest)

### 💡 Opportunities for You (Content Gaps)
- (1-3 areas where this creator is lacking or not covering)
- (How you can differentiate yourself from them)
""")

def analyze_channel_strategy(channel_info, top_videos):
    chain = competitor_prompt | llm
    
    # Format channel info
    info_text = f"Title: {channel_info.get('title')}\nSubscribers: {channel_info.get('subscriberCount')}\nViews: {channel_info.get('viewCount')}\nDescription: {channel_info.get('description', '')[:500]}"
    
    # Format top videos
    video_text = ""
    for v in top_videos:
        video_text += f"- {v.get('title', '')} ({v.get('viewCount', '0')} views)\n"
        
    return chain.invoke({
        "channel_info": info_text,
        "top_videos": video_text
    })

spam_prompt = PromptTemplate.from_template("""
You are a YouTube comment moderation AI.
Analyze the following comments and identify ANY that are likely spam, bots, self-promotion, or abusive trolls.

Comments:
{comments}

Return output STRICTLY in this JSON format (no backticks or extra text, just a valid JSON array):
[
  {{
    "comment_id": "...",
    "author": "...",
    "text": "...",
    "reason": "Why it is spam/troll"
  }}
]

If none are spam, return an empty array: []
""")

def detect_spam_comments(comments):
    llm_json = OllamaLLM(model="llama3.2", format="json")
    chain = spam_prompt | llm_json
    if not comments: return "[]"
    
    text_list = []
    for c in comments:
        if isinstance(c, dict):
            text_list.append(f"ID: {c.get('comment_id')} | Author: {c.get('author', 'User')} | Text: {c.get('text', '')}")
        else:
            text_list.append(str(c))
            
    return chain.invoke({"comments": "\n".join(text_list)})

transcript_prompt = PromptTemplate.from_template("""
You are an expert YouTube content consultant and video editor.
Analyze the following video transcript:

{transcript}

Return your analysis STRICTLY in this Markdown format:

### ⏱️ Pacing & Flow
- (Analyze if the video drags, repeats itself, or flows well)
- (Specific examples of where the script could be tighter)

### 🎯 Hook & Retention
- (How strong is the intro?)
- (Did they deliver on the title/thumbnail promise quickly?)

### 💡 Content Gaps & Issues
- (Any dead air, unclear explanations, or missing information?)
- (Did they go off-topic?)

### 🚀 Creator Action Items
- (3-5 specific, actionable improvements for their next video)
- (Suggestions for b-roll, graphics, or script changes)

IMPORTANT: Be brutally honest but constructive. Do not use generic advice. Base all feedback specifically on the text provided.
""")

def analyze_transcript(transcript_text):
    if not transcript_text or len(transcript_text.strip()) == 0:
        return "No transcript provided."
        
    chain = transcript_prompt | llm
    
    # If transcript is too long, we might need to truncate it for the LLM context window.
    # Llama3.2 has a decent context window, but we'll cap it just in case.
    # 1 word ~ 1.3 tokens. 8000 tokens ~ 6000 words. Let's cap at 6000 words.
    words = transcript_text.split()
    if len(words) > 6000:
        transcript_text = " ".join(words[:6000]) + "\n...[TRANSCRIPT TRUNCATED FOR LENGTH]"
        
    return chain.invoke({"transcript": transcript_text})
