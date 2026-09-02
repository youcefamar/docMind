import * as SecureStore from 'expo-secure-store';

const BASE_URL_KEY = 'docmind.server_url';

export async function getBaseUrl(): Promise<string> {
  try {
    const stored = await SecureStore.getItemAsync(BASE_URL_KEY);
    return stored ?? '';
  } catch {
    return '';
  }
}

export async function saveBaseUrl(url: string): Promise<void> {
  await SecureStore.setItemAsync(BASE_URL_KEY, url.replace(/\/+$/, ''));
}

export async function apiFetch(path: string, options?: RequestInit): Promise<Response> {
  const base = await getBaseUrl();
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return fetch(`${base}${normalizedPath}`, options);
}

export async function readApiPayload<T = unknown>(res: Response): Promise<T | null> {
  const raw = await res.text();
  if (!raw.trim()) return null;

  try {
    const json = JSON.parse(raw);
    return (json?.data ?? json) as T;
  } catch {
    return raw as unknown as T;
  }
}

export function getApiErrorMessage(payload: unknown, fallback = 'An unexpected error occurred'): string {
  if (typeof payload === 'string') return payload.trim() || fallback;
  if (!payload || typeof payload !== 'object') return fallback;

  const record = payload as Record<string, unknown>;
  if (typeof record.error === 'string' && record.error.trim()) return record.error;
  if (typeof record.message === 'string' && record.message.trim()) return record.message;

  const detail = record.detail;
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (detail && typeof detail === 'object') {
    const detailRecord = detail as Record<string, unknown>;
    if (typeof detailRecord.message === 'string' && detailRecord.message.trim()) {
      return detailRecord.message;
    }
    try {
      return JSON.stringify(detailRecord);
    } catch {
      return fallback;
    }
  }

  return fallback;
}
