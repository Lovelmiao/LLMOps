import { get, post } from '@/utils/request.ts'
import { type AuthResponse } from '@/models/auth.ts'

export const register = (username: string, password: string) => {
  return post<AuthResponse>('/auth/register', {
    body: { username, password },
  })
}

export const login = (username: string, password: string) => {
  return post<AuthResponse>('/auth/login', {
    body: { username, password },
  })
}

export const logout = () => {
  return post<AuthResponse>('/auth/logout')
}

export const getCurrentUser = () => {
  return get<AuthResponse>('/auth/me')
}
