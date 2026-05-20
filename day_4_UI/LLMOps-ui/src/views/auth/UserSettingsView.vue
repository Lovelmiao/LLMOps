<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import { useRouter } from 'vue-router'
import { getCurrentUser } from '@/services/auth.ts'
import { type User } from '@/models/auth.ts'

const router = useRouter()
const user = ref<User | null>(null)
const loading = ref(false)
const passwordLoading = ref(false)
const emailLoading = ref(false)
const avatarLoading = ref(false)

const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const emailForm = ref({
  email: '',
  verificationCode: ''
})

const avatarForm = ref({
  avatar: null as File | null,
  avatarPreview: ''
})

const loadUser = async () => {
  loading.value = true
  try {
    const response = await getCurrentUser()
    user.value = response.data.user
    if (user.value?.email) {
      emailForm.value.email = user.value.email
    }
  } catch (err) {
    console.error('获取用户信息失败:', err)
  } finally {
    loading.value = false
  }
}

const handlePasswordChange = async () => {
  if (!passwordForm.value.currentPassword || !passwordForm.value.newPassword) {
    Message.error('请填写完整密码信息')
    return
  }
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    Message.error('两次密码输入不一致')
    return
  }
  if (passwordForm.value.newPassword.length < 6) {
    Message.error('新密码长度不能少于6位')
    return
  }

  passwordLoading.value = true
  try {
    // TODO: 调用后端密码修改API
    Message.success('密码修改成功')
    passwordForm.value = { currentPassword: '', newPassword: '', confirmPassword: '' }
  } catch (err) {
    Message.error('密码修改失败')
  } finally {
    passwordLoading.value = false
  }
}

const handleEmailBind = async () => {
  if (!emailForm.value.email) {
    Message.error('请输入邮箱地址')
    return
  }
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(emailForm.value.email)) {
    Message.error('邮箱格式不正确')
    return
  }

  emailLoading.value = true
  try {
    // TODO: 调用后端邮箱绑定API
    if (user.value) {
      user.value.email = emailForm.value.email
    }
    Message.success('邮箱绑定成功')
  } catch (err) {
    Message.error('邮箱绑定失败')
  } finally {
    emailLoading.value = false
  }
}

const handleAvatarChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    const file = target.files[0]
    if (file.size > 5 * 1024 * 1024) {
      Message.error('头像文件大小不能超过5MB')
      return
    }
    avatarForm.value.avatar = file
    const reader = new FileReader()
    reader.onload = (e) => {
      avatarForm.value.avatarPreview = e.target?.result as string
    }
    reader.readAsDataURL(file)
  }
}

const handleAvatarUpload = async () => {
  if (!avatarForm.value.avatar) {
    Message.error('请选择头像文件')
    return
  }

  avatarLoading.value = true
  try {
    // TODO: 调用后端头像上传API
    Message.success('头像更新成功')
    avatarForm.value = { avatar: null, avatarPreview: '' }
  } catch (err) {
    Message.error('头像更新失败')
  } finally {
    avatarLoading.value = false
  }
}

const goBack = () => {
  router.back()
}

onMounted(() => {
  loadUser()
})
</script>

