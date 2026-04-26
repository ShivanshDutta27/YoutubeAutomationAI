import React, { useState, useEffect } from 'react';

export default function TranscriptAnalysis({ channelId }) {
  const [sourceType, setSourceType] = useState('url'); // 'url', 'recent', 'upload'
  const [videos, setVideos] = useState([]);
  const [selectedVideo, setSelectedVideo] = useState('');
  const [url, setUrl] = useState('');
  const [file, setFile] = useState(null);
  
  const [transcript, setTranscript] = useState('');
  const [analysis, setAnalysis] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (sourceType === 'recent' && channelId) {
      fetch(`http://localhost:8000/api/videos/${channelId}`)
        .then(res => res.json())
        .then(data => {
          setVideos(data.videos || []);
          if (data.videos.length > 0) setSelectedVideo(data.videos[0].video_id);
        })
        .catch(err => console.error(err));
    }
  }, [sourceType, channelId]);

  const fetchTranscriptApi = async (vid) => {
    const res = await fetch(`http://localhost:8000/api/transcript/${vid}`);
    if (!res.ok) throw new Error("Could not fetch transcript. The video might not have captions.");
    const data = await res.json();
    return data.transcript;
  };

  const handleFetchTranscript = async () => {
    setLoading(true);
    setError('');
    setTranscript('');
    setAnalysis('');
    
    try {
      let result = '';
      if (sourceType === 'recent') {
        if (!selectedVideo) throw new Error("No video selected");
        result = await fetchTranscriptApi(selectedVideo);
      } else if (sourceType === 'url') {
        const match = url.match(/(?:v=|\/)([0-9A-Za-z_-]{11}).*/);
        if (!match) throw new Error("Invalid YouTube URL.");
        result = await fetchTranscriptApi(match[1]);
      } else if (sourceType === 'upload') {
        if (!file) throw new Error("Please select a file.");
        const formData = new FormData();
        formData.append("file", file);
        const res = await fetch(`http://localhost:8000/api/transcript/upload`, {
          method: 'POST',
          body: formData
        });
        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.detail || "Upload failed");
        }
        const data = await res.json();
        result = data.transcript;
      }
      setTranscript(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!transcript) return;
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`http://localhost:8000/api/analyze/transcript`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript })
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
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-3xl font-bold">🎙️ Transcript Analysis</h2>
          <p className="text-slate-400 mt-1">Analyze the script and pacing of a video using AI.</p>
        </div>
      </div>

      <div className="bg-surface/50 border border-slate-700/50 rounded-2xl p-6 shadow-xl space-y-6">
        <div className="flex space-x-4 mb-6">
          {['url', 'recent', 'upload'].map(type => (
            <button
              key={type}
              onClick={() => setSourceType(type)}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${sourceType === type ? 'bg-primary text-white shadow-lg shadow-primary/30' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}
            >
              {type === 'url' && 'YouTube URL'}
              {type === 'recent' && 'Recent Video'}
              {type === 'upload' && 'Upload MP4'}
            </button>
          ))}
        </div>

        <div className="p-4 bg-slate-900 rounded-xl border border-slate-700/50">
          {sourceType === 'url' && (
            <input 
              type="text" 
              placeholder="https://youtube.com/watch?v=..."
              value={url}
              onChange={e => setUrl(e.target.value)}
              className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-3 text-slate-200 focus:border-primary focus:outline-none"
            />
          )}
          {sourceType === 'recent' && (
            <select 
              value={selectedVideo}
              onChange={e => setSelectedVideo(e.target.value)}
              className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-3 text-slate-200 focus:border-primary focus:outline-none appearance-none"
            >
              {videos.length === 0 && <option>No videos loaded...</option>}
              {videos.map(v => <option key={v.video_id} value={v.video_id}>{v.title}</option>)}
            </select>
          )}
          {sourceType === 'upload' && (
            <input 
              type="file" 
              accept="video/mp4,video/quicktime"
              onChange={e => setFile(e.target.files[0])}
              className="w-full text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-primary file:text-white hover:file:bg-blue-600 transition-colors"
            />
          )}
        </div>

        {error && <div className="text-red-400 bg-red-500/20 p-3 rounded-lg border border-red-500/30">{error}</div>}

        <button
          onClick={handleFetchTranscript}
          disabled={loading}
          className="w-full py-3 bg-gradient-to-r from-accent to-purple-600 hover:from-accent hover:to-purple-500 text-white font-bold rounded-xl shadow-lg transition-all disabled:opacity-50"
        >
          {loading ? 'Processing...' : 'Fetch & Process Transcript'}
        </button>
      </div>

      {transcript && (
        <div className="space-y-6 animate-fade-in">
          <div className="bg-surface/50 border border-slate-700/50 rounded-2xl p-6 shadow-xl">
            <h3 className="text-lg font-bold mb-3 flex items-center justify-between">
              <span>📝 Transcript Snippet</span>
              <button 
                onClick={handleAnalyze}
                disabled={loading}
                className="text-sm px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                Analyze Content
              </button>
            </h3>
            <div className="bg-slate-900 border border-slate-700/50 rounded-xl p-4 text-slate-400 text-sm h-48 overflow-y-auto leading-relaxed">
              {transcript}
            </div>
          </div>

          {analysis && (
            <div className="bg-surface/50 border border-slate-700/50 rounded-2xl p-6 shadow-xl border-l-4 border-l-primary">
              <h3 className="text-xl font-bold text-primary mb-4">🤖 AI Content Analysis</h3>
              <div className="text-slate-300 leading-relaxed whitespace-pre-wrap">
                {analysis}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
