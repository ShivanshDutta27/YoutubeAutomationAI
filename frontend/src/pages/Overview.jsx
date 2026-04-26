import React, { useEffect, useState } from 'react';

export default function Overview({ channelId }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      if (!channelId) return;
      setLoading(true);
      setError(null);
      try {
        const vidRes = await fetch(`http://localhost:8000/api/videos/${channelId}`);
        if (!vidRes.ok) throw new Error('Failed to fetch videos');
        const vidData = await vidRes.json();
        const videos = vidData.videos;

        if (videos.length === 0) {
          setData([]);
          setLoading(false);
          return;
        }

        const vIds = videos.map(v => v.video_id);
        const statsRes = await fetch(`http://localhost:8000/api/videos/stats`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ video_ids: vIds })
        });
        
        if (!statsRes.ok) throw new Error('Failed to fetch stats');
        const statsData = await statsRes.json();
        
        const merged = statsData.stats.items.map(item => {
          const video = videos.find(v => v.video_id === item.id);
          return {
            video_id: item.id,
            title: video ? video.title : 'Unknown',
            views: parseInt(item.statistics.viewCount || '0'),
            likes: parseInt(item.statistics.likeCount || '0'),
          };
        });

        setData(merged);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [channelId]);

  if (loading) return <div className="flex justify-center p-20"><div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div></div>;
  if (error) return <div className="p-4 bg-red-500/20 border border-red-500/50 rounded-xl text-red-400">{error}</div>;

  const totalViews = data.reduce((acc, curr) => acc + curr.views, 0);
  const totalLikes = data.reduce((acc, curr) => acc + curr.likes, 0);

  return (
    <div className="space-y-8 animate-fade-in">
      <h2 className="text-3xl font-bold border-b border-slate-800 pb-4">📊 Channel Overview</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-surface/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-6 shadow-xl flex flex-col items-center justify-center relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
          <span className="text-slate-400 text-sm font-semibold uppercase tracking-wider mb-2">Total Views</span>
          <span className="text-5xl font-black bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-primary">
            {totalViews.toLocaleString()}
          </span>
        </div>
        
        <div className="bg-surface/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-6 shadow-xl flex flex-col items-center justify-center relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-accent/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
          <span className="text-slate-400 text-sm font-semibold uppercase tracking-wider mb-2">Total Likes</span>
          <span className="text-5xl font-black bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-accent">
            {totalLikes.toLocaleString()}
          </span>
        </div>
      </div>

      <div className="bg-surface/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl shadow-xl overflow-hidden">
        <div className="p-6 border-b border-slate-700/50">
          <h3 className="text-xl font-bold">📋 Video Performance</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-800/50 text-slate-400 text-sm uppercase tracking-wider">
                <th className="p-4 font-medium">Title</th>
                <th className="p-4 font-medium">Views</th>
                <th className="p-4 font-medium">Likes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {data.map((row) => (
                <tr key={row.video_id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="p-4 text-slate-200">{row.title}</td>
                  <td className="p-4 text-slate-300 font-mono">{row.views.toLocaleString()}</td>
                  <td className="p-4 text-slate-300 font-mono">{row.likes.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
