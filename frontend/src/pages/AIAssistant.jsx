import React, { useState, useRef, useEffect } from 'react';

export default function AIAssistant({ channelId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || !channelId) return;

    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      const res = await fetch(`http://localhost:8000/api/agent/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg, channel_id: channelId })
      });

      if (!res.ok) throw new Error("Agent failed to respond.");
      const data = await res.json();
      
      if (data.events && data.events.length > 0) {
        setMessages(prev => [...prev, ...data.events]);
      }
      
      setMessages(prev => [...prev, { role: 'assistant', content: data.reply }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'system', content: `Error: ${err.message}`, isError: true }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] bg-surface/30 rounded-2xl border border-slate-800 shadow-2xl overflow-hidden animate-fade-in relative">
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-1 bg-gradient-to-r from-transparent via-primary to-transparent opacity-50"></div>
      
      <div className="p-6 border-b border-slate-800 bg-surface/80 backdrop-blur-md flex justify-between items-center z-10">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            🤖 <span className="bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">AI Assistant</span>
          </h2>
          <p className="text-sm text-slate-400 mt-1">Chat with your LangChain agent. It can analyze comments and reply directly.</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 space-y-4">
            <div className="text-6xl mb-2">💬</div>
            <p>Start a conversation. For example:</p>
            <div className="flex gap-2 flex-wrap justify-center max-w-lg">
              <span className="px-3 py-1 bg-slate-800 rounded-full text-xs">Analyze my latest video</span>
              <span className="px-3 py-1 bg-slate-800 rounded-full text-xs">Find spam comments</span>
              <span className="px-3 py-1 bg-slate-800 rounded-full text-xs">List my recent videos</span>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : msg.role === 'system' ? 'justify-center' : 'justify-start'} animate-fade-in`}>
            {msg.role === 'system' ? (
              <div className={`px-4 py-1.5 rounded-full text-xs font-mono border ${msg.isError ? 'bg-red-500/10 text-red-400 border-red-500/20' : 'bg-primary/10 text-primary border-primary/20'}`}>
                {msg.content}
              </div>
            ) : (
              <div className={`max-w-[80%] rounded-2xl px-5 py-3 shadow-lg ${
                msg.role === 'user' 
                  ? 'bg-gradient-to-br from-primary to-blue-600 text-white rounded-br-none' 
                  : 'bg-slate-800 text-slate-200 border border-slate-700 rounded-bl-none whitespace-pre-wrap'
              }`}>
                {msg.content}
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-800 border border-slate-700 text-slate-400 rounded-2xl rounded-bl-none px-5 py-3 shadow-lg flex items-center gap-2">
              <div className="w-2 h-2 bg-primary rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{animationDelay: '0.4s'}}></div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSend} className="p-4 bg-surface/80 backdrop-blur-md border-t border-slate-800 z-10">
        <div className="flex gap-4 max-w-4xl mx-auto">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            placeholder={channelId ? "Type your message..." : "Enter Channel ID in sidebar first!"}
            className="flex-1 bg-slate-900 border border-slate-700 focus:border-primary focus:ring-1 focus:ring-primary rounded-xl px-4 py-3 text-slate-200 placeholder-slate-500 outline-none transition-all disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !channelId || !input.trim()}
            className="px-6 py-3 bg-primary hover:bg-blue-600 text-white font-bold rounded-xl shadow-[0_0_15px_rgba(59,130,246,0.3)] hover:shadow-[0_0_25px_rgba(59,130,246,0.5)] transition-all disabled:opacity-50 disabled:shadow-none flex items-center justify-center min-w-[100px]"
          >
            {loading ? <div className="animate-spin h-5 w-5 border-2 border-white/20 border-t-white rounded-full"></div> : 'Send 🚀'}
          </button>
        </div>
      </form>
    </div>
  );
}
