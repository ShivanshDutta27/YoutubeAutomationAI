import React, { useState, useRef, useEffect } from 'react';

export default function CompetitorAnalysis() {
  const [inputType, setInputType] = useState('direct'); // 'direct', 'ai'
  const [query, setQuery] = useState('');
  const [compId, setCompId] = useState('');
  
  // Dashboard state
  const [stats, setStats] = useState(null);
  const [recentVids, setRecentVids] = useState([]);
  const [analysis, setAnalysis] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // AI Chat state
  const [messages, setMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (inputType === 'ai') {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, inputType, chatLoading]);

  const handleResolve = async () => {
    if (!query) return;
    setLoading(true); setError(''); setStats(null); setAnalysis('');
    try {
      const res = await fetch(`http://localhost:8000/api/competitor/resolve?query=${encodeURIComponent(query)}`);
      if (!res.ok) throw new Error("Could not resolve channel.");
      const data = await res.json();
      setCompId(data.channel_id);
      await fetchDashboard(data.channel_id);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleManualSetId = async () => {
    if (!compId) return;
    setLoading(true); setError(''); setStats(null); setAnalysis('');
    try {
      await fetchDashboard(compId);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchDashboard = async (cid) => {
    const res = await fetch(`http://localhost:8000/api/competitor/stats/${cid}`);
    if (!res.ok) throw new Error("Could not fetch stats.");
    const data = await res.json();
    setStats(data.stats);
    setRecentVids(data.recent_videos || []);
  };

  const handleAnalyzeStrategy = async () => {
    setLoading(true); setError('');
    try {
      const res = await fetch(`http://localhost:8000/api/competitor/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channel_stats: stats, recent_videos: recentVids })
      });
      if (!res.ok) throw new Error("Analysis failed");
      const data = await res.json();
      setAnalysis(data.analysis);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleChat = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    const userMsg = chatInput.trim();
    setChatInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setChatLoading(true);
    
    try {
      const res = await fetch(`http://localhost:8000/api/competitor/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg })
      });
      if (!res.ok) throw new Error("Chat failed");
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.reply }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'system', content: `Error: ${err.message}` }]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-3xl font-bold">🕵️ Competitor Analysis</h2>
        <p className="text-slate-400 mt-1">Analyze competitors by directly entering their info or letting AI find them.</p>
      </div>

      <div className="flex space-x-4">
        <button
          onClick={() => setInputType('direct')}
          className={`px-6 py-3 rounded-xl font-bold transition-all ${inputType === 'direct' ? 'bg-primary text-white shadow-lg shadow-primary/30' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}
        >
          Direct Input
        </button>
        <button
          onClick={() => setInputType('ai')}
          className={`px-6 py-3 rounded-xl font-bold transition-all ${inputType === 'ai' ? 'bg-accent text-white shadow-lg shadow-accent/30' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}
        >
          AI Discovery
        </button>
      </div>

      {inputType === 'direct' ? (
        <div className="bg-surface/50 border border-slate-700/50 rounded-2xl p-6 shadow-xl flex gap-4">
          <input 
            type="text" 
            placeholder="Enter YouTube Channel URL or Handle (e.g. @MrBeast)"
            value={query}
            onChange={e => setQuery(e.target.value)}
            className="flex-1 bg-slate-900 border border-slate-600 rounded-xl px-4 py-3 focus:border-primary focus:outline-none transition-colors"
          />
          <button 
            onClick={handleResolve}
            disabled={loading || !query}
            className="px-6 py-3 bg-primary hover:bg-blue-600 text-white font-bold rounded-xl disabled:opacity-50 transition-colors whitespace-nowrap"
          >
            {loading ? 'Searching...' : 'Find Channel'}
          </button>
        </div>
      ) : (
        <div className="bg-surface/50 border border-slate-700/50 rounded-2xl shadow-xl flex flex-col h-[500px]">
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-slate-500 mt-10">
                Ask the AI to find competitors. E.g., 'Find tech review channels'
              </div>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] rounded-2xl px-5 py-3 ${msg.role === 'user' ? 'bg-accent text-white rounded-br-none' : 'bg-slate-800 text-slate-200 rounded-bl-none border border-slate-700 whitespace-pre-wrap'}`}>
                  {msg.content}
                </div>
              </div>
            ))}
            {chatLoading && <div className="text-slate-500 text-sm italic">AI is thinking...</div>}
            <div ref={messagesEndRef} />
          </div>
          <form onSubmit={handleChat} className="p-4 border-t border-slate-800 bg-slate-900/50 flex gap-4">
            <input 
              type="text" 
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              placeholder="What is your niche?"
              className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 focus:border-accent focus:outline-none"
            />
            <button type="submit" disabled={chatLoading} className="px-6 py-3 bg-accent hover:bg-purple-600 text-white font-bold rounded-xl disabled:opacity-50 transition-colors">
              Send
            </button>
          </form>
          <div className="p-4 bg-slate-800/80 border-t border-slate-700 flex gap-4 items-center">
            <span className="text-sm text-slate-400 whitespace-nowrap">Found an ID?</span>
            <input 
              type="text" 
              placeholder="Enter Channel ID here"
              value={compId}
              onChange={e => setCompId(e.target.value)}
              className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:border-primary focus:outline-none"
            />
            <button onClick={handleManualSetId} disabled={loading || !compId} className="px-4 py-2 bg-primary hover:bg-blue-600 text-white text-sm font-bold rounded-lg disabled:opacity-50 transition-colors">
              Load Dash
            </button>
          </div>
        </div>
      )}

      {error && <div className="p-4 bg-red-500/20 text-red-400 rounded-xl border border-red-500/30">{error}</div>}

      {stats && (
        <div className="space-y-6 animate-fade-in mt-12">
          <h3 className="text-2xl font-bold border-b border-slate-800 pb-2">📊 Competitor Dashboard</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-slate-800/50 p-6 rounded-2xl border border-slate-700 text-center">
              <div className="text-slate-400 text-sm uppercase mb-1">Subscribers</div>
              <div className="text-3xl font-bold text-white">{parseInt(stats.subscriberCount || 0).toLocaleString()}</div>
            </div>
            <div className="bg-slate-800/50 p-6 rounded-2xl border border-slate-700 text-center">
              <div className="text-slate-400 text-sm uppercase mb-1">Total Views</div>
              <div className="text-3xl font-bold text-white">{parseInt(stats.viewCount || 0).toLocaleString()}</div>
            </div>
            <div className="bg-slate-800/50 p-6 rounded-2xl border border-slate-700 text-center">
              <div className="text-slate-400 text-sm uppercase mb-1">Total Videos</div>
              <div className="text-3xl font-bold text-white">{parseInt(stats.videoCount || 0).toLocaleString()}</div>
            </div>
          </div>

          <div className="bg-slate-800/30 p-6 rounded-2xl border border-slate-700/50">
            <p className="text-slate-300 text-sm leading-relaxed">{stats.description?.slice(0, 300)}...</p>
          </div>

          <div className="bg-surface/50 border border-slate-700/50 rounded-2xl p-6 shadow-xl">
            <div className="flex justify-between items-center mb-6">
              <h4 className="text-xl font-bold">🎯 Strategy Insights</h4>
              <button 
                onClick={handleAnalyzeStrategy}
                disabled={loading}
                className="px-4 py-2 bg-gradient-to-r from-accent to-primary text-white font-bold rounded-lg shadow-lg hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                {loading ? 'Analyzing...' : 'Generate Analysis'}
              </button>
            </div>
            
            {analysis && (
              <div className="bg-slate-900 border border-slate-700/50 p-6 rounded-xl text-slate-300 leading-relaxed whitespace-pre-wrap shadow-inner animate-fade-in mb-6">
                {analysis}
              </div>
            )}

            <h5 className="font-bold text-slate-400 mb-3 uppercase tracking-wide text-sm">Recent Videos</h5>
            <div className="grid gap-3">
              {recentVids.slice(0, 5).map(v => (
                <div key={v.video_id} className="bg-slate-800/50 px-4 py-3 rounded-lg border border-slate-700 flex items-center space-x-3">
                  <span className="text-xl">🎥</span>
                  <span className="text-slate-200">{v.title}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
