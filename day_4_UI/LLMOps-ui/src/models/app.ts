import { type BaseResponse } from '@/models/base.ts'
import { type SessionSettings } from '@/models/session.ts'

export type DebugAppResponse = BaseResponse<{
  content: string
  message: {
    role: 'assistant'
    content: string
  }
}>

export type CompletionSettings = Partial<SessionSettings>
