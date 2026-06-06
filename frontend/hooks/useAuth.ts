import { useCallback, useState } from "react";
import { authApi } from "@/lib/api";
import { setTokens, clearTokens } from "@/lib/auth";
import type { LoginRequest, RegisterRequest } from "@/types";

export function useAuth() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = useCallback(async (body: LoginRequest) => {
    setLoading(true);
    try {
      const tokens = await authApi.login(body);
      setTokens(tokens.access_token, tokens.refresh_token);
      return tokens;
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Login failed");
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const register = useCallback(async (body: RegisterRequest) => {
    setLoading(true);
    try {
      const tokens = await authApi.register(body);
      setTokens(tokens.access_token, tokens.refresh_token);
      return tokens;
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Registration failed");
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    clearTokens();
    window.location.href = "/login";
  }, []);

  return { login, register, logout, loading, error };
}