<template>
  <div class="settings-wrapper">
    <div class="settings-top-bar">
      <a-button @click="goBack" class="back-btn">
        <template #icon><icon-left /></template>
        返回
      </a-button>
    </div>
    <div class="settings-container">
      <div class="settings-header">
        <h1 class="settings-title">账户设置</h1>
        <p class="settings-subtitle">管理你的个人信息和安全设置</p>
      </div>

      <a-spin :loading="loading" class="w-full">
        <div class="settings-content">
        <!-- 账户信息概览 -->
        <div class="settings-card profile-card">
          <div class="profile-header">
            <a-avatar :size="72" :style="{ backgroundColor: '#2563eb', fontSize: '28px' }">
              {{ user?.username?.slice(0, 1).toUpperCase() || 'U' }}
            </a-avatar>
            <div class="profile-info">
              <h2 class="profile-name">{{ user?.username || '用户' }}</h2>
              <div class="profile-details">
                <div class="profile-detail-item">
                  <icon-email />
                  <span>{{ user?.email || '未绑定邮箱' }}</span>
                </div>
                <div class="profile-detail-item">
                  <icon-clock-circle />
                  <span>注册于 {{ user?.created_at ? new Date(user.created_at).toLocaleDateString() : '-' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 头像设置 -->
        <div class="settings-card">
          <div class="card-header">
            <icon-user class="card-icon" />
            <div>
              <h3 class="card-title">头像设置</h3>
              <p class="card-desc">上传你的个人头像</p>
            </div>
          </div>
          <div class="card-body">
            <div class="avatar-section">
              <div class="avatar-preview">
                <img v-if="avatarForm.avatarPreview" :src="avatarForm.avatarPreview" alt="头像预览" />
                <a-avatar v-else :size="80" :style="{ backgroundColor: '#2563eb' }">
                  {{ user?.username?.slice(0, 1).toUpperCase() || 'U' }}
                </a-avatar>
              </div>
              <div class="avatar-actions">
                <input type="file" accept="image/*" @change="handleAvatarChange" class="hidden-input" id="avatarInput" />
                <label for="avatarInput" class="upload-label">
                  选择图片
                </label>
                <p class="upload-hint">支持 JPG、PNG 格式，最大 5MB</p>
                <a-button type="primary" :loading="avatarLoading" @click="handleAvatarUpload" :disabled="!avatarForm.avatar">
                  保存头像
                </a-button>
              </div>
            </div>
          </div>
        </div>

        <!-- 密码设置 -->
        <div class="settings-card">
          <div class="card-header">
            <icon-lock class="card-icon" />
            <div>
              <h3 class="card-title">修改密码</h3>
              <p class="card-desc">定期修改密码可以提高账户安全性</p>
            </div>
          </div>
          <div class="card-body">
            <a-form layout="vertical" @submit="handlePasswordChange">
              <a-form-item label="当前密码">
                <a-input-password v-model="passwordForm.currentPassword" placeholder="请输入当前密码" />
              </a-form-item>
              <a-form-item label="新密码">
                <a-input-password v-model="passwordForm.newPassword" placeholder="请输入新密码（至少6位）" />
              </a-form-item>
              <a-form-item label="确认新密码">
                <a-input-password v-model="passwordForm.confirmPassword" placeholder="请再次输入新密码" />
              </a-form-item>
              <a-button type="primary" :loading="passwordLoading" @click="handlePasswordChange">
                修改密码
              </a-button>
            </a-form>
          </div>
        </div>

        <!-- 邮箱设置 -->
        <div class="settings-card">
          <div class="card-header">
            <icon-email class="card-icon" />
            <div>
              <h3 class="card-title">邮箱绑定</h3>
              <p class="card-desc">绑定邮箱用于接收通知和找回密码</p>
            </div>
          </div>
          <div class="card-body">
            <a-form layout="vertical" @submit="handleEmailBind">
              <a-form-item label="邮箱地址">
                <a-input v-model="emailForm.email" placeholder="请输入邮箱地址" />
              </a-form-item>
              <a-form-item label="验证码" v-if="emailForm.email">
                <div class="verification-row">
                  <a-input v-model="emailForm.verificationCode" placeholder="请输入验证码" />
                  <a-button type="outline" class="send-code-btn">
                    发送验证码
                  </a-button>
                </div>
              </a-form-item>
              <a-button type="primary" :loading="emailLoading" @click="handleEmailBind">
                绑定邮箱
              </a-button>
            </a-form>
          </div>
        </div>
        </div>
      </a-spin>
    </div>
  </div>
</template>

<style scoped>
.settings-wrapper {
  height: 100vh;
  overflow-y: auto;
  background: #f8fafc;
}

.settings-wrapper::-webkit-scrollbar {
  width: 0;
  display: none;
}

.settings-wrapper {
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.settings-top-bar {
  padding: 16px 24px 0;
}

.back-btn {
  margin-bottom: 0;
}

.settings-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 16px 24px 32px;
  box-sizing: border-box;
}

.settings-header {
  margin-bottom: 32px;
}

.settings-title {
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 8px 0;
}

.settings-subtitle {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding-bottom: 32px;
}

.settings-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.profile-card .profile-header {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 24px;
}

.profile-info {
  flex: 1;
}

.profile-name {
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 12px 0;
}

.profile-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.profile-detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #64748b;
}

.profile-detail-item svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.card-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 24px 24px 16px;
  border-bottom: 1px solid #f1f5f9;
}

.card-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #eff6ff;
  color: #2563eb;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 20px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 4px 0;
}

.card-desc {
  font-size: 13px;
  color: #64748b;
  margin: 0;
}

.card-body {
  padding: 24px;
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: 32px;
}

.avatar-preview {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  overflow: hidden;
  border: 3px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8fafc;
}

.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hidden-input {
  display: none;
}

.upload-label {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 36px;
  padding: 0 16px;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  background: #fff;
  color: #374151;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-label:hover {
  border-color: #2563eb;
  color: #2563eb;
}

.upload-hint {
  font-size: 12px;
  color: #9ca3af;
  margin: 0;
}

.verification-row {
  display: flex;
  gap: 12px;
}

.send-code-btn {
  flex-shrink: 0;
  white-space: nowrap;
}

@media (max-width: 640px) {
  .settings-container {
    padding: 16px;
  }

  .profile-card .profile-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .avatar-section {
    flex-direction: column;
    align-items: flex-start;
  }

  .verification-row {
    flex-direction: column;
  }
}
</style>
