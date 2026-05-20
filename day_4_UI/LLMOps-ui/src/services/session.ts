import { del, get, patch, post } from '@/utils/request.ts'
import {
  type CreateSessionResponse,
  type DocumentListResponse,
  type DocumentMetadata,
  type SessionDetailResponse,
  type SessionListResponse,
  type SessionSettings,
  type SessionSettingsResponse,
  type UploadDocumentsResponse,
} from '@/models/session.ts'

export const createSession = (title = '新的论文研究会话') => {
  return post<CreateSessionResponse>('/sessions', {
    body: { title },
  })
}

export const listSessions = () => {
  return get<SessionListResponse>('/sessions')
}

export const getSession = (sessionId: string) => {
  return get<SessionDetailResponse>(`/sessions/${sessionId}`)
}

export const updateSession = (sessionId: string, title: string) => {
  return patch<CreateSessionResponse>(`/sessions/${sessionId}`, {
    body: { title },
  })
}

export const deleteSession = (sessionId: string) => {
  return del(`/sessions/${sessionId}`)
}

export const listDocuments = (sessionId: string) => {
  return get<DocumentListResponse>(`/sessions/${sessionId}/documents`)
}

export const uploadDocuments = (
  sessionId: string,
  files: File[],
  metadata: DocumentMetadata,
) => {
  const formData = new FormData()
  files.forEach((file) => formData.append('files', file))
  formData.append('metadata', JSON.stringify(metadata))

  return post<UploadDocumentsResponse>(`/sessions/${sessionId}/documents`, {
    body: formData,
  })
}

export const deleteDocument = (sessionId: string, documentId: string) => {
  return del(`/sessions/${sessionId}/documents/${documentId}`)
}

export const getSessionSettings = (sessionId: string) => {
  return get<SessionSettingsResponse>(`/sessions/${sessionId}/settings`)
}

export const updateSessionSettings = (sessionId: string, settings: SessionSettings) => {
  return patch<SessionSettingsResponse>(`/sessions/${sessionId}/settings`, {
    body: settings,
  })
}

export const deleteMessagePair = (sessionId: string, messageId: string) => {
  return del(`/sessions/${sessionId}/messages/${messageId}`)
}
