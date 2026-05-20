<script setup lang="ts">
import { nextTick, ref, watch, onBeforeUnmount } from 'vue'
import { Message } from '@arco-design/web-vue'
import { useRoute } from 'vue-router'
import { debugApp } from '@/services/app.ts'
import { getCurrentUser } from '@/services/auth.ts'
import {
  deleteDocument,
  deleteMessagePair,
  getSession,
  getSessionSettings,
  listDocuments,
  updateSessionSettings,
  uploadDocuments,
} from '@/services/session.ts'
import {
  type ChatMessage,
  type ChatSession,
  type DocumentMetadata,
  type LoadedDocument,
  type SessionSettings,
} from '@/models/session.ts'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'

const defaultMetadata: DocumentMetadata = {
  title: '',
  author: '',
  year: '',
  keywords: '',
  source: 'local_upload',
  tags: [],
}

const defaultSettings: SessionSettings = {
  model: 'bailu-2.7',
  temperature: 0,
  top_p: 1,
  retrieval_top_k: 3,
  namespace: 'ReID',
  enable_web_search: true,
}

const route = useRoute()
const userInput = ref('')
const messages = ref<ChatMessage[]>([])
const documents = ref<LoadedDocument[]>([])
const settings = ref<SessionSettings>({ ...defaultSettings })
const metadata = ref<DocumentMetadata>({ ...defaultMetadata })
const metadataTags = ref('')
const currentSession = ref<ChatSession | null>(null)
const isLoading = ref(false)
const historyLoading = ref(false)
const uploading = ref(false)
const settingsVisible = ref(false)
const dragging = ref(false)
let dragCounter = 0
const messagePanel = ref<HTMLElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const userInitial = ref('U')

// 编辑消息相关状态
const editingMessageIndex = ref<number | null>(null)
const editingContent = ref('')

// 流式输出相关状态
const streamingContent = ref('')
const isStreaming = ref(false)
let streamingTimer: ReturnType<typeof setInterval> | null = null

// 加载提示信息
const loadingTips = [
  'AI 正在阅读您的问题...',
  '正在检索相关论文内容...',
  'AI 正在组织回答...',
  '正在分析论文数据...',
  '即将为您生成回答...',
  '请稍候，AI 正在思考...',
]
const currentTipIndex = ref(0)
let tipTimer: ReturnType<typeof setInterval> | null = null

const getSessionId = () => route.params.session_id as string

const loadUser = async () => {
  try {
    const response = await getCurrentUser()
    const u = response.data.user
    userInitial.value = u?.username?.slice(0, 1).toUpperCase() || 'U'
  } catch {
    // ignore
  }
}

const getAssistantContent = (data: { content?: string; message?: { content?: string } }) => {
  return data.message?.content || data.content || ''
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagePanel.value) {
    messagePanel.value.scrollTop = messagePanel.value.scrollHeight
  }
}

const loadSession = async () => {
  const sessionId = getSessionId()
  if (!sessionId) return

  historyLoading.value = true
  try {
    const response = await getSession(sessionId)
    currentSession.value = response.data.session
    messages.value = response.data.messages
    scrollToBottom()
  } finally {
    historyLoading.value = false
  }
}

const loadDocuments = async () => {
  const sessionId = getSessionId()
  if (!sessionId) return

  const response = await listDocuments(sessionId)
  documents.value = response.data.documents
}

const loadSettings = async () => {
  const sessionId = getSessionId()
  if (!sessionId) return

  const response = await getSessionSettings(sessionId)
  settings.value = { ...defaultSettings, ...response.data.settings }
}

const refreshSideData = async () => {
  await Promise.all([loadDocuments(), loadSettings()])
}

const openSettings = async () => {
  settingsVisible.value = true
  await refreshSideData()
}

const pickFiles = () => {
  fileInput.value?.click()
}

const buildMetadata = () => ({
  ...metadata.value,
  tags: metadataTags.value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean),
})

const handleFiles = async (fileList: FileList | File[]) => {
  const files = Array.from(fileList)
  if (!files.length) return

  uploading.value = true
  try {
    const response = await uploadDocuments(getSessionId(), files, buildMetadata())
    documents.value = response.data.documents
    Message.success(`已加载 ${files.length} 个文件`)
  } finally {
    uploading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files) handleFiles(target.files)
}

const handleDragEnter = (event: DragEvent) => {
  event.preventDefault()
  dragCounter++
  dragging.value = true
}

const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
}

const handleDragLeave = (event: DragEvent) => {
  event.preventDefault()
  dragCounter--
  if (dragCounter <= 0) {
    dragCounter = 0
    dragging.value = false
  }
}

