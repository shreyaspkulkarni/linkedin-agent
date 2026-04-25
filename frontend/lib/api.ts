import axios from "axios";

const API = axios.create({ baseURL: process.env.NEXT_PUBLIC_API_URL });

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

export function setToken(token: string) {
  localStorage.setItem("token", token);
}

export function clearToken() {
  localStorage.removeItem("token");
}

// Agent
export async function sendMessage(message: string) {
  const { data } = await API.post("/agent/chat", {
    token: getToken(),
    message,
  });
  return data as { response: string };
}

// Posts
export async function getDrafts() {
  const { data } = await API.get("/posts/drafts", {
    params: { token: getToken() },
  });
  return data as { id: string; content: string; created_at: string }[];
}

export async function publishPost(postId: string) {
  const { data } = await API.post(
    `/posts/publish/${postId}`,
    null,
    { params: { token: getToken() } }
  );
  return data;
}

export async function schedulePost(postId: string, publishAt: string) {
  const { data } = await API.post("/posts/schedule", {
    token: getToken(),
    post_id: postId,
    publish_at: publishAt,
  });
  return data;
}

export async function getProfile() {
  const { data } = await API.get("/profile/me", {
    params: { token: getToken() },
  });
  return data;
}

export async function getProfileData() {
  const { data } = await API.get("/profile/data", {
    params: { token: getToken() },
  });
  return data as { headline: string; about: string; experience: string; skills: string; updated_at?: string };
}

export async function saveProfileData(payload: {
  headline: string;
  about: string;
  experience: string;
  skills: string;
}) {
  const { data } = await API.post("/profile/data", {
    token: getToken(),
    ...payload,
  });
  return data;
}

export async function importLinkedInExport(file: File) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await API.post(`/profile/import?token=${getToken()}`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data as { message: string; headline: string; positions_imported: number; skills_imported: number };
}

export async function getAnalytics() {
  const { data } = await API.get("/posts/analytics", {
    params: { token: getToken() },
  });
  return data as {
    id: string;
    content: string;
    published_at: string;
    likes: number;
    comments: number;
    shares: number;
    impressions: number;
    fetched_at: string | null;
  }[];
}

export async function refreshAnalytics() {
  const { data } = await API.post("/posts/analytics/refresh", null, {
    params: { token: getToken() },
  });
  return data as { refreshed: number };
}
