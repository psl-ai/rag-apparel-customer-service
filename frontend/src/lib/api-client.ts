export type HealthData = { status: string };
import { sessionStore, type SessionUser } from "@/lib/session-store";

export type Product = {
  id: string;
  category_id: string;
  name: string;
  slug: string;
  description: string;
  fabric_info: string | null;
  care_instructions: string | null;
  status: string;
};

export type ProductList = { items: Product[]; total: number; skip: number; limit: number };
export type CategoryOption = { id: string; name: string; slug: string };
export type ColorOption = { id: string; name: string; hex_value: string };
export type SizeOption = { id: string; name: string; sort_order: number };
export type Sku = {
  id: string;
  code: string;
  color_id: string;
  size_id: string;
  sale_price: string | number;
  original_price: string | number | null;
  status: string;
};

type ApiResponse<T> = {
  data: T;
  code: string;
  message: string;
  request_id: string;
};

export type AuthTokens = { access_token: string; refresh_token: string; token_type: string; user: SessionUser };

export async function login(email: string, password: string): Promise<AuthTokens> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const response = await fetch(`${baseUrl}/api/v1/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password }) });
  if (!response.ok) throw new Error("邮箱或密码错误");
  const result = (await response.json() as ApiResponse<AuthTokens>).data;
  sessionStore.setSession({ user: result.user, accessToken: result.access_token, refreshToken: result.refresh_token });
  return result;
}

export async function register(email: string, password: string, displayName: string): Promise<void> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const response = await fetch(`${baseUrl}/api/v1/auth/register`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password, display_name: displayName }) });
  if (!response.ok) throw new Error("注册失败，请检查邮箱或密码");
}

export async function getLiveHealth(): Promise<HealthData> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const response = await fetch(`${baseUrl}/api/v1/health/live`, { cache: "no-store" });
  if (!response.ok) throw new Error("Health request failed");
  const payload = (await response.json()) as ApiResponse<HealthData>;
  return payload.data;
}

async function apiGet<T>(path: string): Promise<T> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const response = await fetch(`${baseUrl}${path}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  const payload = (await response.json()) as ApiResponse<T>;
  return payload.data;
}

export function getProducts(search = "", skip = 0, limit = 20): Promise<ProductList> {
  const query = new URLSearchParams({ skip: String(skip), limit: String(limit) });
  if (search.trim()) query.set("search", search.trim());
  return apiGet<ProductList>(`/api/v1/products?${query.toString()}`);
}

export function getCategories(): Promise<CategoryOption[]> { return apiGet<CategoryOption[]>("/api/v1/categories"); }
export function getColors(): Promise<ColorOption[]> { return apiGet<ColorOption[]>("/api/v1/colors"); }
export function getSizes(): Promise<SizeOption[]> { return apiGet<SizeOption[]>("/api/v1/sizes"); }

export function getProduct(id: string): Promise<Product> {
  return apiGet<Product>(`/api/v1/products/${id}`);
}

export function getProductSkus(id: string): Promise<Sku[]> {
  return apiGet<Sku[]>(`/api/v1/products/${id}/skus`);
}

export type ChatCitation = { title: string; section: string | null; source_locator: string | null; snippet: string };
export type ChatResult = { conversation_id: string; message_id: string; answer: string; intent: string; citations: ChatCitation[]; handoff: boolean };

export async function sendChat(message: string, conversationId?: string, productId?: string): Promise<ChatResult> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const token = sessionStore.getState().accessToken;
  const response = await fetch(`${baseUrl}/api/v1/chat`, { method: "POST", headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) }, body: JSON.stringify({ message, conversation_id: conversationId, product_id: productId }) });
  if (!response.ok) throw new Error(`Chat request failed: ${response.status}`);
  const payload = (await response.json()) as ApiResponse<ChatResult>;
  return payload.data;
}

export type Cart = { id: string; user_id: string; items: { id: string; sku_id: string; quantity: number }[] };
export type Order = { id: string; order_number: string; user_id: string; status: string; total_amount: string | number; address_snapshot?: string };

