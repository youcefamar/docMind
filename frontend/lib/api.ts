export async function readApiPayload<T = unknown>(response: Response): Promise<T | null> {
  const raw = await response.text();
  if (!raw.trim()) return null;

  try {
    return JSON.parse(raw) as T;
  } catch {
    // Reverse proxies and development servers sometimes return plain text
    // (for example, "Internal Server Error") instead of JSON.
    return raw as T;
  }
}

export function getApiErrorMessage(payload: unknown, fallback: string): string {
  if (typeof payload === 'string') return payload.trim() || fallback;
  if (!payload || typeof payload !== 'object') return fallback;

  const record = payload as Record<string, unknown>;
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
