"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getProfile, getToken, sendMessage } from "@/lib/api";
import Link from "next/link";

export default function ProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<Record<string, string> | null>(null);
  const [audit, setAudit] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [auditing, setAuditing] = useState(false);

  useEffect(() => {
    if (!getToken()) { router.push("/"); return; }
    getProfile()
      .then(setProfile)
      .finally(() => setLoading(false));
  }, [router]);

  async function handleAudit() {
    setAuditing(true);
    const { response } = await sendMessage(
      "Fetch my LinkedIn profile and give me a prioritized list of improvements I should make right now."
    );
    setAudit(response);
    setAuditing(false);
  }

  return (
    <div className="min-h-screen">
      <nav className="flex items-center justify-between border-b border-gray-800 bg-gray-900 px-6 py-4">
        <h1 className="font-semibold text-white">Profile</h1>
        <div className="flex gap-4">
          <Link href="/chat" className="text-sm text-gray-400 hover:text-white transition">Chat</Link>
          <Link href="/drafts" className="text-sm text-gray-400 hover:text-white transition">Drafts</Link>
        </div>
      </nav>

      <div className="mx-auto max-w-2xl px-4 py-8 space-y-6">
        {loading && <p className="text-gray-500">Loading profile...</p>}

        {profile && (
          <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
            <div className="flex items-center gap-4 mb-4">
              {profile.picture && (
                <img src={profile.picture} alt="Profile" className="h-14 w-14 rounded-full" />
              )}
              <div>
                <h2 className="text-lg font-semibold text-white">{profile.name}</h2>
                <p className="text-sm text-gray-400">{profile.email}</p>
              </div>
            </div>
          </div>
        )}

        <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
          <h3 className="mb-3 font-semibold text-white">AI Profile Audit</h3>
          <p className="mb-4 text-sm text-gray-400">
            The agent will fetch your live profile and tell you exactly what to improve.
          </p>
          <button
            onClick={handleAudit}
            disabled={auditing}
            className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-semibold text-white hover:bg-blue-500 transition disabled:opacity-40"
          >
            {auditing ? "Analyzing..." : "Run Profile Audit"}
          </button>

          {audit && (
            <div className="mt-6 whitespace-pre-wrap text-sm leading-relaxed text-gray-200 border-t border-gray-800 pt-6">
              {audit}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
