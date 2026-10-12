export type Role = 'administrador' | 'docente' | 'estudiante';
export interface User { id: string; nombre: string; correo: string; rol: Role; estado: string }
export interface Course { id: string; nombre: string; estado: string; docenteId?: string; descripcion?:string; docente?:{id:string;nombre:string;correo:string};materialCount?:number }
export interface ApiError extends Error { status?: number; code?: string }

const readCookie = (name: string) => document.cookie.split('; ').find(row => row.startsWith(`${name}=`))?.split('=').slice(1).join('=') ?? '';
let accessToken = sessionStorage.getItem('monda_token') ?? '';
export const setToken = (token: string) => { accessToken = token; if (token) sessionStorage.setItem('monda_token', token); else sessionStorage.removeItem('monda_token'); };

async function decode<T>(response: Response): Promise<T> {
  if (response.status === 204) return undefined as T;
  const ct = response.headers.get('content-type') ?? '';
  const body = ct.includes('json') ? await response.json() : await response.text();
  if (!response.ok) {
    const detail = typeof body === 'object' && body ? (body.message ?? body.detail?.message ?? body.detail ?? body.code) : body;
    const error = new Error(String(detail || `Error HTTP ${response.status}`)) as ApiError;
    error.status = response.status; error.code = typeof body === 'object' && body ? body.code : undefined; throw error;
  }
  return body as T;
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`);
  if (init.body && !(init.body instanceof FormData) && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  let response = await fetch(path, { ...init, headers, credentials: 'same-origin' });
  if (response.status === 401 && !path.startsWith('/api/auth/')) {
    const csrf = decodeURIComponent(readCookie('monda_csrf'));
    if (csrf) {
      const refresh = await fetch('/api/auth/refresh', { method: 'POST', credentials: 'same-origin', headers: { 'X-CSRF-Token': csrf } });
      if (refresh.ok) { const data = await refresh.json(); const expected=JSON.parse(sessionStorage.getItem('monda_user')||'null'); if(expected&&data.user?.id!==expected.id){setToken('');throw new Error('La sesión cambió en otra pestaña. Cierra sesión e ingresa con tu cuenta.');} setToken(data.accessToken); const retry = new Headers(headers); retry.set('Authorization', `Bearer ${data.accessToken}`); response = await fetch(path, { ...init, headers: retry, credentials: 'same-origin' }); }
    }
  }
  return decode<T>(response);
}
export const post = <T>(path: string, body?: unknown, headers?: HeadersInit) => api<T>(path, { method: 'POST', headers, body: body === undefined ? undefined : JSON.stringify(body) });
export const patch = <T>(path: string, body: unknown) => api<T>(path, { method: 'PATCH', body: JSON.stringify(body) });
export function logoutLocal() { setToken(''); sessionStorage.removeItem('monda_user'); }
export async function raw(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers); if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`);
  const response = await fetch(path, { ...init, headers, credentials: 'same-origin' });
  if (!response.ok) { const ct=response.headers.get('content-type')??''; let message=`Error HTTP ${response.status}`; try { const b=ct.includes('json')?await response.json():await response.text(); message=typeof b==='object'?(b.message??b.detail?.message??b.detail??message):b; } catch {} throw new Error(String(message)); }
  return response;
}
