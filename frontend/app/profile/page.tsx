"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getProfile, getProfileData, saveProfileData, importLinkedInExport, getToken, sendMessage } from "@/lib/api";

type BasicProfile = { name?: string; picture?: string; email?: string };
type ProfileData = { headline: string; about: string; experience: string; skills: string; updated_at?: string };

export default function ProfilePage() {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);

  const [basic, setBasic] = useState<BasicProfile | null>(null);
  const [form, setForm] = useState<ProfileData>({ headline: "", about: "", experience: "", skills: "" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [importing, setImporting] = useState(false);
  const [savedMsg, setSavedMsg] = useState<string | null>(null);
  const [audit, setAudit] = useState<string | null>(null);
  const [auditing, setAuditing] = useState(false);

  useEffect(() => {
    if (!getToken()) { router.push("/"); return; }
    Promise.all([getProfile(), getProfileData()])
      .then(([b, p]) => { setBasic(b); setForm(p); })
      .finally(() => setLoading(false));
  }, [router]);

  async function handleSave() {
    setSaving(true);
    setSavedMsg(null);
    try {
      await saveProfileData(form);
      setSavedMsg("Profile saved and indexed.");
    } catch {
      setSavedMsg("Failed to save. Try again.");
    } finally {
      setSaving(false);
    }
  }

  async function handleImport(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true);
    setSavedMsg(null);
    try {
      const result = await importLinkedInExport(file);
      setSavedMsg(`Imported: ${result.positions_imported} positions, ${result.skills_imported} skills.`);
      const updated = await getProfileData();
      setForm(updated);
    } catch {
      setSavedMsg("Import failed. Make sure it's a LinkedIn data export ZIP.");
    } finally {
      setImporting(false);
    }
  }

  async function handleAudit() {
    setAuditing(true);
    setAudit(null);
    try {
      const { response } = await sendMessage("Audit my LinkedIn profile and give me a prioritized improvement plan.");
      setAudit(response);
    } finally {
      setAuditing(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <nav className="flex items-center justify-between border-b border-gray-800 bg-gray-900 px-6 py-4">
        <h1 className="font-semibold text-white">Profile</h1>
        <div className="flex gap-4">
          <Link href="/chat" className="text-sm text-gray-400 hover:text-white transition">Chat</Link>
          <Link href="/drafts" className="text-sm text-gray-400 hover:text-white transition">Drafts</Link>
          <Link href="/analytics" className="text-sm text-gray-400 hover:text-white transition">Analytics</Link>
        </div>
      </nav>

      <div className="mx-auto max-w-2xl px-4 py-8 space-y-6">
        {loading && <p className="text-gray-500">Loading...</p>}

        {/* Basic identity from LinkedIn */}
        {basic && (
          <div className="rounded-xl border border-gray-800 bg-gray-900 p-5 flex items-center gap-4">
            {basic.picture && <img src={basic.picture} alt="Profile" className="h-12 w-12 rounded-full" />}
            <div>
              <p className="font-semibold text-white">{basic.name}</p>
              <p className="text-sm text-gray-400">{basic.email}</p>
            </div>
          </div>
        )}

        {/* Import section */}
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
          <h3 className="font-semibold text-white mb-1">Import from LinkedIn</h3>
          <p className="text-sm text-gray-400 mb-4">
            Download your data export from{" "}
            <span className="text-gray-300">LinkedIn → Settings → Privacy → Get a copy of your data</span>
            {" "}and upload the ZIP here to auto-populate your profile.
          </p>
          <input ref={fileRef} type="file" accept=".zip" className="hidden" onChange={handleImport} />
          <button
            onClick={() => fileRef.current?.click()}
            disabled={importing}
            className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:border-gray-500 disabled:opacity-50 transition"
          >
            {importing ? "Importing..." : "Upload LinkedIn ZIP"}
          </button>
        </div>

        {/* Profile form */}
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-5 space-y-5">
          <h3 className="font-semibold text-white">Your LinkedIn Profile</h3>

          <div>
            <label className="mb-1 block text-xs text-gray-400">Headline</label>
            <input
              type="text"
              value={form.headline}
              onChange={(e) => setForm({ ...form, headline: e.target.value })}
              placeholder="Software Engineer @ ADP | React · TypeScript · GenAI"
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs text-gray-400">About / Summary</label>
            <textarea
              value={form.about}
              onChange={(e) => setForm({ ...form, about: e.target.value })}
              rows={5}
              placeholder="Paste your About section here..."
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none resize-none"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs text-gray-400">Experience</label>
            <p className="mb-2 text-xs text-gray-600">Paste your experience bullets — one role per block, separated by a blank line.</p>
            <textarea
              value={form.experience}
              onChange={(e) => setForm({ ...form, experience: e.target.value })}
              rows={8}
              placeholder={`Application Developer — ADP (2023–Present)\n• Built GenAI automation tool using GPT-4 and LLaMA 2\n• Reduced manual test effort by 50% across ADP modules\n\nSoftware Engineer Intern — XYZ (2022)\n• ...`}
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none resize-none font-mono"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs text-gray-400">Skills</label>
            <input
              type="text"
              value={form.skills}
              onChange={(e) => setForm({ ...form, skills: e.target.value })}
              placeholder="React, TypeScript, Java, Python, GPT-4, LLaMA, Prompt Engineering, LangChain..."
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none"
            />
          </div>

          {savedMsg && <p className="text-sm text-green-400">{savedMsg}</p>}

          <button
            onClick={handleSave}
            disabled={saving}
            className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50 transition"
          >
            {saving ? "Saving..." : "Save & Index Profile"}
          </button>

          {form.updated_at && (
            <p className="text-xs text-gray-600">Last saved: {new Date(form.updated_at).toLocaleString()}</p>
          )}
        </div>

        {/* AI Audit */}
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
          <h3 className="font-semibold text-white mb-1">AI Profile Audit</h3>
          <p className="text-sm text-gray-400 mb-4">
            Save your profile above first, then run the audit. The agent compares your profile against your career goals and returns specific rewrites.
          </p>
          <button
            onClick={handleAudit}
            disabled={auditing}
            className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-40 transition"
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
