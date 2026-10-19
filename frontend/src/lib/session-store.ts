"use client";

import { useSyncExternalStore } from "react";

export type SessionUser = { id: string; email: string; display_name: string; is_active: boolean };
export type SessionState = { user: SessionUser | null; accessToken: string | null; refreshToken: string | null };

const STORAGE_KEY = "fashionrag_session";
let state: SessionState = { user: null, accessToken: null, refreshToken: null };
const listeners = new Set<() => void>();

function emit() { listeners.forEach((listener) => listener()); }
function persist() {
  if (typeof window !== "undefined") window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

export const sessionStore = {
  getState: () => state,
  setSession: (next: SessionState) => { state = next; persist(); emit(); },
  hydrate: () => {
    if (typeof window === "undefined") return;
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (raw) { try { state = JSON.parse(raw) as SessionState; } catch { window.localStorage.removeItem(STORAGE_KEY); } }
    emit();
  },
  logout: () => { state = { user: null, accessToken: null, refreshToken: null }; if (typeof window !== "undefined") window.localStorage.removeItem(STORAGE_KEY); emit(); },
  subscribe: (listener: () => void) => { listeners.add(listener); return () => listeners.delete(listener); },
};

export function useSession() { return useSyncExternalStore(sessionStore.subscribe, sessionStore.getState, sessionStore.getState); }
