import React from 'react';

const navItems = [
  { id: 'Overview', icon: '📊' },
  { id: 'Comment Analysis', icon: '💬' },
  { id: 'Transcript Analysis', icon: '🎙️' },
  { id: 'AI Assistant', icon: '🤖' },
  { id: 'Competitor Analysis', icon: '🕵️' },
];

export default function Sidebar({ activePage, setActivePage, channelId, setChannelId }) {
  return (
    <div className="w-72 bg-surface border-r border-slate-800 flex flex-col p-6 space-y-8 z-10 shadow-xl">
      <div className="flex items-center space-x-3">
        <div className="text-3xl">📊</div>
        <h1 className="text-xl font-bold tracking-wide">YT Analyst</h1>
      </div>

      <div className="space-y-2">
        <label className="text-xs font-semibold text-textMuted uppercase tracking-wider ml-1">Channel ID</label>
        <input 
          type="text" 
          placeholder="e.g. UCX6OQ3DkcsbYNE6H8uQQuVA"
          value={channelId}
          onChange={(e) => setChannelId(e.target.value)}
          className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary transition-all duration-300"
        />
      </div>

      <nav className="flex-1 space-y-2">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActivePage(item.id)}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 font-medium ${
              activePage === item.id 
                ? 'bg-primary/20 text-primary border border-primary/30 shadow-[0_0_15px_rgba(59,130,246,0.15)]' 
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
            }`}
          >
            <span className="text-lg">{item.icon}</span>
            <span>{item.id}</span>
          </button>
        ))}
      </nav>
      
      <div className="pt-4 border-t border-slate-800 text-xs text-center text-slate-500">
        AI-Powered Automation
      </div>
    </div>
  );
}
