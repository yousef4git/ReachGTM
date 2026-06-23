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

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      window.location.href = "/login";
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
  list: () =>
    api.get<ContentAsset[]>("/api/v1/content/").then((r) => r.data),
  generate: (body: { strategy_id?: string; content_types: string[]; count_per_type: number }) =>
    api.post<{ content_assets: ContentAsset[]; session_id?: string }>("/api/v1/content/generate", body).then((r) => r.data),
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
  list: () =>
    api.get<KnowledgeDocument[]>("/api/v1/knowledge/").then((r) => r.data),
};

export default api;
