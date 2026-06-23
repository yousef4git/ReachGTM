"use client";
import { Suspense, useState, FormEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { authApi } from "@/lib/api";
import { setTokens } from "@/lib/auth";

function RegisterForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const inviteToken = searchParams.get("invite");
  const isInvite = !!inviteToken;

  const { register, loading: registerLoading, error: registerError } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [companyName, setCompanyName] = useState("");

  const [inviteLoading, setInviteLoading] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);

  const loading = isInvite ? inviteLoading : registerLoading;
  const error = isInvite ? inviteError : registerError;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (isInvite) {
      setInviteError(null);
      setInviteLoading(true);
      try {
        const tokens = await authApi.acceptInvite({
          invite_token: inviteToken as string,
          email,
          password,
        });
        setTokens(tokens.access_token, tokens.refresh_token);
        router.push("/dashboard");
      } catch (err: unknown) {
        setInviteError(err instanceof Error ? err.message : "Failed to accept invite");
      } finally {
        setInviteLoading(false);
      }
      return;
    }

    try {
      await register({ email, password, company_name: companyName });
      router.push("/knowledge");
    } catch {
      // error already set in useAuth
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50">
      <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-4 rounded-xl bg-white p-8 shadow">
        <h1 className="text-2xl font-bold text-gray-900">
          {isInvite ? "Join your team on ReachGTM" : "Create your ReachGTM workspace"}
        </h1>
        {isInvite && (
          <p className="text-sm text-gray-600">
            You&apos;ve been invited to a workspace. Set your email and password to join.
          </p>
        )}
        {error && <p className="text-sm text-red-600">{error}</p>}
        {!isInvite && (
          <div>
            <label className="block text-sm font-medium text-gray-700">Company name</label>
            <input
              type="text" required value={companyName} onChange={(e) => setCompanyName(e.target.value)}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            />
          </div>
        )}
        <div>
          <label className="block text-sm font-medium text-gray-700">Email</label>
          <input
            type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Password</label>
          <input
            type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>
        <button
          type="submit" disabled={loading}
          className="w-full rounded-md bg-blue-600 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {isInvite
            ? loading ? "Joining team..." : "Accept invite"
            : loading ? "Creating workspace..." : "Get started"}
        </button>
        {!isInvite && (
          <p className="text-center text-sm text-gray-600">
            Have an account? <a href="/login" className="text-blue-600 hover:underline">Sign in</a>
          </p>
        )}
      </form>
    </main>
  );
}

export default function RegisterPage() {
  return (
    <Suspense fallback={
      <main className="flex min-h-screen items-center justify-center bg-gray-50">
        <p className="text-sm text-gray-500">Loading...</p>
      </main>
    }>
      <RegisterForm />
    </Suspense>
  );
}
