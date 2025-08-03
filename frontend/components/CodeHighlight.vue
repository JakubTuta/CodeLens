<script setup lang="ts">
import Prism from 'prismjs'
import 'prismjs/themes/prism-tomorrow.css'
import 'prismjs/components/prism-python'

interface Props {
  code: string
  maxHeight?: string
  title?: string
  copyable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  maxHeight: 'none',
  title: '',
})

const { copy, copied } = useClipboard()
const codeRef = ref<HTMLElement>()

async function copyCode() {
  if (props.copyable) {
    await copy(props.code)
  }
}

onMounted(() => {
  if (codeRef.value) {
    Prism.highlightElement(codeRef.value)
  }
})

watch(() => props.code, () => {
  nextTick(() => {
    if (codeRef.value) {
      Prism.highlightElement(codeRef.value)
    }
  })
})
</script>

<template>
  <v-card
    class="code-highlight-card"
    elevation="2"
  >
    <!-- Header with title and copy button -->
    <div
      v-if="title || copyable"
      class="code-header d-flex justify-space-between align-center pa-3"
    >
      <div
        v-if="title"
        class="code-title font-weight-medium text-body-1"
      >
        {{ title }}
      </div>

      <v-btn
        v-if="copyable"
        variant="text"
        size="small"
        :color="copied
          ? 'success'
          : 'primary'"
        @click="copyCode"
      >
        <v-icon start>
          {{ copied
            ? 'mdi-check'
            : 'mdi-content-copy' }}
        </v-icon>
        {{ copied
          ? 'Copied!'
          : 'Copy' }}
      </v-btn>
    </div>

    <v-divider v-if="title || copyable" />

    <!-- Code content -->
    <div
      class="code-container"
      :style="{
        'max-height': maxHeight !== 'none'
          ? maxHeight
          : undefined,
      }"
    >
      <pre
        ref="codeRef"
        class="code-content language-python"
      >{{ code }}</pre>
    </div>
  </v-card>
</template>

<style scoped>
.code-highlight-card {
  border: 1px solid rgba(var(--v-theme-outline), 0.2);
  border-radius: 8px;
  overflow: hidden;
  background: rgb(var(--v-theme-surface));
}

.code-header {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-bottom: 1px solid rgba(var(--v-theme-outline), 0.1);
}

.code-title {
  color: rgba(var(--v-theme-on-surface), 0.87);
}

.code-container {
  position: relative;
  overflow: auto;
  background: rgb(var(--v-theme-grey-darken-4));
}

.code-content {
  font-family: 'Fira Code', 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', 'Source Code Pro', monospace;
  font-size: 0.875rem;
  line-height: 1.6;
  margin: 0;
  padding: 16px;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-weight: 400;
  letter-spacing: 0.025em;
  background: transparent;
  border: none;
  outline: none;
  color: #e8eaed;
}

@media (max-width: 960px) {
  .code-content {
    font-size: 0.8rem;
    padding: 12px;
  }
}

.code-highlight-card {
  transition: all 0.3s ease;
}

.code-highlight-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
}
</style>
