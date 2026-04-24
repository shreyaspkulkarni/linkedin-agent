"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getAnalytics, refreshAnalytics, getToken } from "@/lib/api";

type PostAnalytics = {
  id: string;
  content: string;
  published_at: string;
  likes: number;
  comments: number;
  shares: number;
  impressions: number;
  fetched_at: string | null;
};

export default function AnalyticsPage() {
  const router = useRouter();
  const [posts, setPosts] = useState<PostAnalytics[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshMsg, setRefreshMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) { router.push("/"); return; }
    getAnalytics().then(setPosts).finally(() => setLoading(false));
  }, [router]);

  async function handleRefresh() {
    setRefreshing(true);
    setRefreshMsg(null);
    try {
      const result = await refreshAnalytics();
      setRefreshMsg(`Refreshed data for ${result.refreshed} post${result.refreshed !== 1 ? "s" : ""}.`);
      const updated = await getAnalytics();
      setPosts(updated);
    } catch {
      setRefreshMsg("Failed to refresh. Try again.");
    } finally {
      setRefreshing(false);
    }
  }

  const totalLikes = posts.reduce((s, p) => s + p.likes, 0);
  const totalComments = posts.reduce((s, p) => s + p.comments, 0);
  const totalShares = posts.reduce((s, p) => s + p.shares, 0);

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <nav className="flex items-center justify-between border-b border-gray-800 bg-gray-900 px-6 py-4">
        <h1 className="font-semibold text-white">Analytics</h1>
        <div className="flex gap-4">
          <Link href="/chat" className="text-sm text-gray-400 hover:text-white transition">Chat</Link>
          <Link href="/drafts" className="text-sm text-gray-400 hover:text-white transition">Drafts</Link>
          <Link href="/profile" className="text-sm text-gray-400 hover:text-white transition">Profile</Link>
        </div>
      </nav>

      <div className="mx-auto max-w-3xl px-4 py-8">
        {/* Summary bar */}
        {!loading && posts.length > 0 && (
          <div className="mb-8 grid grid-cols-3 gap-4">
            {[
              { label: "Total Likes", value: totalLikes },
              { label: "Total Comments", value: totalComments },
              { label: "Total Shares", value: totalShares },
            ].map(({ label, value }) => (
              <div key={label} className="rounded-xl border border-gray-800 bg-gray-900 p-4 text-center">
                <p className="text-2xl font-bold text-white">{value}</p>
                <p className="mt-1 text-xs text-gray-500">{label}</p>
              </div>
            ))}
          </div>
        )}

        {/* Refresh button */}
        <div className="mb-6 flex items-center gap-4">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50 transition"
          >
            {refreshing ? "Refreshing..." : "Refresh from LinkedIn"}
          </button>
          {refreshMsg && <p className="text-sm text-gray-400">{refreshMsg}</p>}
        </div>

        {loading && <p className="text-gray-500">Loading...</p>}

        {!loading && posts.length === 0 && (
          <div className="rounded-xl border border-gray-800 bg-gray-900 p-8 text-center">
            <p className="text-gray-400">No published posts yet.</p>
            <Link href="/chat" className="mt-4 inline-block text-sm text-blue-400 hover:text-blue-300">
              Ask the agent to write one →
            </Link>
          </div>
        )}

        <div className="space-y-4">
          {posts.map((post) => (
            <div key={post.id} className="rounded-xl border border-gray-800 bg-gray-900 p-5">
              <p className="mb-3 text-sm leading-relaxed text-gray-300 line-clamp-3">
                {post.content}
              </p>
              <div className="flex items-center justify-between">
                <div className="flex gap-5 text-sm">
                  <span className="text-white font-medium">{post.likes} <span className="text-gray-500 font-normal">likes</span></span>
                  <span className="text-white font-medium">{post.comments} <span className="text-gray-500 font-normal">comments</span></span>
                  <span className="text-white font-medium">{post.shares} <span className="text-gray-500 font-normal">shares</span></span>
                </div>
                <p className="text-xs text-gray-600">
                  {post.published_at ? new Date(post.published_at).toLocaleDateString() : ""}
                  {post.fetched_at ? ` · data from ${new Date(post.fetched_at).toLocaleDateString()}` : " · no data yet"}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
