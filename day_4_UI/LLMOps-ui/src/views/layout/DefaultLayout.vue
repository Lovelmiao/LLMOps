<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Message, Modal } from '@arco-design/web-vue'
import { getCurrentUser, logout } from '@/services/auth.ts'
import { createSession, listSessions, updateSession, deleteSession as deleteSessionApi } from '@/services/session.ts'
import { clearLogin } from '@/utils/auth.ts'
import { type User } from '@/models/auth.ts'
import { type ChatSession } from '@/models/session.ts'

const router = useRouter()
const route = useRoute()
const sessions = ref<ChatSession[]>([])
const user = ref<User | null>(null)
const loading = ref(false)
const editingSessionId = ref<string | null>(null)
const editingTitle = ref('')
const dragSessionIndex = ref<number | null>(null)
const dragOverSessionIndex = ref<number | null>(null)

const loadSessions = async () => {
  loading.value = true
  try {
    const response = await listSessions()
    sessions.value = response.data.sessions
  } finally {
    loading.value = false
  }
}

const loadUser = async () => {
  const response = await getCurrentUser()
  user.value = response.data.user
}

const createNewSession = async () => {
  const response = await createSession()
  await loadSessions()
  router.push(`/sessions/${response.data.session.id}`)
}

const handleLogout = async () => {
  await logout()
  clearLogin()
  Message.success('已退出登录')
  router.push('/auth/login')
}

const startRename = (session: ChatSession) => {
  editingSessionId.value = session.id
  editingTitle.value = session.title || ''
}

const cancelRename = () => {
  editingSessionId.value = null
  editingTitle.value = ''
}

const confirmRename = async (sessionId: string) => {
  const title = editingTitle.value.trim()
  if (!title) {
    Message.error('标题不能为空')
    return
  }
  try {
    await updateSession(sessionId, title)
    const session = sessions.value.find(s => s.id === sessionId)
    if (session) session.title = title
    Message.success('重命名成功')
  } catch (err) {
    Message.error('重命名失败')
  } finally {
    cancelRename()
  }
}

const handleDeleteSession = async (sessionId: string, event: Event) => {
  event.stopPropagation()
  Modal.confirm({
    title: '确认删除',
    content: '删除后将无法恢复该会话及其所有消息，确定要删除吗？',
    okText: '删除',
    cancelText: '取消',
    okButtonProps: { status: 'danger' },
    onOk: async () => {
      try {
        await deleteSessionApi(sessionId)
        sessions.value = sessions.value.filter(s => s.id !== sessionId)
        if (route.params.session_id === sessionId) {
          router.push('/home')
        }
        Message.success('会话已删除')
      } catch (err) {
        Message.error('删除失败')
      }
    }
  })
}

const onSessionDragStart = (index: number, event: DragEvent) => {
  dragSessionIndex.value = index
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', String(index))
  }
}

const onSessionDragOver = (index: number, event: DragEvent) => {
  event.preventDefault()
  event.dataTransfer!.dropEffect = 'move'
  dragOverSessionIndex.value = index
}

const onSessionDragEnd = () => {
  if (dragSessionIndex.value !== null && dragOverSessionIndex.value !== null && dragSessionIndex.value !== dragOverSessionIndex.value) {
    const draggedItem = sessions.value[dragSessionIndex.value]
    sessions.value.splice(dragSessionIndex.value, 1)
    sessions.value.splice(dragOverSessionIndex.value, 0, draggedItem)
  }
  dragSessionIndex.value = null
  dragOverSessionIndex.value = null
}

onMounted(async () => {
  await Promise.all([loadSessions(), loadUser()])
})
</script>