const handleDrop = (event: DragEvent) => {
  dragCounter = 0
  dragging.value = false
  if (event.dataTransfer?.files) {
    handleFiles(event.dataTransfer.files)
  }
}

const removeDocument = async (documentId: string) => {
  await deleteDocument(getSessionId(), documentId)
  await loadDocuments()
  Message.success('文件已删除')
}

const saveSettings = async () => {
  const response = await updateSessionSettings(getSessionId(), settings.value)
  settings.value = response.data.settings
  Message.success('设置已保存')
}

/** 流式输出模拟：逐字显示文本 */
const startStreaming = (fullText: string): Promise<void> => {
  return new Promise((resolve) => {
    streamingContent.value = ''
    isStreaming.value = true
    let charIndex = 0

    const speed = 5 // 每个字符的间隔毫秒数

    streamingTimer = setInterval(() => {
      if (charIndex < fullText.length) {
        streamingContent.value += fullText[charIndex]
        charIndex++
        scrollToBottom()
      } else {
        if (streamingTimer) clearInterval(streamingTimer)
        streamingTimer = null
        isStreaming.value = false
        resolve()
      }
    }, speed)
  })
}

const send = async () => {
  const content = userInput.value.trim()
  if (!content) {
    Message.error('用户提问不能为空')
    return
  }
  if (isLoading.value || isStreaming.value) {
    Message.error('上一轮回答还在生成中')
    return
  }

  const sessionId = getSessionId()
  messages.value.push({ role: 'user', content })
  userInput.value = ''
  isLoading.value = true
  currentTipIndex.value = 0
  scrollToBottom()

  // 启动加载提示轮播
  startTipRotation()

  try {
    const response = await debugApp(sessionId, content, settings.value)
    const assistantContent = getAssistantContent(response.data)
    if (!assistantContent) {
      Message.warning('AI 已返回响应，但没有可展示的文本内容')
      isLoading.value = false
      stopTipRotation()
      return
    }

    isLoading.value = false
    stopTipRotation()

    // 流式输出：逐字显示
    await startStreaming(assistantContent)

    // 流式输出完成后，将完整内容存入消息列表
    messages.value.push({
      role: 'assistant',
      content: assistantContent,
    })
    streamingContent.value = ''
    await loadSession()
    scrollToBottom()
  } catch (err) {
    console.error('请求失败:', err)
    Message.error('请求失败，请重试')
    streamingContent.value = ''
    isStreaming.value = false
    if (streamingTimer) {
      clearInterval(streamingTimer)
      streamingTimer = null
    }
  } finally {
    isLoading.value = false
    stopTipRotation()
  }
}

/** 开始加载提示轮播 */
const startTipRotation = () => {
  tipTimer = setInterval(() => {
    currentTipIndex.value = (currentTipIndex.value + 1) % loadingTips.length
  }, 3000)
}

/** 停止加载提示轮播 */
const stopTipRotation = () => {
  if (tipTimer) {
    clearInterval(tipTimer)
    tipTimer = null
  }
}

/** 开始编辑用户消息 */
const startEditMessage = (index: number) => {
  const msg = messages.value[index]
  if (msg.role !== 'user') return
  editingMessageIndex.value = index
  editingContent.value = msg.content
}

/** 取消编辑 */
const cancelEdit = () => {
  editingMessageIndex.value = null
  editingContent.value = ''
}

/** 提交编辑后的消息（删除旧消息对，重新发送） */
const submitEdit = async (index: number) => {
  const newContent = editingContent.value.trim()
  if (!newContent) {
    Message.error('消息内容不能为空')
    return
  }
  if (isLoading.value || isStreaming.value) {
    Message.error('上一轮回答还在生成中')
    return
  }

  const sessionId = getSessionId()
  const oldMessage = messages.value[index]

  // 取消编辑状态
  editingMessageIndex.value = null
  editingContent.value = ''

  // 找到旧的AI回复（紧随其后的assistant消息）
  const assistantIndex = index + 1
  const hasAssistantReply =
    assistantIndex < messages.value.length && messages.value[assistantIndex].role === 'assistant'

  // 从界面上移除旧消息和旧回复
  if (hasAssistantReply) {
    messages.value.splice(index, 2)
  } else {
    messages.value.splice(index, 1)
  }

  // 从数据库中删除旧消息对
  if (oldMessage.id) {
    try {
      await deleteMessagePair(sessionId, oldMessage.id)
    } catch (err) {
      console.error('删除旧消息失败:', err)
    }
  }

  // 重新发送编辑后的新消息
  messages.value.push({ role: 'user', content: newContent })
  isLoading.value = true
  currentTipIndex.value = 0
  scrollToBottom()

  // 启动加载提示轮播
  startTipRotation()

  try {
    const response = await debugApp(sessionId, newContent, settings.value)
    const assistantContent = getAssistantContent(response.data)
    if (!assistantContent) {
      Message.warning('AI 已返回响应，但没有可展示的文本内容')
      isLoading.value = false
      stopTipRotation()
      return
    }

    isLoading.value = false
    stopTipRotation()

    // 流式输出
    await startStreaming(assistantContent)

    messages.value.push({
      role: 'assistant',
      content: assistantContent,
    })
    streamingContent.value = ''
    await loadSession()
    scrollToBottom()
  } catch (err) {
    console.error('请求失败:', err)
    Message.error('请求失败，请重试')
    streamingContent.value = ''
    isStreaming.value = false
    if (streamingTimer) {
      clearInterval(streamingTimer)
      streamingTimer = null
    }
  } finally {
    isLoading.value = false
    stopTipRotation()
  }
}

