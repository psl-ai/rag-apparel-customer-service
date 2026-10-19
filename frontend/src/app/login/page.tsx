"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/api-client";

export default function LoginPage() {
  const router = useRouter(); const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [error, setError] = useState(""); const [pending, setPending] = useState(false);
  async function submit(event: FormEvent) { event.preventDefault(); setPending(true); setError(""); try { await login(email, password); router.push("/account"); } catch (err) { setError(err instanceof Error ? err.message : "登录失败"); } finally { setPending(false); } }
  return <main><section className="shell auth-card"><Link href="/">← FashionRAG</Link><h1>登录</h1><form className="checkout-form" onSubmit={submit}><label>邮箱<input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} /></label><label>密码<input type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} /></label>{error && <p role="alert">{error}</p>}<button type="submit" disabled={pending}>{pending ? "登录中..." : "登录"}</button></form><p className="muted">还没有账号？<Link href="/register">立即注册</Link></p></section></main>;
}
