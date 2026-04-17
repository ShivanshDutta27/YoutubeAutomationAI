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