/** 编辑区域按键处理 */
const handleEditKeydown = (event: KeyboardEvent, index: number) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    submitEdit(index)
  } else if (event.key === 'Escape') {
    cancelEdit()
  }
}

watch(
  () => route.params.session_id,
  async () => {
    await loadSession()
    await refreshSideData()
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  if (streamingTimer) {
    clearInterval(streamingTimer)
    streamingTimer = null
  }
  if (tipTimer) {
    clearInterval(tipTimer)
    tipTimer = null
  }
})

loadUser()
</script>

<template>
  <div class="chat-shell">
    <header class="chat-header">
      <div>
        <div class="chat-title">
          {{ currentSession?.title || '论文研究会话' }}
        </div>
        <div class="chat-subtitle">基于本地论文库和检索增强生成</div>
      </div>
      <a-button class="icon-btn-circle" @click="openSettings">
        <template #icon>
          <icon-settings />
        </template>
      </a-button>
    </header>

    <div
      ref="messagePanel"
      class="message-panel"
      :class="{ 'drag-active': dragging }"
      @dragenter="handleDragEnter"
      @dragover="handleDragOver"
      @dragleave="handleDragLeave"
      @drop.prevent="handleDrop"
    >
      <div v-if="dragging" class="drop-mask">
        <icon-upload />
        <span>释放文件并加载到当前会话</span>
      </div>

      <a-spin :loading="historyLoading" class="message-spin">
        <div class="message-list">
          <div
            v-for="(message, index) in messages"
            :key="message.id || `${message.role}-${index}`"
            class="message-row"
            :class="message.role === 'user' ? 'message-row-user' : 'message-row-assistant'"
          >
            <a-avatar v-if="message.role === 'assistant'" class="avatar" :size="34">
              <icon-book />
            </a-avatar>
            <div class="message-content-wrapper">
              <!-- 用户消息：普通文本或编辑模式 -->
              <div v-if="message.role === 'user'">
                <div v-if="editingMessageIndex === index" class="edit-wrapper">
                  <a-textarea
                    v-model="editingContent"
                    :auto-size="{ minRows: 1, maxRows: 6 }"
                    class="edit-textarea"
                    @keydown="handleEditKeydown($event, index)"
                  />
                  <div class="edit-actions">
                    <a-button size="mini" type="primary" @click="submitEdit(index)">
                      <template #icon><icon-send /></template>
                      重新发送
                    </a-button>
                    <a-button size="mini" @click="cancelEdit">取消</a-button>
                    <span class="edit-hint">Enter 发送 · Esc 取消</span>
                  </div>
                </div>
                <div
                  v-else
                  class="message-bubble bubble-user"
                  @dblclick="startEditMessage(index)"
                >
                  {{ message.content }}
                  <div class="edit-hint-text">双击可编辑</div>
                </div>
              </div>

              <!-- AI回复：Markdown渲染 -->
              <div v-else>
                <div class="message-bubble bubble-assistant">
                  <MarkdownRenderer :content="message.content" />
                </div>
              </div>
            </div>
            <a-avatar
              v-if="message.role === 'user'"
              :style="{ backgroundColor: '#2563eb' }"
              class="avatar"
              :size="34"
            >
              {{ userInitial }}
            </a-avatar>
          </div>

          <!-- 流式输出中的消息 -->
          <div v-if="isStreaming && streamingContent" class="message-row message-row-assistant">
            <a-avatar class="avatar" :size="34">
              <icon-book />
            </a-avatar>
            <div class="message-content-wrapper">
              <div class="message-bubble bubble-assistant">
                <MarkdownRenderer :content="streamingContent" />
                <span class="streaming-cursor" />
              </div>
            </div>
          </div>

          <!-- 加载中状态 -->
          <div v-if="isLoading" class="message-row message-row-assistant">
            <a-avatar class="avatar" :size="34">
              <icon-book />
            </a-avatar>
            <div class="typing-bubble">
              <div class="typing-content">
                <icon-loading />
                <span class="typing-text">{{ loadingTips[currentTipIndex] }}</span>
              </div>
            </div>
          </div>

          <div v-if="!messages.length && !historyLoading" class="empty-state">
            <div class="empty-icon">
              <icon-search size="30" />
            </div>
            <div class="empty-title">向论文库提问</div>
            <div class="empty-desc">例如：请总结 MDReID 的核心贡献和实验结论。</div>
          </div>
        </div>
      </a-spin>
    </div>

    <footer class="chat-footer">
      <div class="composer">
        <input ref="fileInput" class="hidden-file" type="file" multiple @change="handleFileChange" />
        <a-button class="load-btn" :loading="uploading" @click="pickFiles">
          <template #icon>
            <icon-plus />
          </template>
        </a-button>
        <a-textarea
          v-model="userInput"
          placeholder="输入你的论文研究问题..."
          :auto-size="{ minRows: 1, maxRows: 5 }"
          @keydown.enter.exact.prevent="send"
        />
        <a-button type="primary" :loading="isLoading || isStreaming" @click="send">
          <template #icon>
            <icon-send />
          </template>
          发送
        </a-button>
      </div>
      <div class="footer-tip">内容由 AI 生成，请结合论文原文核验。双击用户消息可编辑重新发送。</div>
    </footer>

    <a-drawer v-model:visible="settingsVisible" width="420px" title="会话设置" unmount-on-close>
      <a-tabs default-active-key="documents">
        <a-tab-pane key="documents" title="文件">
          <div class="drawer-section">
            <div class="section-title">加载文件</div>
            <div class="upload-zone" @click="pickFiles" @dragover.prevent @drop.prevent="handleDrop">
              <icon-upload />
              <span>点击选择或拖拽文件到这里</span>
            </div>
            <a-input v-model="metadata.title" placeholder="标题" />
            <a-input v-model="metadata.author" placeholder="作者" />
            <a-input v-model="metadata.year" placeholder="年份" />
            <a-input v-model="metadata.keywords" placeholder="关键词" />
            <a-input v-model="metadata.source" placeholder="来源" />
            <a-input v-model="metadataTags" placeholder="标签，使用英文逗号分隔" />
          </div>

          <div class="drawer-section">
            <div class="section-title">已加载文件</div>
            <a-empty v-if="!documents.length" description="暂无文件" />
            <div v-for="item in documents" :key="item.id" class="document-item">
              <div class="document-main">
                <icon-file />
                <div class="document-text">
                  <div class="document-name">{{ item.metadata.title || item.filename }}</div>
                  <div class="document-meta">{{ item.status }} · {{ Math.ceil(item.size / 1024) }} KB</div>
                </div>
              </div>
              <a-button status="danger" class="delete-btn" @click="removeDocument(item.id)">
                <template #icon>
                  <icon-delete />
                </template>
              </a-button>
            </div>
          </div>
        </a-tab-pane>

        <a-tab-pane key="model" title="模型">
          <div class="drawer-section">
            <div class="section-title">模型参数</div>
            <label class="field-label">模型</label>
            <a-input v-model="settings.model" placeholder="模型名称" />
            <label class="field-label">Temperature</label>
            <a-input-number v-model="settings.temperature" :min="0" :max="2" :step="0.1" />
            <label class="field-label">Top P</label>
            <a-input-number v-model="settings.top_p" :min="0" :max="1" :step="0.1" />
            <label class="field-label">检索 Top K</label>
            <a-input-number v-model="settings.retrieval_top_k" :min="1" :max="20" :step="1" />
            <label class="field-label">Namespace</label>
            <a-input v-model="settings.namespace" placeholder="向量库命名空间" />
            <div class="switch-row">
              <span>启用联网搜索</span>
              <a-switch v-model="settings.enable_web_search" />
            </div>
            <a-button type="primary" long @click="saveSettings">
              <template #icon>
                <icon-save />
              </template>
              保存设置
            </a-button>
          </div>
        </a-tab-pane>
      </a-tabs>
    </a-drawer>
  </div>
