"use client";
import { Suspense, useState, FormEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Loader2, AlertCircle } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { authApi } from "@/lib/api";
import { setTokens } from "@/lib/auth";
import { AuthShell } from "@/components/auth/AuthShell";

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
    <AuthShell
      title={isInvite ? "Join your team" : "Create your workspace"}
      subtitle={
        isInvite
          ? "You've been invited to a workspace. Set your email and password to join."
          : "Spin up an AI go-to-market workspace in seconds."
      }
      footer={
        isInvite ? undefined : (
          <>
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-blue-600 hover:text-blue-700">
              Sign in
            </Link>
          </>
        )
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="flex items-start gap-2 rounded-md bg-red-50 px-3 py-2.5 text-sm text-red-700">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!isInvite && (
          <div>
            <label htmlFor="company" className="field-label">Company name</label>
            <input
              id="company" type="text" required placeholder="Acme Inc."
              value={companyName} onChange={(e) => setCompanyName(e.target.value)} className="field"
            />
          </div>
        )}

        <div>
          <label htmlFor="email" className="field-label">Work email</label>
          <input
            id="email" type="email" required autoComplete="email" placeholder="you@company.com"
            value={email} onChange={(e) => setEmail(e.target.value)} className="field"
          />
        </div>

        <div>
          <label htmlFor="password" className="field-label">Password</label>
          <input
            id="password" type="password" required minLength={8} autoComplete="new-password"
            placeholder="At least 8 characters"
            value={password} onChange={(e) => setPassword(e.target.value)} className="field"
          />
        </div>

        <button type="submit" disabled={loading} className="btn btn-primary mt-1 w-full">
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              {isInvite ? "Joining…" : "Creating workspace…"}
            </>
          ) : isInvite ? (
            "Accept invite"
          ) : (
            "Get started"
          )}
        </button>
      </form>
    </AuthShell>
  );
}

export default function RegisterPage() {
  return (
    <Suspense
      fallback={
        <main className="flex min-h-screen items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-ink-muted" />
        </main>
      }
    >
      <RegisterForm />
    </Suspense>
  );
}
