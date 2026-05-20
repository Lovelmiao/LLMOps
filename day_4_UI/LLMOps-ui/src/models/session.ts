import { type BaseResponse } from '@/models/base.ts'

export type ChatSession = {
  id: string
  title: string
  created_at: string
  updated_at: string
}

export type ChatMessage = {
  id?: string
  role: 'user' | 'assistant'
  content: string
  created_at?: string
}

export type SessionListResponse = BaseResponse<{
  sessions: ChatSession[]
}>

export type SessionDetailResponse = BaseResponse<{
  session: ChatSession
  messages: ChatMessage[]
}>

export type CreateSessionResponse = BaseResponse<{
  session: ChatSession
}>

export type DocumentMetadata = {
  title: string
  author: string
  year: string
  keywords: string
  source: string
  tags: string[]
}

export type LoadedDocument = {
  id: string
  filename: string
  content_type: string
  size: number
  status: 'processing' | 'ready' | 'failed'
  metadata: DocumentMetadata
  created_at: string
}

export type SessionSettings = {
  model: string
  temperature: number
  top_p: number
  retrieval_top_k: number
  namespace: string
  enable_web_search: boolean
}

export type DocumentListResponse = BaseResponse<{
  documents: LoadedDocument[]
}>

export type UploadDocumentsResponse = BaseResponse<{
  documents: LoadedDocument[]
}>

export type SessionSettingsResponse = BaseResponse<{
  settings: SessionSettings
}>
