<script setup lang="ts">
import { ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import { useRouter } from 'vue-router'
import { login, register } from '@/services/auth.ts'
import { setLogin } from '@/utils/auth.ts'

const router = useRouter()
const username = ref('')
const password = ref('')
const mode = ref<'login' | 'register'>('login')
const loading = ref(false)

const submit = async () => {
  if (!username.value.trim() || !password.value) {
    Message.error('请输入用户名和密码')
    return
  }

  loading.value = true
  try {
    if (mode.value === 'login') {
      await login(username.value.trim(), password.value)
      Message.success('登录成功')
    } else {
      await register(username.value.trim(), password.value)
      Message.success('注册成功')
    }
    setLogin()
    router.push('/home')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="min-h-screen flex items-center justify-center px-6 py-10 login-shell">
    <section class="w-full max-w-[430px] bg-white/95 border border-white/70 rounded-lg shadow-xl p-8 backdrop-blur login-card">
      <div class="mb-7">
        <div class="inline-flex items-center gap-2 text-sm text-blue-700 bg-blue-50 border border-blue-100 rounded px-2.5 py-1 mb-4">
          <icon-book />
          Paper Research RAG
        </div>
        <h1 class="text-2xl font-semibold text-slate-950">
          {{ mode === 'login' ? '登录工作台' : '创建账号' }}
        </h1>
        <p class="text-sm text-slate-500 mt-2">进入你的论文检索、阅读和问答空间。</p>
      </div>

      <a-form :model="{ username, password }" layout="vertical" @submit.prevent="submit">
        <a-form-item label="用户名">
          <a-input v-model="username" placeholder="请输入用户名" @keyup.enter="submit" />
        </a-form-item>
        <a-form-item label="密码">
          <a-input-password v-model="password" placeholder="请输入密码" @keyup.enter="submit" />
        </a-form-item>
        <a-button type="primary" long :loading="loading" @click="submit">
          {{ mode === 'login' ? '登录' : '注册并登录' }}
        </a-button>
      </a-form>

      <div class="mt-5 text-center text-sm text-slate-500">
        <button
          class="text-blue-600 hover:text-blue-700"
          type="button"
          @click="mode = mode === 'login' ? 'register' : 'login'"
        >
          {{ mode === 'login' ? '没有账号？立即注册' : '已有账号？返回登录' }}
        </button>
      </div>
    </section>
  </main>
</template>

<style scoped>
.login-shell {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  width: 100%;
  padding: 40px 24px;
  background:
    linear-gradient(120deg, rgba(37, 99, 235, 0.16), rgba(20, 184, 166, 0.12)),
    radial-gradient(circle at 18% 20%, rgba(14, 165, 233, 0.22), transparent 32%),
    linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
}

.login-card {
  width: min(430px, 100%);
  padding: 32px;
}
</style>
