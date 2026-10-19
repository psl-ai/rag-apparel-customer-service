"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { use } from "react";

import { addCartItem, createReview, getProduct, getProductSkus, getReviews, toggleFavorite, type Review } from "@/lib/api-client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useSession, sessionStore } from "@/lib/session-store";

export default function ProductDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const session = useSession();
  const [selectedSku, setSelectedSku] = useState<string>();
  const [cartMessage, setCartMessage] = useState(""); const [favoriteMessage, setFavoriteMessage] = useState(""); const [reviewText, setReviewText] = useState(""); const [reviews, setReviews] = useState<Review[]>([]);
  const product = useQuery({ queryKey: ["product", id], queryFn: () => getProduct(id) });
  const skus = useQuery({ queryKey: ["product-skus", id], queryFn: () => getProductSkus(id), enabled: product.isSuccess });
  useQuery({ queryKey: ["reviews", id], queryFn: () => getReviews(id).then((items) => { setReviews(items); return items; }), enabled: product.isSuccess });

  if (product.isPending) return <main><section className="shell"><p role="status">正在加载商品...</p></section></main>;
  if (product.isError) return <main><section className="shell"><p role="alert">商品不存在或暂时无法加载。</p><Link href="/products">返回商品目录</Link></section></main>;

  const firstSku = skus.data?.[0];
  const activeSku = selectedSku ?? firstSku?.id;
  async function addToCart() {
    if (!sessionStore.getState().accessToken) { router.push("/login"); return; }
    if (!activeSku) return;
    try { await addCartItem(activeSku, 1); setCartMessage("已加入购物车"); } catch { setCartMessage("加入失败，请检查库存"); }
  }
  async function favorite() { if (!sessionStore.getState().accessToken) { router.push("/login"); return; } try { const result = await toggleFavorite(id); setFavoriteMessage(result.favorited ? "已收藏" : "已取消收藏"); } catch { setFavoriteMessage("操作失败"); } }
  async function submitReview() { if (!sessionStore.getState().accessToken) { router.push("/login"); return; } if (!reviewText.trim()) return; try { const review = await createReview(id, 5, reviewText); setReviews((items) => [review, ...items]); setReviewText(""); } catch { setFavoriteMessage("评价提交失败"); } }
  return (
    <main>
      <section className="shell detail">
        <Link href="/products">← 返回目录</Link>
        <div className="product-mark" style={{ marginTop: 28 }}>FASHIONRAG / {product.data.slug}</div>
        <p className="muted">{product.data.status === "published" ? "现货商品" : "暂不可售"}</p>
        <h1>{product.data.name}</h1>
        <button type="button" onClick={favorite}>收藏</button>{favoriteMessage && <span className="muted">{favoriteMessage}</span>}
        <p>{product.data.description}</p>
        <p className="muted">面料：{product.data.fabric_info ?? "暂无说明"}</p>
        <p className="muted">洗护：{product.data.care_instructions ?? "暂无说明"}</p>
        {skus.isPending && <p role="status">正在加载可选规格...</p>}
        {skus.isError && <p role="alert">规格暂时无法加载。</p>}
        {skus.data && skus.data.length > 0 && <>
          <p className="price">¥{firstSku?.sale_price}</p>
          <div className="sku-list" aria-label="商品规格">
            {skus.data.map((sku) => <button className={`sku-row sku-select ${activeSku === sku.id ? "selected" : ""}`} type="button" key={sku.id} onClick={() => setSelectedSku(sku.id)}><span>{sku.code}</span><span>¥{sku.sale_price}</span></button>)}
          </div>
          <button type="button" onClick={addToCart}>加入购物车</button>
          {cartMessage && <p role="status">{cartMessage}</p>}
        </>}
        {skus.data?.length === 0 && <p className="muted">该商品暂时没有可选规格。</p>}
        <section className="reviews"><h2>用户评价</h2>{reviews.length === 0 ? <p className="muted">暂无评价</p> : reviews.map((review) => <article className="review" key={review.id}><strong>{"★".repeat(review.rating)}</strong><p>{review.content}</p></article>)}<textarea value={reviewText} onChange={(e) => setReviewText(e.target.value)} placeholder="分享你的穿着体验" aria-label="评价内容" /><button type="button" onClick={submitReview}>提交评价</button></section>
      </section>
    </main>
  );
}
