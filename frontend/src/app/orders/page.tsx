"use client";

import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { cancelOrder, getOrders, refundOrder } from "@/lib/api-client";

export default function OrdersPage() {
  const client = useQueryClient(); const orders = useQuery({ queryKey: ["orders"], queryFn: getOrders });
  const cancel = useMutation({ mutationFn: cancelOrder, onSuccess: () => client.invalidateQueries({ queryKey: ["orders"] }) });
  const refund = useMutation({ mutationFn: refundOrder, onSuccess: () => client.invalidateQueries({ queryKey: ["orders"] }) });
  if (orders.isPending) return <main><section className="shell"><p role="status">正在加载订单...</p></section></main>;
  if (orders.isError) return <main><section className="shell"><p role="alert">请先登录后查看订单。</p><Link href="/products">去购物</Link></section></main>;
  return <main><section className="shell"><Link href="/">← FashionRAG</Link><h1>我的订单</h1>{orders.data.length === 0 ? <p className="muted">暂无订单。</p> : <div className="order-list">{orders.data.map((order) => <article className="order-card" key={order.id}><strong>{order.order_number}</strong><span>¥{order.total_amount}</span><span>{order.status}</span><div>{order.status === "paid" && <button type="button" onClick={() => cancel.mutate(order.id)}>取消订单</button>}{["paid", "shipped", "delivered"].includes(order.status) && <button type="button" onClick={() => refund.mutate(order.id)}>申请退款</button>}</div></article>)}</div>}</section></main>;
}
