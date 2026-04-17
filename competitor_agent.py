from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from youtube_api import search_channels_by_niche
from langgraph.checkpoint.memory import MemorySaver

llm = ChatOllama(model="llama3.2", temperature=0)
memory = MemorySaver()

@tool
def find_niche_channels(niche: str):
    """Searches YouTube for popular channels in a given niche or topic. Returns a list of channels with title, ID, and description."""
    channels = search_channels_by_niche(niche, max_results=5)
    if not channels:
        return "No channels found for this niche."
    return channels

tools = [find_niche_channels]

system_prompt = """You are an expert YouTube Competitor Discovery Agent.
Your job is to help users find competitors in a specific niche. 
If the user tells you their niche, you must use the `find_niche_channels` tool to discover 3-5 popular channels.
Once you have the channels, summarize them nicely for the user and ask them to select one or provide a different niche.
Make sure you include the channel names and a very brief explanation of what they do.
DO NOT guess channel names. ONLY return data that you fetched using your tools.
"""

competitor_agent_executor = create_react_agent(llm, tools, prompt=system_prompt, checkpointer=memory)
