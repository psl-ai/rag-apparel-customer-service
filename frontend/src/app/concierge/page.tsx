"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { sendChat, type ChatCitation } from "@/lib/api-client";

type Turn = { role: "user" | "assistant"; content: string; citations?: ChatCitation[] };

export default function ConciergePage() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [message, setMessage] = useState("");
  const [conversationId, setConversationId] = useState<string>();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string>();

  async function submit(event: FormEvent) {
    event.preventDefault();
    const value = message.trim();
    if (!value || pending) return;
    setMessage(""); setError(undefined); setTurns((items) => [...items, { role: "user", content: value }]); setPending(true);
    try {
      const result = await sendChat(value, conversationId);
      setConversationId(result.conversation_id);
      setTurns((items) => [...items, { role: "assistant", content: result.answer, citations: result.citations }]);
    } catch { setError("暂时无法连接智能导购，请稍后重试。"); } finally { setPending(false); }
  }

  return <main><div className="shell concierge"><div className="concierge-head"><div><Link href="/">返回首页</Link><h1>AI 导购</h1><p className="muted">商品、尺码、库存与售后政策，基于真实数据回答。</p></div><Link className="action-link" href="/products">浏览商品</Link></div><section className="chat-window" aria-live="polite">{turns.length === 0 && <p className="muted">试试问：“这件衬衫 M 码还有库存吗？”</p>}{turns.map((turn, index) => <article className={`turn ${turn.role}`} key={`${turn.role}-${index}`}><strong>{turn.role === "user" ? "你" : "FashionRAG"}</strong><p>{turn.content}</p>{turn.citations?.map((citation) => <small className="citation" key={`${citation.title}-${citation.source_locator}`}>来源：{citation.title} · {citation.section ?? "正文"} · {citation.source_locator ?? "未标注"}</small>)}</article>)}</section>{error && <p role="alert">{error}</p>}<form className="chat-form" onSubmit={submit}><input value={message} onChange={(event) => setMessage(event.target.value)} placeholder="输入你的问题" aria-label="输入你的问题" /><button type="submit" disabled={pending}>{pending ? "思考中" : "发送"}</button></form></div></main>;
}
