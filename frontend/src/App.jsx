import { useState } from 'react';
import Sidebar from './components/Sidebar';
import Overview from './pages/Overview';
import CommentAnalysis from './pages/CommentAnalysis';
import TranscriptAnalysis from './pages/TranscriptAnalysis';
import AIAssistant from './pages/AIAssistant';
import CompetitorAnalysis from './pages/CompetitorAnalysis';

function App() {
  const [activePage, setActivePage] = useState('Overview');
  const [channelId, setChannelId] = useState('');

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar 
        activePage={activePage} 
        setActivePage={setActivePage} 
        channelId={channelId}
        setChannelId={setChannelId}
      />
      <main className="flex-1 overflow-y-auto p-8 relative bg-background">
        {/* Glow effect */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[128px] -z-10 pointer-events-none"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-accent/20 rounded-full blur-[128px] -z-10 pointer-events-none"></div>

        {!channelId && activePage !== 'Competitor Analysis' ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              YouTube AI Analyst
            </h1>
            <p className="text-textMuted text-lg">Enter a Channel ID in the sidebar to begin.</p>
          </div>
        ) : (
          <div className="w-full max-w-7xl mx-auto animate-fade-in">
            {activePage === 'Overview' && <Overview channelId={channelId} />}
            {activePage === 'Comment Analysis' && <CommentAnalysis channelId={channelId} />}
            {activePage === 'Transcript Analysis' && <TranscriptAnalysis />}
            {activePage === 'AI Assistant' && <AIAssistant channelId={channelId} />}
            {activePage === 'Competitor Analysis' && <CompetitorAnalysis />}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
