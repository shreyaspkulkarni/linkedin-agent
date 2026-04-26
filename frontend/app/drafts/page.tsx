"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getDrafts, getToken } from "@/lib/api";
import Link from "next/link";

type Draft = { id: string; content: string; created_at: string };

export default function DraftsPage() {
  const router = useRouter();
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) { router.push("/"); return; }
    getDrafts().then(setDrafts).finally(() => setLoading(false));
  }, [router]);


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


              <p className="text-xs text-gray-600 italic">
                Publishing is disabled in the demo — copy the draft and post it manually on LinkedIn.
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
