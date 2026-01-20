import { ApiError, UnauthorizedError, type ValidationErrorPayload } from './errors';

const DEFAULT_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

function joinUrl(base: string, path: string): string {
  if (!base) return path;
  return base.replace(/\/$/, '') + path;
}

async function readErrorBody(res: Response): Promise<unknown> {
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) {
    try {
      return await res.json();
    } catch {
      return undefined;
    }
  }
  try {
    return await res.text();
  } catch {
    return undefined;
  }
}

export async function apiFetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const url = joinUrl(DEFAULT_BASE_URL, path);

  const res = await fetch(url, {
    ...init,
    credentials: 'include',
    headers: {
      'Accept': 'application/json',
      ...(init?.headers ?? {}),
    },
  });

  if (res.status === 401) throw new UnauthorizedError();

  if (!res.ok) {
    const body = (await readErrorBody(res)) as ValidationErrorPayload | string | undefined;
    const msg = typeof body === 'string' ? body : body?.detail || 'Request failed';
    throw new ApiError(msg, res.status);
  }

  return (await res.json()) as T;
}

export async function apiPostJson<T>(path: string, body: unknown): Promise<T> {
  return apiFetchJson<T>(path, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });
}

export async function apiDeleteJson<T>(path: string): Promise<T> {
  return apiFetchJson<T>(path, { method: 'DELETE' });
}

export async function apiPostForm<T>(path: string, form: FormData): Promise<T> {
  const url = joinUrl(DEFAULT_BASE_URL, path);

  const res = await fetch(url, {
    method: 'POST',
    credentials: 'include',
    body: form,
  });

  if (res.status === 401) throw new UnauthorizedError();
  if (!res.ok) {
    const body = await readErrorBody(res);
    const msg = typeof body === 'string' ? body : (body as any)?.detail || 'Request failed';
    throw new ApiError(msg, res.status);
  }

  return (await res.json()) as T;
}
