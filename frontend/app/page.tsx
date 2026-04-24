"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();

  useEffect(() => {
    if (getToken()) router.push("/chat");
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-sm rounded-2xl border border-gray-800 bg-gray-900 p-10 text-center shadow-xl">
        <h1 className="mb-2 text-2xl font-bold text-white">LinkedIn AI Agent</h1>
        <p className="mb-8 text-sm text-gray-400">
          Your personal agent for growing on LinkedIn
        </p>
        <a
          href={`${process.env.NEXT_PUBLIC_API_URL}/auth/login`}
          className="flex w-full items-center justify-center gap-3 rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-500"
        >
          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M19 0h-14c-2.76 0-5 2.24-5 5v14c0 2.76 2.24 5 5 5h14c2.76 0 5-2.24 5-5v-14c0-2.76-2.24-5-5-5zm-11 19h-3v-10h3v10zm-1.5-11.27c-.97 0-1.75-.79-1.75-1.76s.78-1.75 1.75-1.75 1.75.78 1.75 1.75-.78 1.76-1.75 1.76zm13.5 11.27h-3v-5.6c0-1.34-.03-3.07-1.87-3.07-1.87 0-2.16 1.46-2.16 2.97v5.7h-3v-10h2.88v1.36h.04c.4-.76 1.38-1.56 2.84-1.56 3.04 0 3.6 2 3.6 4.59v5.61z" />
          </svg>
          Continue with LinkedIn
        </a>
        <p className="mt-6 text-xs text-gray-500">
          Your posts are never published without your approval.
        </p>
      </div>
    </div>
  );
}
