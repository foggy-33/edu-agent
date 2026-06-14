export interface AuthUser {
  username: string
  display_name: string
  created_at: string
}

interface AuthResponse {
  token: string
  user: AuthUser
}

const TOKEN_KEY = 'studyflow_auth_token'

async function authRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem(TOKEN_KEY)
  const response = await fetch(`/api/auth/${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options?.headers || {})
    }
  })
  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new Error(data?.detail || '认证请求失败')
  }
  return response.status === 204 ? (undefined as T) : response.json()
}

export async function register(username: string, displayName: string, password: string): Promise<AuthUser> {
  const result = await authRequest<AuthResponse>('register', {
    method: 'POST',
    body: JSON.stringify({ username, display_name: displayName, password })
  })
  localStorage.setItem(TOKEN_KEY, result.token)
  return result.user
}

export async function login(username: string, password: string): Promise<AuthUser> {
  const result = await authRequest<AuthResponse>('login', {
    method: 'POST',
    body: JSON.stringify({ username, password })
  })
  localStorage.setItem(TOKEN_KEY, result.token)
  return result.user
}

export async function getCurrentUser(): Promise<AuthUser | null> {
  if (!localStorage.getItem(TOKEN_KEY)) return null
  try {
    return (await authRequest<{ user: AuthUser }>('me')).user
  } catch {
    localStorage.removeItem(TOKEN_KEY)
    return null
  }
}

export async function logout(): Promise<void> {
  try {
    await authRequest<void>('logout', { method: 'POST' })
  } finally {
    localStorage.removeItem(TOKEN_KEY)
  }
}
