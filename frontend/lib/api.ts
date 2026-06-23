import axios from "axios";
import type {
  TokenResponse,
  LoginRequest,
  RegisterRequest,
  ContentAsset,
  KnowledgeDocument,
  AcceptInviteRequest,
  CreateInviteRequest,
  CreateInviteResponse,
  TeamMember,
  AssignableRole,
  TeamSettings,
  WorkspacePlan,
} from "@/types";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Single-flight refresh: on a 401, try to mint a new access token from the
// refresh token once, retry the original request, and only bounce to /login if
// the refresh itself fails. Prevents a stampede of refresh calls and the abrupt
// "logged out mid-session" UX when a short-lived access token expires.
let refreshing: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const rt = typeof window !== "undefined" ? localStorage.getItem("refresh_token") : null;
  if (!rt) return null;
  try {
    const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    const res = await axios.post(`${base}/api/v1/auth/refresh`, { refresh_token: rt });
    const { access_token, refresh_token } = res.data as TokenResponse;
    localStorage.setItem("access_token", access_token);
    if (refresh_token) localStorage.setItem("refresh_token", refresh_token);
    return access_token;
  } catch {
    return null;
  }
}

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    const status = error.response?.status;
    const isAuthCall = typeof original?.url === "string" && original.url.includes("/auth/");

    if (status === 401 && original && !original._retry && !isAuthCall) {
      original._retry = true;
      refreshing = refreshing ?? refreshAccessToken();
      const newToken = await refreshing;
      refreshing = null;
      if (newToken) {
        original.headers = original.headers ?? {};
        original.headers.Authorization = `Bearer ${newToken}`;
        return api(original);
      }
    }

    if (status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      if (typeof window !== "undefined") window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: (body: LoginRequest) =>
    api.post<TokenResponse>("/api/v1/auth/login", body).then((r) => r.data),
  register: (body: RegisterRequest) =>
    api.post<TokenResponse>("/api/v1/auth/register", body).then((r) => r.data),
  refresh: (refresh_token: string) =>
    api.post<TokenResponse>("/api/v1/auth/refresh", { refresh_token }).then((r) => r.data),
  acceptInvite: (body: AcceptInviteRequest) =>
    api.post<TokenResponse>("/api/v1/auth/accept-invite", body).then((r) => r.data),
};

export const teamApi = {
  createInvite: (body: CreateInviteRequest) =>
    api.post<CreateInviteResponse>("/api/v1/auth/invite", body).then((r) => r.data),
  listMembers: () =>
    api.get<TeamMember[]>("/api/v1/team/members").then((r) => r.data),
  updateMemberRole: (userId: string, role: AssignableRole) =>
    api
      .patch<TeamMember>(`/api/v1/team/members/${userId}/role`, { role })
      .then((r) => r.data),
  getSettings: () =>
    api.get<TeamSettings>("/api/v1/team/settings").then((r) => r.data),
  updateSettings: (body: { name?: string; plan?: WorkspacePlan }) =>
    api.patch<TeamSettings>("/api/v1/team/settings", body).then((r) => r.data),
};

export const strategyApi = {
  generate: (body: unknown) =>
    api.post("/api/v1/strategy/generate", body).then((r) => r.data),
  get: (id: string) =>
    api.get(`/api/v1/strategy/${id}`).then((r) => r.data),
  list: () =>
    api.get("/api/v1/strategy").then((r) => r.data),
};

export const contentApi = {
  // Backend wraps list/generate responses as { count, assets }. Unwrap to the
  // array / shape the hooks and pages expect.
  list: () =>
    api.get<{ count: number; assets: ContentAsset[] }>("/api/v1/content/").then((r) => r.data.assets ?? []),
  generate: (body: { strategy_id?: string; content_types: string[]; count_per_type: number }) =>
    api
      .post<{ count: number; assets: ContentAsset[]; session_id?: string }>("/api/v1/content/generate", body)
      .then((r) => ({ content_assets: r.data.assets ?? [], session_id: r.data.session_id })),
};

export const SSE_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/^http/, "http") ?? "http://localhost:8000";

export const knowledgeApi = {
  upload: (file: File, doc_type: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("doc_type", doc_type);
    return api.post<KnowledgeDocument>("/api/v1/knowledge/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((r) => r.data);
  },
  // Backend wraps the list response as { documents }. Unwrap to an array.
  list: () =>
    api.get<{ documents: KnowledgeDocument[] }>("/api/v1/knowledge/").then((r) => r.data.documents ?? []),
};

export default api;
