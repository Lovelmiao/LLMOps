import { defineStore } from 'pinia'
import { ref } from 'vue'

const initAccount = {
  name: 'xulaoban',
  email: '892342192@qq.com',
}

type Account = typeof initAccount

export const useAccountStore = defineStore('account', () => {
  const account = ref({ ...initAccount })
  function update(params: Partial<Account>) {
    Object.assign(account.value, params)
  }
  function clear() {
    account.value = { ...initAccount }
  }
  return { account, update, clear }
})
