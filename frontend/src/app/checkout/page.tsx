"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { checkout } from "@/lib/api-client";

export default function CheckoutPage() {
  const [address, setAddress] = useState(""); const [coupon, setCoupon] = useState(""); const [error, setError] = useState(""); const [orderNumber, setOrderNumber] = useState("");
  async function submit(event: FormEvent) { event.preventDefault(); setError(""); try { const order = await checkout(address, coupon); setOrderNumber(order.order_number); } catch { setError("下单失败，请确认登录状态、地址和库存。"); } }
  if (orderNumber) return <main><section className="shell"><h1>下单成功</h1><p>订单号：{orderNumber}</p><Link className="action-link" href="/orders">查看订单</Link></section></main>;
  return <main><section className="shell detail"><Link href="/cart">← 返回购物车</Link><h1>确认订单</h1><form className="checkout-form" onSubmit={submit}><label>收货地址<textarea required minLength={5} value={address} onChange={(e) => setAddress(e.target.value)} placeholder="省市区和详细地址" /></label><label>优惠券<input value={coupon} onChange={(e) => setCoupon(e.target.value)} placeholder="可选" /></label>{error && <p role="alert">{error}</p>}<button type="submit">提交订单</button></form></section></main>;
}
