<script setup lang="ts">
import { useCounterStore } from '@/stores/counter.ts'

const counterStore = useCounterStore()
</script>

<template>
  <p>Ai列表</p>
  <p>数值是:{{ counterStore.count }}</p>
  <router-link to="/home">返回home界面</router-link>
</template>

<style scoped></style>