<template>
  <div class="h-screen bg-slate-50 flex overflow-hidden">
    <aside class="sidebar w-[280px] shrink-0 bg-white border-r border-slate-200 flex flex-col">
      <div class="sidebar-header h-16 px-5 flex items-center justify-between border-b border-slate-200">
        <div>
          <div class="text-base font-semibold text-slate-950">论文研究 RAG</div>
          <div class="text-xs text-slate-500">多会话知识问答</div>
        </div>
        <a-button type="primary" class="new-session-btn" @click="createNewSession">
          <template #icon>
            <icon-plus />
          </template>
        </a-button>
      </div>

      <div class="px-3 py-3 flex-1 overflow-y-auto scrollbar-w-none">
        <a-spin :loading="loading" class="w-full">
          <div
            v-for="(item, index) in sessions"
            :key="item.id"
            class="session-item"
            :class="[
              route.params.session_id === item.id ? 'session-item-active' : 'session-item-inactive',
              { 'session-drag-over': dragOverSessionIndex === index, 'session-dragging': dragSessionIndex === index }
            ]"
            draggable="true"
            @click="router.push(`/sessions/${item.id}`)"
            @dragstart="onSessionDragStart(index, $event)"
            @dragover="onSessionDragOver(index, $event)"
            @dragend="onSessionDragEnd"
            @dblclick="startRename(item)"
          >
            <template v-if="editingSessionId === item.id">
              <a-input
                v-model="editingTitle"
                size="small"
                @press-enter="confirmRename(item.id)"
                @blur="cancelRename"
                @click.stop
                autofocus
              />
            </template>
            <template v-else>
              <div class="session-content">
                <div class="text-sm font-medium truncate">{{ item.title }}</div>
                <div class="text-xs text-slate-400 mt-1 truncate">
                  {{ new Date(item.updated_at).toLocaleString() }}
                </div>
              </div>
              <div class="session-actions">
                <a-tooltip content="重命名">
                  <a-button class="session-action-btn" size="mini" @click.stop="startRename(item)">
                    <template #icon><icon-edit /></template>
                  </a-button>
                </a-tooltip>
                <a-tooltip content="删除">
                  <a-button class="session-action-btn" size="mini" status="danger" @click.stop="handleDeleteSession(item.id, $event)">
                    <template #icon><icon-delete /></template>
                  </a-button>
                </a-tooltip>
              </div>
            </template>
          </div>
          <div v-if="!sessions.length && !loading" class="px-3 py-8 text-sm text-slate-500">
            点击右上角创建第一个研究会话。
          </div>
        </a-spin>
      </div>

      <div class="sidebar-footer border-t border-slate-200">
        <a-dropdown trigger="click" position="top">
          <button
            type="button"
            class="w-full flex items-center gap-3 rounded-md border border-slate-200 px-3 py-2 text-left hover:bg-slate-50 transition-colors"
          >
            <a-avatar :size="36" :style="{ backgroundColor: '#2563eb' }">
              {{ user?.username?.slice(0, 1).toUpperCase() || 'U' }}
            </a-avatar>
            <div class="min-w-0 flex-1">
              <div class="text-sm font-medium text-slate-900 truncate">{{ user?.username || '当前用户' }}</div>
              <div class="text-xs text-slate-500 truncate">已登录</div>
            </div>
            <icon-down />
          </button>
          <template #content>
            <a-doption @click="router.push('/user/settings')">
              <template #icon>
                <icon-settings />
              </template>
              账户设置
            </a-doption>
            <a-doption @click="handleLogout" class="text-red-500">
              <template #icon>
                <icon-export />
              </template>
              退出登录
            </a-doption>
          </template>
        </a-dropdown>
      </div>
    </aside>

    <main class="flex-1 min-w-0">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.sidebar {
  user-select: none;
}

.sidebar-header {
  height: 64px;
  flex-shrink: 0;
}

.sidebar-footer {
  flex-shrink: 0;
  padding: 16px 12px;
  box-sizing: border-box;
  display: flex;
  align-items: flex-end;
  height: 95px;
}

.new-session-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.session-item {
  position: relative;
  width: 100%;
  text-align: left;
  padding: 10px 12px;
  border-radius: 8px;
  margin-bottom: 4px;
  border: 1px solid transparent;
  transition: all 0.15s ease;
  cursor: grab;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.session-item:active {
  cursor: grabbing;
}

.session-item-inactive {
  background: #fff;
  color: #334155;
}

.session-item-inactive:hover {
  background: #f1f5f9;
  border-color: #e2e8f0;
}

.session-item-inactive:hover .session-actions {
  display: flex;
}

.session-item-active {
  background: #eff6ff;
  border-color: #bfdbfe;
  color: #1d4ed8;
}

.session-item-active:hover .session-actions {
  display: flex;
}

.session-dragging {
  opacity: 0.4;
}

.session-drag-over {
  border-color: #2563eb !important;
  background: #dbeafe !important;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
}

.session-content {
  min-width: 0;
  flex: 1;
}

.session-actions {
  display: none;
  gap: 2px;
  flex-shrink: 0;
}

.session-action-btn {
  width: 24px;
  height: 24px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  opacity: 0.8;
}

.session-action-btn:hover {
  opacity: 1;
}
</style>
