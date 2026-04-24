"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getDrafts, publishPost, schedulePost, getToken } from "@/lib/api";
import Link from "next/link";

type Draft = { id: string; content: string; created_at: string };

export default function DraftsPage() {
  const router = useRouter();
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [loading, setLoading] = useState(true);
  const [schedulingId, setSchedulingId] = useState<string | null>(null);
  const [scheduleDate, setScheduleDate] = useState("");
  const [statusMsg, setStatusMsg] = useState<{ id: string; msg: string } | null>(null);

  useEffect(() => {
    if (!getToken()) { router.push("/"); return; }
    getDrafts().then(setDrafts).finally(() => setLoading(false));
  }, [router]);

  async function handlePublish(id: string) {
    try {
      await publishPost(id);
      setStatusMsg({ id, msg: "Published to LinkedIn!" });
      setDrafts((d) => d.filter((p) => p.id !== id));
    } catch {
      setStatusMsg({ id, msg: "Failed to publish. Try again." });
    }
  }

  async function handleSchedule(id: string) {
    if (!scheduleDate) return;
    try {
      await schedulePost(id, scheduleDate);
      setStatusMsg({ id, msg: `Scheduled for ${new Date(scheduleDate).toLocaleString()}` });
      setDrafts((d) => d.filter((p) => p.id !== id));
      setSchedulingId(null);
    } catch {
      setStatusMsg({ id, msg: "Failed to schedule. Try again." });
    }
  }

  return (
    <div className="min-h-screen">
      <nav className="flex items-center justify-between border-b border-gray-800 bg-gray-900 px-6 py-4">
        <h1 className="font-semibold text-white">Drafts</h1>
        <div className="flex gap-4">
          <Link href="/chat" className="text-sm text-gray-400 hover:text-white transition">Chat</Link>
          <Link href="/analytics" className="text-sm text-gray-400 hover:text-white transition">Analytics</Link>
          <Link href="/profile" className="text-sm text-gray-400 hover:text-white transition">Profile</Link>
        </div>
      </nav>

      <div className="mx-auto max-w-2xl px-4 py-8">
        {loading && <p className="text-gray-500">Loading drafts...</p>}

        {!loading && drafts.length === 0 && (
          <div className="rounded-xl border border-gray-800 bg-gray-900 p-8 text-center">
            <p className="text-gray-400">No drafts yet.</p>
            <Link href="/chat" className="mt-4 inline-block text-sm text-blue-400 hover:text-blue-300">
              Ask the agent to write one →
            </Link>
          </div>
        )}

        <div className="space-y-6">
          {drafts.map((draft) => (
            <div key={draft.id} className="rounded-xl border border-gray-800 bg-gray-900 p-6">
              <p className="mb-4 whitespace-pre-wrap text-sm leading-relaxed text-gray-200">
                {draft.content}
              </p>
              <p className="mb-4 text-xs text-gray-600">
                Created {new Date(draft.created_at).toLocaleDateString()}
              </p>

              {statusMsg?.id === draft.id && (
                <p className="mb-3 text-sm text-green-400">{statusMsg.msg}</p>
              )}

              <div className="flex flex-wrap gap-3">
                <button
                  onClick={() => handlePublish(draft.id)}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 transition"
                >
                  Publish Now
                </button>
                <button
                  onClick={() => setSchedulingId(schedulingId === draft.id ? null : draft.id)}
                  className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:border-gray-500 transition"
                >
                  Schedule
                </button>
              </div>

              {schedulingId === draft.id && (
                <div className="mt-4 flex gap-3">
                  <input
                    type="datetime-local"
                    value={scheduleDate}
                    onChange={(e) => setScheduleDate(e.target.value)}
                    className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none"
                  />
                  <button
                    onClick={() => handleSchedule(draft.id)}
                    className="rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-500 transition"
                  >
                    Confirm
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
