import { API_BASE } from './orchestrator';

const AUTH_API_ROOT = `${API_BASE.replace(/\/$/, '')}/api/auth`;
const TOKEN_KEY = 'archon_token';
const USER_KEY = 'archon_user';

export interface AuthUser {
  id: number;
  email: string;
  name: string;
}

interface AuthPayload {
  user: AuthUser;
  token?: string;
  access_token?: string;
}

function getErrorMessage(body: unknown, fallback: string) {
  if (body && typeof body === 'object' && 'error' in body && typeof body.error === 'string') {
    return body.error;
  }
  if (typeof body === 'string' && body.trim()) {
    return body;
  }
  return fallback;
}

async function parseBody(response: Response) {
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return response.json();
  }
  return response.text();
}

function persistAuth(payload: AuthPayload) {
  const token = payload.token || payload.access_token;
  if (!token) {
    throw new Error('Authentication response did not include a token');
  }

  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(payload.user));
  return payload.user;
}

async function authRequest(path: string, body: Record<string, unknown>, fallback: string) {
  const response = await fetch(`${AUTH_API_ROOT}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const payload = (await parseBody(response)) as AuthPayload | { error?: string } | string;

  if (!response.ok) {
    throw new Error(getErrorMessage(payload, fallback));
  }

  return persistAuth(payload as AuthPayload);
}

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): AuthUser | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;

  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function clearStoredSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export async function fetchCurrentUser() {
  const token = getStoredToken();
  if (!token) {
    throw new Error('No active session');
  }

  const response = await fetch(`${AUTH_API_ROOT}/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const payload = (await parseBody(response)) as AuthUser | { error?: string } | string;

  if (!response.ok) {
    throw new Error(getErrorMessage(payload, 'Unable to load your account'));
  }

  localStorage.setItem(USER_KEY, JSON.stringify(payload));
  return payload as AuthUser;
}

export async function loginWithPassword(email: string, password: string) {
  return authRequest('/login', { email, password }, 'Sign in failed');
}

export async function registerWithPassword({
  email,
  password,
  name,
  guestProjectId,
}: {
  email: string;
  password: string;
  name: string;
  guestProjectId?: string | null;
}) {
  return authRequest(
    '/register',
    {
      email,
      password,
      name,
      guest_project_id: guestProjectId || undefined,
    },
    'Account creation failed'
  );
}

export async function loginWithGoogle(credential: string, guestProjectId?: string | null) {
  return authRequest(
    '/google',
    {
      token: credential,
      guest_project_id: guestProjectId || undefined,
    },
    'Google sign-in failed'
  );
}

export async function claimGuestProject(projectId: string) {
  const token = getStoredToken();
  if (!token) {
    throw new Error('No active session');
  }

  const response = await fetch(`${API_BASE.replace(/\/$/, '')}/api/projects/${projectId}/claim`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const payload = await parseBody(response);

  if (!response.ok) {
    throw new Error(getErrorMessage(payload, 'Unable to claim this project'));
  }

  return payload;
}

export async function logout() {
  const token = getStoredToken();
  if (token) {
    try {
      await fetch(`${AUTH_API_ROOT}/logout`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
    } catch {
      // Best effort: clear local session even if the network call fails.
    }
  }

  clearStoredSession();
}
