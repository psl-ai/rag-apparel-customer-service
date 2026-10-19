"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { login, register } from "@/lib/api-client";

export default function RegisterPage() {
  const router = useRouter(); const [displayName, setDisplayName] = useState(""); const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [error, setError] = useState(""); const [pending, setPending] = useState(false);
  async function submit(event: FormEvent) { event.preventDefault(); setPending(true); setError(""); try { await register(email, password, displayName); await login(email, password); router.push("/account"); } catch (err) { setError(err instanceof Error ? err.message : "注册失败"); } finally { setPending(false); } }
  return <main><section className="shell auth-card"><Link href="/">← FashionRAG</Link><h1>创建账号</h1><form className="checkout-form" onSubmit={submit}><label>昵称<input required value={displayName} onChange={(e) => setDisplayName(e.target.value)} /></label><label>邮箱<input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} /></label><label>密码<input type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} /></label>{error && <p role="alert">{error}</p>}<button type="submit" disabled={pending}>{pending ? "创建中..." : "注册并登录"}</button></form><p className="muted">已有账号？<Link href="/login">返回登录</Link></p></section></main>;
}
