"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { getProducts } from "@/lib/api-client";

export default function ProductsPage() {
  const [search, setSearch] = useState("");
  const [submittedSearch, setSubmittedSearch] = useState("");
  const products = useQuery({ queryKey: ["products", submittedSearch], queryFn: () => getProducts(submittedSearch) });

  return (
    <main>
      <section className="shell">
        <Link href="/">← FashionRAG</Link>
        <p className="muted">春秋系列 · 单品牌精选</p>
        <h1>商品目录</h1>
        <form className="toolbar" onSubmit={(event) => { event.preventDefault(); setSubmittedSearch(search); }}>
          <input aria-label="搜索商品" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="搜索风衣、针织、通勤..." />
          <button type="submit">搜索</button>
        </form>
        {products.isPending && <p role="status">正在加载商品...</p>}
        {products.isError && <p role="alert">商品暂时无法加载，请确认后端服务已启动。</p>}
        {products.data && products.data.items.length === 0 && <p className="muted">没有找到匹配商品。</p>}
        <div className="product-grid">
          {products.data?.items.map((product) => (
            <Link className="product-card" href={`/products/${product.id}`} key={product.id}>
              <div className="product-mark">FASHIONRAG / {product.slug}</div>
              <h2>{product.name}</h2>
              <p>{product.description}</p>
              <span className="muted">查看详情 →</span>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}
