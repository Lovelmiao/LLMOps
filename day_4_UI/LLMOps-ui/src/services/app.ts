import { post } from '@/utils/request.ts'
import { type CompletionSettings, type DebugAppResponse } from '@/models/app.ts'

export const debugApp = (app_id: string, user_input: string, settings?: CompletionSettings) => {
  return post<DebugAppResponse>(`/sessions/${app_id}/messages`, {
    body: { user_input, settings },
  })
}
