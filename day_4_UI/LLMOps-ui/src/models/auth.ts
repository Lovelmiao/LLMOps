import { type BaseResponse } from '@/models/base.ts'

export type User = {
  id: string
  username: string
  email?: string
  avatar_url?: string
}

export type AuthResponse = BaseResponse<{
  user: User | null
}>

export type AccountProfilePayload = {
  username: string
  email: string
  avatar_url: string
}

export type PasswordResetPayload = {
  old_password: string
  new_password: string
}
