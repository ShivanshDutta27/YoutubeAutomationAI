import React, { useState, useEffect } from 'react';

export default function CommentAnalysis({ channelId }) {
  const [videos, setVideos] = useState([]);
  const [selectedVideo, setSelectedVideo] = useState('');
  const [comments, setComments] = useState([]);
  const [analysis, setAnalysis] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchVideos() {
      if (!channelId) return;
      try {
        const res = await fetch(`http://localhost:8000/api/videos/${channelId}`);
        if (res.ok) {
          const data = await res.json();
          setVideos(data.videos || []);
          if (data.videos.length > 0) setSelectedVideo(data.videos[0].video_id);
        }
      } catch (err) {
        console.error(err);
      }
    }
    fetchVideos();
  }, [channelId]);

  useEffect(() => {
    async function fetchComments() {
      if (!selectedVideo) return;
      setLoading(true);
      setError(null);
      setComments([]);
      setAnalysis('');
      try {
        const res = await fetch(`http://localhost:8000/api/comments/${selectedVideo}`);
        if (!res.ok) throw new Error("Failed to fetch comments");
        const data = await res.json();
        setComments(data.comments || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchComments();
  }, [selectedVideo]);

  const handleAnalyze = async () => {
    if (comments.length === 0) return;
    setLoading(true);
    setAnalysis('');
    try {
      const res = await fetch(`http://localhost:8000/api/analyze/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ comments: comments.slice(0, 30) }) // Match app.py logic
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

  return (
    <div className="space-y-8 animate-fade-in">
      <h2 className="text-3xl font-bold border-b border-slate-800 pb-4">💬 Comment Analysis</h2>

      {videos.length === 0 ? (
        <p className="text-slate-400">Loading videos or none found...</p>
      ) : (
        <div className="bg-surface/50 p-6 rounded-2xl border border-slate-700/50 shadow-xl space-y-6">
          <div>
            <label className="block text-sm font-semibold text-textMuted mb-2 uppercase tracking-wide">Select a Video</label>
            <select 
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-slate-200 focus:outline-none focus:border-primary transition-colors appearance-none"
              value={selectedVideo}
              onChange={(e) => setSelectedVideo(e.target.value)}
            >
              {videos.map(v => (
                <option key={v.video_id} value={v.video_id}>{v.title}</option>
              ))}
            </select>
          </div>

          {error && <div className="p-3 bg-red-500/20 text-red-400 rounded-lg border border-red-500/30">{error}</div>}

          <div className="flex items-center justify-between">
            <p className="text-slate-400 font-medium">
              Loaded <span className="text-primary font-bold">{comments.length}</span> comments for this video.
            </p>
            <button 
              onClick={handleAnalyze}
              disabled={loading || comments.length === 0}
              className="px-6 py-3 bg-gradient-to-r from-primary to-blue-600 hover:from-primary hover:to-blue-500 text-white font-bold rounded-xl shadow-lg hover:shadow-primary/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {loading && <div className="animate-spin h-4 w-4 border-2 border-white/20 border-t-white rounded-full"></div>}
              <span>{loading ? 'Analyzing...' : 'Analyze Comments'}</span>
            </button>
          </div>

          {analysis && (
            <div className="mt-8 animate-fade-in">
              <h3 className="text-xl font-bold text-accent mb-4 flex items-center gap-2">
                <span>🧠</span> AI Insights
              </h3>
              <div className="bg-slate-900/80 border border-slate-700/50 p-6 rounded-xl text-slate-300 leading-relaxed whitespace-pre-wrap shadow-inner">
                {analysis}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
