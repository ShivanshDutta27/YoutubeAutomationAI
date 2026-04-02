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
