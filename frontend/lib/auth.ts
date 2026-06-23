export function getAccessToken(): string | null {
  return localStorage.getItem("access_token");
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
}

export function clearTokens(): void {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

interface AccessTokenPayload {
  sub?: string;
  company_id?: string;
  role?: string;
}

function decodeJwt(token: string): AccessTokenPayload | null {
  try {
    const payload = token.split(".")[1];
    if (!payload) return null;
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    const json = atob(normalized);
    return JSON.parse(json) as AccessTokenPayload;
  } catch {
    return null;
  }
}

/** Reads the `role` claim from the stored access token, or null if absent/invalid. */
export function getRole(): string | null {
  const token = getAccessToken();
  if (!token) return null;
  return decodeJwt(token)?.role ?? null;
}

/** Reads the `sub` (user id) claim from the stored access token, or null. */
export function getUserId(): string | null {
  const token = getAccessToken();
  if (!token) return null;
  return decodeJwt(token)?.sub ?? null;
}
