"use client";

import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getCart, deleteCartItem, updateCartItem } from "@/lib/api-client";

export default function CartPage() {
  const client = useQueryClient();
  const cart = useQuery({ queryKey: ["cart"], queryFn: getCart });
  const remove = useMutation({ mutationFn: deleteCartItem, onSuccess: (data) => client.setQueryData(["cart"], data) });
  const update = useMutation({ mutationFn: ({ id, skuId, quantity }: { id: string; skuId: string; quantity: number }) => updateCartItem(id, skuId, quantity), onSuccess: (data) => client.setQueryData(["cart"], data) });
  if (cart.isPending) return <main><section className="shell"><p role="status">正在加载购物车...</p></section></main>;
  if (cart.isError) return <main><section className="shell"><p role="alert">请先登录后查看购物车。</p><Link href="/products">继续购物</Link></section></main>;
  return <main><section className="shell"><Link href="/products">← 继续购物</Link><h1>购物车</h1>{cart.data.items.length === 0 ? <p className="muted">购物车还是空的。</p> : <div className="cart-list">{cart.data.items.map((item) => <div className="cart-row" key={item.id}><span>SKU {item.sku_id.slice(0, 8)}</span><input aria-label="商品数量" type="number" min={1} value={item.quantity} onChange={(e) => update.mutate({ id: item.id, skuId: item.sku_id, quantity: Number(e.target.value) })} /><button type="button" onClick={() => remove.mutate(item.id)}>删除</button></div>)}</div>}<Link className="action-link" href="/checkout">去结算</Link></section></main>;
}
