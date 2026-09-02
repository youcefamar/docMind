import * as SecureStore from 'expo-secure-store';

const BASE_URL_KEY = 'docmind.server_url';

export function normalizeBaseUrl(url: string): string {
  let trimmed = url.trim();
  if (!trimmed) return '';
  if (!/^https?:\/\//i.test(trimmed)) {
    trimmed = `http://${trimmed}`;
  }
  return trimmed.replace(/\/+$/, '');
}

export async function getBaseUrl(): Promise<string> {
  try {
    const stored = await SecureStore.getItemAsync(BASE_URL_KEY);
    return stored ? normalizeBaseUrl(stored) : '';
  } catch {
    return '';
  }
}

export async function saveBaseUrl(url: string): Promise<void> {
  const normalized = normalizeBaseUrl(url);
  await SecureStore.setItemAsync(BASE_URL_KEY, normalized);
}

export async function clearBaseUrl(): Promise<void> {
  try {
    await SecureStore.deleteItemAsync(BASE_URL_KEY);
  } catch {
    // Ignore clear error
  }
}

export async function testConnection(url: string): Promise<{ success: boolean; error?: string }> {
  const normalized = normalizeBaseUrl(url);
  if (!normalized) {
    return { success: false, error: 'Please enter a server URL.' };
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 6000);

  try {
    // Try /health first
    const res = await fetch(`${normalized}/health`, {
      method: 'GET',
      signal: controller.signal,
    });

    if (res.ok) {
      clearTimeout(timeoutId);
      return { success: true };
    }

    // Try /api/runtime/status as fallback with the same timeout signal
    const altRes = await fetch(`${normalized}/api/runtime/status`, {
      method: 'GET',
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (altRes.ok) {
      return { success: true };
    }

    return {
      success: false,
      error: `Server responded with status HTTP ${res.status}.`,
    };
  } catch (err: unknown) {
    clearTimeout(timeoutId);
    if (err instanceof Error && err.name === 'AbortError') {
      return {
        success: false,
        error: 'Connection timed out. Make sure the server is running and reachable on this Wi-Fi network.',
      };
    }
    return {
      success: false,
      error: 'Could not connect to server. Check IP address, port, and Wi-Fi connection.',
    };
  }
}

export async function apiFetch(path: string, options?: RequestInit): Promise<Response> {
  const base = await getBaseUrl();
  if (!base) {
    throw new Error('No server URL configured. Please set server address.');
  }
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