async function apiAuthed<T>(path: string, init: RequestInit = {}): Promise<T> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const token = sessionStore.getState().accessToken;
  let response = await fetch(`${baseUrl}${path}`, { ...init, headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(init.headers ?? {}) } });
  if (response.status === 401 && sessionStore.getState().refreshToken) {
    const refreshed = await fetch(`${baseUrl}/api/v1/auth/refresh`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh_token: sessionStore.getState().refreshToken }) });
    if (refreshed.ok) {
      const result = (await refreshed.json() as ApiResponse<AuthTokens>).data;
      sessionStore.setSession({ user: result.user, accessToken: result.access_token, refreshToken: result.refresh_token });
      response = await fetch(`${baseUrl}${path}`, { ...init, headers: { "Content-Type": "application/json", Authorization: `Bearer ${result.access_token}`, ...(init.headers ?? {}) } });
    }
  }
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  const payload = (await response.json()) as ApiResponse<T>;
  return payload.data;
}

export function getCart(): Promise<Cart> { return apiAuthed<Cart>("/api/v1/cart"); }
export function addCartItem(skuId: string, quantity = 1): Promise<Cart> { return apiAuthed<Cart>("/api/v1/cart/items", { method: "POST", body: JSON.stringify({ sku_id: skuId, quantity }) }); }
export function updateCartItem(itemId: string, skuId: string, quantity: number): Promise<Cart> { return apiAuthed<Cart>(`/api/v1/cart/items/${itemId}`, { method: "PATCH", body: JSON.stringify({ sku_id: skuId, quantity }) }); }
export function deleteCartItem(itemId: string): Promise<Cart> { return apiAuthed<Cart>(`/api/v1/cart/items/${itemId}`, { method: "DELETE" }); }
export function checkout(addressSnapshot: string, couponCode?: string, idempotencyKey?: string): Promise<Order> { return apiAuthed<Order>("/api/v1/orders", { method: "POST", headers: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : undefined, body: JSON.stringify({ address_snapshot: addressSnapshot, coupon_code: couponCode || null }) }); }
export function getOrders(): Promise<Order[]> { return apiAuthed<Order[]>("/api/v1/orders"); }
export function getOrder(id: string): Promise<Order> { return apiAuthed<Order>(`/api/v1/orders/${id}`); }
export function cancelOrder(id: string): Promise<Order> { return apiAuthed<Order>(`/api/v1/orders/${id}/cancel`, { method: "POST" }); }
export function refundOrder(id: string): Promise<Order> { return apiAuthed<Order>(`/api/v1/orders/${id}/refund`, { method: "POST" }); }
export type FavoriteProduct = { id: string; name: string; slug: string };
export type Review = { id: string; rating: number; content: string | null; created_at: string };
export type Profile = { id: string; email: string; display_name: string; is_active: boolean };
export function getProfile(): Promise<Profile> { return apiAuthed<Profile>("/api/v1/profile"); }
export function updateProfile(displayName: string): Promise<Profile> { return apiAuthed<Profile>("/api/v1/profile", { method: "PATCH", body: JSON.stringify({ display_name: displayName }) }); }
export function getFavorites(): Promise<FavoriteProduct[]> { return apiAuthed<FavoriteProduct[]>("/api/v1/profile/favorites"); }
export function toggleFavorite(productId: string): Promise<{ product_id: string; favorited: boolean }> { return apiAuthed<{ product_id: string; favorited: boolean }>(`/api/v1/products/${productId}/favorite`, { method: "POST" }); }
export function getReviews(productId: string): Promise<Review[]> { return apiGet<Review[]>(`/api/v1/products/${productId}/reviews`); }
export function createReview(productId: string, rating: number, content: string): Promise<Review> { return apiAuthed<Review>(`/api/v1/products/${productId}/reviews`, { method: "POST", body: JSON.stringify({ rating, content }) }); }
export type AdminDashboard = { users: number; orders: number; sales_amount: string | number; consultations: number; handoffs: number; satisfaction: number; feedback_count: number };
export type AdminProduct = { id: string; name: string; slug: string; status: string; category_id: string; description?: string; fabric_info?: string | null; care_instructions?: string | null };
export type AdminOrder = { id: string; order_number: string; user_id: string; status: string; total_amount: string | number };
export type AdminTrace = { id: string; conversation_id: string; intent: string | null; model_name: string | null; tool_calls: { tool_name: string; success: boolean }[] };
export type Inventory = { id: string; sku_id: string; quantity: number; locked_quantity: number; available_quantity: number; low_stock_threshold: number };
export function getAdminDashboard(): Promise<AdminDashboard> { return apiAuthed<AdminDashboard>("/api/v1/admin/dashboard"); }
export function getAdminProducts(): Promise<AdminProduct[]> { return apiAuthed<AdminProduct[]>("/api/v1/admin/products"); }
export function getAdminOrders(): Promise<AdminOrder[]> { return apiAuthed<AdminOrder[]>("/api/v1/admin/orders"); }
export function getRagEvaluations(): Promise<{ passed: number; total: number; pass_rate: number }> { return apiAuthed<{ passed: number; total: number; pass_rate: number }>("/api/v1/admin/rag/evaluations"); }
export type AdminKnowledgeDocument = { id: string; title: string; document_type: string; status: string; active_version: number | null };
export function updateAdminProductStatus(id: string, status: string): Promise<{ id: string; status: string }> { return apiAuthed<{ id: string; status: string }>(`/api/v1/admin/products/${id}/status`, { method: "PATCH", body: JSON.stringify({ status }) }); }
export function updateAdminOrderStatus(id: string, status: string, carrier?: string, trackingNumber?: string): Promise<{ id: string; status: string }> { return apiAuthed<{ id: string; status: string }>(`/api/v1/admin/orders/${id}/status`, { method: "PATCH", body: JSON.stringify({ status, carrier: carrier || null, tracking_number: trackingNumber || null }) }); }
export function getKnowledgeDocuments(): Promise<AdminKnowledgeDocument[]> { return apiAuthed<AdminKnowledgeDocument[]>("/api/v1/knowledge/documents"); }
export function getAdminAgentTraces(): Promise<AdminTrace[]> { return apiAuthed<AdminTrace[]>("/api/v1/admin/agent-traces"); }
export function getInventory(): Promise<Inventory[]> { return apiAuthed<Inventory[]>("/api/v1/inventory"); }
export function adjustInventory(skuId: string, delta: number, reason: string): Promise<Inventory> { return apiAuthed<Inventory>(`/api/v1/inventory/${skuId}`, { method: "PATCH", body: JSON.stringify({ delta, reason }) }); }
export function createProduct(payload: { category_id: string; name: string; slug: string; description: string; fabric_info?: string; care_instructions?: string; status?: string }): Promise<Product> { return apiAuthed<Product>("/api/v1/products", { method: "POST", body: JSON.stringify(payload) }); }
export function updateProduct(id: string, payload: { name?: string; description?: string; fabric_info?: string; care_instructions?: string }): Promise<Product> { return apiAuthed<Product>(`/api/v1/products/${id}`, { method: "PATCH", body: JSON.stringify(payload) }); }
export function createSku(productId: string, payload: { color_id: string; size_id: string; code: string; barcode?: string; sale_price: number; original_price?: number; image_key?: string }): Promise<Sku> { return apiAuthed<Sku>(`/api/v1/products/${productId}/skus`, { method: "POST", body: JSON.stringify(payload) }); }
export function uploadKnowledgeDocument(file: File, title: string, documentType: string, productId?: string): Promise<AdminKnowledgeDocument & { version: number }> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const token = sessionStore.getState().accessToken;
  const form = new FormData(); form.append("file", file); form.append("title", title); form.append("document_type", documentType); if (productId) form.append("product_id", productId);
  return fetch(`${baseUrl}/api/v1/knowledge/documents`, { method: "POST", headers: token ? { Authorization: `Bearer ${token}` } : {}, body: form }).then(async (response) => { if (!response.ok) throw new Error(`Request failed: ${response.status}`); return (await response.json() as ApiResponse<AdminKnowledgeDocument & { version: number }>).data; });
}
export function reindexKnowledgeDocument(id: string): Promise<{ chunks: number; version: number }> { return apiAuthed<{ chunks: number; version: number }>(`/api/v1/knowledge/reindex/${id}`, { method: "POST" }); }
export function deleteKnowledgeDocument(id: string): Promise<{ id: string; status: string }> { return apiAuthed<{ id: string; status: string }>(`/api/v1/knowledge/documents/${id}`, { method: "DELETE" }); }
