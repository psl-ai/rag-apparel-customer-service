"use client";

import { useQuery } from "@tanstack/react-query";

import { getLiveHealth } from "@/lib/api-client";
import Link from "next/link";

export default function Home() {
  const health = useQuery({ queryKey: ["health"], queryFn: getLiveHealth });

  return (
    <main>
      <section className="shell" aria-labelledby="brand-title">
        <p>单品牌服装商城</p>
        <h1 id="brand-title">FashionRAG</h1>
        <p>智能客服与个性化导购系统</p>
        <div className="status" role="status">
          {health.isPending && "正在连接服务..."}
          {health.isError && "服务暂不可用"}
          {health.data?.status === "ok" && "服务已连接"}
        </div>
        <div>
          <Link className="action-link" href="/products">浏览商品</Link>
          <Link className="action-link" href="/concierge">咨询 AI 导购</Link>
        </div>
      </section>
    </main>
  );
}