</template>

<style scoped>
.chat-shell {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #fff;
}

.chat-header {
  height: 64px;
  flex-shrink: 0;
  padding: 0 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e2e8f0;
}

.chat-title {
  color: #020617;
  font-size: 18px;
  font-weight: 600;
}

.chat-subtitle,
.footer-tip,
.document-meta {
  color: #64748b;
  font-size: 12px;
}

.icon-btn-circle,
.load-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  flex-shrink: 0;
}

.message-panel {
  position: relative;
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
  background: #f8fafc;
}

.message-spin,
.message-list {
  width: 100%;
  min-height: 100%;
}

.message-list {
  max-width: 860px;
  margin: 0 auto;
}

.message-row {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  padding: 4px;
  border-radius: 8px;
}

.message-row-user {
  justify-content: flex-end;
}

.message-row-assistant {
  justify-content: flex-start;
  margin-right: 0;
  padding-right: 0;
}

.avatar {
  flex-shrink: 0;
}

.message-content-wrapper {
  position: relative;
  max-width: 72%;
}

.message-row-user .message-content-wrapper {
  margin-left: auto;
}

.message-row-assistant .message-content-wrapper {
  margin-right: 0;
}

.message-bubble {
  border-radius: 12px;
  border: 1px solid;
  padding: 12px 16px;
  line-height: 1.75;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.bubble-user {
  color: #fff;
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  border-color: #2563eb;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  position: relative;
  cursor: pointer;
}

.bubble-user:hover .edit-hint-text {
  opacity: 1;
}

.edit-hint-text {
  position: absolute;
  bottom: -20px;
  right: 0;
  font-size: 11px;
  color: #94a3b8;
  opacity: 0;
  transition: opacity 0.2s;
  pointer-events: none;
}

.bubble-assistant {
  color: #1e293b;
  background: #fff;
  border-color: #e2e8f0;
  border: 1px solid #e2e8f0;
  white-space: normal;
  overflow-wrap: anywhere;
  max-width: 100%;
}

.typing-bubble {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px 16px;
  color: #1e293b;
  background: #fff;
}

.typing-content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.typing-text {
  color: #64748b;
  font-size: 14px;
  animation: fadeInOut 3s infinite;
}

@keyframes fadeInOut {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

/* 编辑模式样式 */
.edit-wrapper {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  border-radius: 12px;
  padding: 12px;
  border: 1px solid #2563eb;
}

.edit-textarea {
  width: 100%;
  border: none !important;
  background: rgba(255, 255, 255, 0.15) !important;
  color: #fff !important;
  border-radius: 8px;
  font-size: 14px;
  resize: none;
}

.edit-textarea :deep(textarea) {
  color: #fff !important;
  background: transparent !important;
  border: none !important;
}

.edit-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.edit-hint {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.6);
  margin-left: auto;
}

/* 流式光标 */
.streaming-cursor {
  display: inline-block;
  width: 2px;
  height: 16px;
  background: #2563eb;
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: blink 0.8s infinite;
}

@keyframes blink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}

