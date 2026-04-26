"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { sendMessage, clearConversation, getToken, clearToken } from "@/lib/api";
import Link from "next/link";

type Message = { role: "user" | "agent"; text: string };

export default function ChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([
    { role: "agent", text: "Hey Shreyas! What do you want to work on today? I can help you decide what to post, draft content, or analyze your LinkedIn profile." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [clearing, setClearing] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!getToken()) router.push("/");
  }, [router]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;

    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");
    setLoading(true);

    try {
      const { response } = await sendMessage(text);
      setMessages((m) => [...m, { role: "agent", text: response }]);
    } catch {
      setMessages((m) => [...m, { role: "agent", text: "Something went wrong. Please try again." }]);
    } finally {
      setLoading(false);
    }
  }

  async function handleNewConversation() {
    setClearing(true);
    try {
      await clearConversation();
      setMessages([{ role: "agent", text: "Hey Shreyas! Fresh start — what do you want to work on?" }]);
    } finally {
      setClearing(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="flex h-screen flex-col">
      {/* Nav */}
      <nav className="flex items-center justify-between border-b border-gray-800 bg-gray-900 px-6 py-4">
        <h1 className="font-semibold text-white">LinkedIn AI Agent</h1>
        <div className="flex items-center gap-4">
          <button
            onClick={handleNewConversation}
            disabled={clearing}
            className="text-sm text-gray-400 hover:text-white transition disabled:opacity-40"
          >
            {clearing ? "Clearing..." : "New conversation"}
          </button>
          <Link href="/drafts" className="text-sm text-gray-400 hover:text-white transition">
            Drafts
          </Link>
          <Link href="/analytics" className="text-sm text-gray-400 hover:text-white transition">
            Analytics
          </Link>
          <Link href="/profile" className="text-sm text-gray-400 hover:text-white transition">
            Profile
          </Link>
          <button
            onClick={() => { clearToken(); router.push("/"); }}
            className="text-sm text-gray-500 hover:text-red-400 transition"
          >
            Sign out
          </button>
        </div>
      </nav>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto max-w-2xl space-y-4">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                  m.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-800 text-gray-100"
                }`}
              >
                {m.text}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="rounded-2xl bg-gray-800 px-4 py-3 text-sm text-gray-400">
                Thinking...
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-gray-800 bg-gray-900 px-4 py-4">
        <div className="mx-auto flex max-w-2xl gap-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask me what to post, request a draft, or get profile advice..."
            rows={2}
            className="flex-1 resize-none rounded-xl border border-gray-700 bg-gray-800 px-4 py-3 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
        <p className="mt-2 text-center text-xs text-gray-600">
          Shift+Enter for new line · Enter to send
        </p>
      </div>
    </div>
  );
}
