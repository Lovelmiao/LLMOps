<script setup lang="ts">
import { computed, ref } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'
import { Message } from '@arco-design/web-vue'

const props = defineProps<{
  content: string
}>()

const copiedIndex = ref<number>(-1)
let codeBlockIndex = 0

const renderedHtml = computed(() => {
  codeBlockIndex = 0
  marked.setOptions({
    breaks: true,
    gfm: true,
    highlight: function (code: string, lang: string) {
      if (lang && hljs.getLanguage(lang)) {
        try {
          return hljs.highlight(code, { language: lang }).value
        } catch {
          // ignore
        }
      }
      return hljs.highlightAuto(code).value
    },
  } as any)

  const renderer = new marked.Renderer()

  renderer.code = function ({ text, lang }: { text: string; lang?: string }) {
    const currentIndex = codeBlockIndex++
    const language = lang || 'plaintext'
    const displayLang = language.charAt(0).toUpperCase() + language.slice(1)
    let highlighted: string
    try {
      if (hljs.getLanguage(language)) {
        highlighted = hljs.highlight(text, { language }).value
      } else {
        highlighted = hljs.highlightAuto(text).value
      }
    } catch {
      highlighted = text
        .replace(/&/g, '&')
        .replace(/</g, '<')
        .replace(/>/g, '>')
    }

    return `<div class="code-block-wrapper">
      <div class="code-block-header">
        <span class="code-language">${displayLang}</span>
        <button class="code-copy-btn" data-code-index="${currentIndex}" onclick="window.__copyCode(${currentIndex})">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
          <span data-code-index="${currentIndex}">复制</span>
        </button>
      </div>
      <pre class="code-block-pre"><code class="hljs language-${language}">${highlighted}</code></pre>
    </div>`
  }

  marked.setOptions({ renderer } as any)

  return marked(props.content || '') as string
})

const codeSnippets = computed(() => {
  const snippets: string[] = []
  const regex = /```[\w]*\n([\s\S]*?)```/g
  let match
  while ((match = regex.exec(props.content || '')) !== null) {
    snippets.push(match[1].trim())
  }
  return snippets
})

const copyCode = (index: number) => {
  const code = codeSnippets.value[index]
  if (code) {
    navigator.clipboard.writeText(code).then(() => {
      copiedIndex.value = index
      Message.success('代码已复制到剪贴板')
      setTimeout(() => {
        copiedIndex.value = -1
      }, 2000)
    }).catch(() => {
      Message.error('复制失败')
    })
  }
}

if (typeof window !== 'undefined') {
  (window as any).__copyCode = (index: number) => {
    const code = codeSnippets.value[index]
    if (code) {
      navigator.clipboard.writeText(code).then(() => {
        Message.success('代码已复制到剪贴板')
      }).catch(() => {
        Message.error('复制失败')
      })
    }
  }
}
</script>

<template>
  <div class="markdown-body" v-html="renderedHtml" />
</template>

<style scoped>
.markdown-body {
  font-size: 14px;
  line-height: 1.75;
  color: #1e293b;
  word-break: break-word;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  margin-top: 16px;
  margin-bottom: 8px;
  font-weight: 600;
  color: #0f172a;
}

.markdown-body :deep(h1) {
  font-size: 1.5em;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 8px;
}

.markdown-body :deep(h2) {
  font-size: 1.3em;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 6px;
}

.markdown-body :deep(h3) {
  font-size: 1.1em;
}

.markdown-body :deep(p) {
  margin: 8px 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 24px;
  margin: 8px 0;
}

.markdown-body :deep(li) {
  margin: 4px 0;
}

.markdown-body :deep(blockquote) {
  margin: 8px 0;
  padding: 8px 16px;
  border-left: 4px solid #2563eb;
  background: #f1f5f9;
  border-radius: 0 8px 8px 0;
  color: #475569;
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid #e2e8f0;
  padding: 8px 12px;
  text-align: left;
}

.markdown-body :deep(th) {
  background: #f1f5f9;
  font-weight: 600;
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid #e2e8f0;
  margin: 16px 0;
}

.markdown-body :deep(strong) {
  font-weight: 600;
  color: #0f172a;
}

.markdown-body :deep(a) {
  color: #2563eb;
  text-decoration: none;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

.markdown-body :deep(code) {
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
  font-family: 'Fira Code', 'Consolas', 'Monaco', monospace;
  color: #e11d48;
}

.markdown-body :deep(.code-block-wrapper) {
  margin: 12px 0;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #2d3748;
  background: #1a202c;
}

.markdown-body :deep(.code-block-header) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: #2d3748;
  border-bottom: 1px solid #4a5568;
}

.markdown-body :deep(.code-language) {
  font-size: 12px;
  color: #a0aec0;
  font-weight: 500;
  text-transform: capitalize;
}

.markdown-body :deep(.code-copy-btn) {
  display: flex;
  align-items: center;
  gap: 4px;
  background: transparent;
  border: 1px solid #4a5568;
  border-radius: 4px;
  color: #a0aec0;
  cursor: pointer;
  padding: 2px 8px;
  font-size: 12px;
  transition: all 0.2s;
}

.markdown-body :deep(.code-copy-btn:hover) {
  background: #4a5568;
  color: #e2e8f0;
}

.markdown-body :deep(.code-block-pre) {
  margin: 0;
  padding: 16px;
  overflow-x: auto;
  background: #1a202c;
}

.markdown-body :deep(.code-block-pre code) {
  font-family: 'Fira Code', 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #e2e8f0;
  background: transparent;
  padding: 0;
  border-radius: 0;
}

.markdown-body :deep(img) {
  max-width: 100%;
  border-radius: 8px;
}
</style>