.empty-state {
  min-height: 420px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.empty-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.empty-title {
  color: #020617;
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 8px;
}

.empty-desc {
  color: #64748b;
}

.drop-mask {
  position: absolute;
  inset: 16px;
  z-index: 5;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #2563eb;
  background: rgba(239, 246, 255, 0.88);
  border: 2px dashed #2563eb;
  border-radius: 12px;
  font-weight: 600;
  backdrop-filter: blur(4px);
}

.chat-footer {
  flex-shrink: 0;
  border-top: 1px solid #e2e8f0;
  background: #fff;
  padding: 16px 32px;
}

.composer {
  max-width: 860px;
  margin: 0 auto;
  display: flex;
  align-items: flex-end;
  gap: 12px;
}

.hidden-file {
  display: none;
}

.footer-tip {
  padding-top: 12px;
  text-align: center;
}

.drawer-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

.section-title {
  color: #0f172a;
  font-weight: 600;
}

.upload-zone {
  min-height: 96px;
  border: 2px dashed #cbd5e1;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #2563eb;
  cursor: pointer;
  background: #f8fafc;
  transition: all 0.2s ease;
}

.upload-zone:hover {
  border-color: #2563eb;
  background: #eff6ff;
}

.document-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 12px 14px;
  transition: all 0.2s ease;
}

.document-item:hover {
  border-color: #cbd5e1;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.document-main {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.document-text {
  min-width: 0;
}

.document-name {
  color: #0f172a;
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.delete-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  flex-shrink: 0;
}

.field-label {
  color: #475569;
  font-size: 13px;
}

.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 4px 0 8px;
}
</style>
