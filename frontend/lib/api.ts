import axios from "axios";
import type { TokenResponse, LoginRequest, RegisterRequest } from "@/types";

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
};

export const strategyApi = {
  generate: (body: unknown) =>
    api.post("/api/v1/strategy/generate", body).then((r) => r.data),
  get: (id: string) =>
    api.get(`/api/v1/strategy/${id}`).then((r) => r.data),
};

export const knowledgeApi = {
  upload: (file: File, doc_type: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("doc_type", doc_type);
    return api.post("/api/v1/knowledge/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((r) => r.data);
  },
};

export default api;
