import type { Metadata } from "next";

import { Providers } from "@/components/providers";
import Link from "next/link";

import "./globals.css";

export const metadata: Metadata = {
  title: "FashionRAG",
  description: "智能服装导购与商城",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>
        <nav className="site-nav"><Link href="/">FashionRAG</Link><span><Link href="/products">商品</Link><Link href="/concierge">AI 导购</Link><Link href="/cart">购物车</Link><Link href="/account">我的</Link><Link href="/admin">后台</Link></span></nav>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
