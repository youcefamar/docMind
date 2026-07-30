import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const backendBaseUrl = (process.env.BACKEND_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

function proxyError(status: number, detail: string, code: string) {
  return NextResponse.json({ detail, code }, { status });
}

export async function POST(request: NextRequest) {
  let requestBody: string;
  try {
    requestBody = await request.text();
  } catch {
    return proxyError(400, 'The chat request body could not be read.', 'invalid_chat_request');
  }

  try {
    const upstream = await fetch(`${backendBaseUrl}/api/ask`, {
      method: 'POST',
      headers: { 'content-type': request.headers.get('content-type') || 'application/json' },
      body: requestBody,
      cache: 'no-store',
    });
    const responseBody = await upstream.text();
    const contentType = upstream.headers.get('content-type') || '';

    if (contentType.includes('application/json')) {
      return new NextResponse(responseBody, {
        status: upstream.status,
        headers: { 'content-type': 'application/json' },
      });
    }

    if (!upstream.ok) {
      console.warn(`[CHAT_PROXY] backend returned status=${upstream.status}`);
      return proxyError(
        upstream.status,
        'The DocMind backend returned an error. Check the backend terminal for an [ASK] failed message.',
        'backend_error',
      );
    }

    return proxyError(
      502,
      'The DocMind backend returned an unexpected non-JSON response.',
      'invalid_backend_response',
    );
  } catch (error) {
    const reason = error instanceof Error ? error.message : 'unknown connection error';
    console.warn(`[CHAT_PROXY] backend unavailable reason=${reason}`);
    return proxyError(
      503,
      'The DocMind backend is temporarily unavailable. Wait a moment and try again.',
      'backend_unavailable',
    );
  }
}
