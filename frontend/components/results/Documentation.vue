<script setup lang="ts">
import type { ResponseMessage } from '~/types/websocket'
import { MESSAGE_TYPES } from '~/types/websocket'
import { createGenerateDocsMessage, generateMessageId } from '~/utils/websocket-helpers'

const webSocketStore = useWebSocketStore()
const { getGenerateDocumentation, setGenerateDocumentation, getCode, getLanguage } = useCookieStore()

const generateDocumentation = ref(getGenerateDocumentation())
const code = getCode()
const language = getLanguage()

const isLoading = ref(false)
const messageSent = ref(false)
const documentation = ref<string>('')

const hasDocumentation = computed(() => documentation.value.trim() !== '')
const hasCode = computed(() => !!code)

const containsCode = computed(() => {
  return documentation.value.includes('```')
    || documentation.value.includes('def ')
    || documentation.value.includes('class ')
    || documentation.value.includes('import ')
    || documentation.value.includes('function')
    || documentation.value.includes('return ')
})

function sendDocsRequest() {
  if (!generateDocumentation.value || !code || !code.value.trim() || messageSent.value) {
    return
  }

  const message = createGenerateDocsMessage(
    generateMessageId(),
    code.value,
    language.value as 'python',
  )

  webSocketStore.sendMessage(message)
  messageSent.value = true
  isLoading.value = true
}

function handleMessage(message: ResponseMessage) {
  if (!generateDocumentation.value) {
    return
  }

  if (message.type === MESSAGE_TYPES.response.ERROR && message.error_message) {
    isLoading.value = false
  }
  else if (message.type === MESSAGE_TYPES.response.RETURN_DOCS && message.docs) {
    documentation.value = message.docs
    isLoading.value = false
  }
}

let unregisterHandler: (() => void) | null = null

watch(generateDocumentation, (newValue) => {
  setGenerateDocumentation(newValue)
  if (newValue) {
    messageSent.value = false
    sendDocsRequest()
  }
})

watch(
  () => webSocketStore.isConnected,
  (isConnected) => {
    if (isConnected) {
      sendDocsRequest()
    }
  },
  { immediate: true },
)

onMounted(() => {
  unregisterHandler = webSocketStore.onMessage(handleMessage)
  if (generateDocumentation.value && hasCode.value) {
    sendDocsRequest()
  }
})

onUnmounted(() => {
  if (unregisterHandler) {
    unregisterHandler()
  }
})
</script>

<template>
  <v-card
    class="documentation-card h-100 pa-6"
    elevation="4"
    :class="{'disabled-card': !generateDocumentation}"
  >
    <!-- Header with checkbox -->
    <div class="d-flex align-center justify-space-between mb-4">
      <div class="flex-grow-1 text-center">
        <v-icon
          size="48"
          color="secondary"
          class="mb-3"
          :class="{'disabled-icon': !generateDocumentation}"
        >
          mdi-book-open-variant
        </v-icon>

        <h2 class="text-h4 mb-2">
          Documentation
        </h2>

        <p class="text-body-1 text-medium-emphasis">
          AI-generated documentation for your function
        </p>
      </div>

      <div class="checkbox-container">
        <v-checkbox
          v-model="generateDocumentation"
          color="secondary"
          hide-details
          density="compact"
        >
          <template #label>
            <span class="text-body-2">Enable</span>
          </template>
        </v-checkbox>
      </div>
    </div>

    <!-- Disabled state -->
    <div
      v-if="!generateDocumentation"
      class="disabled-content text-center"
    >
      <v-icon
        size="64"
        color="grey-lighten-1"
        class="mb-3"
      >
        mdi-book-off
      </v-icon>

      <h3 class="text-h6 text-medium-emphasis mb-2">
        Documentation Generation Disabled
      </h3>

      <p class="text-body-2 text-medium-emphasis">
        Enable documentation generation to see AI-generated docs for your function.
      </p>
    </div>

    <!-- Enabled state -->
    <div v-else>
      <!-- Waiting for code -->
      <v-alert
        v-if="!hasCode"
        type="info"
        variant="tonal"
        class="mb-4"
      >
        Waiting for code...
      </v-alert>

      <!-- Loading state -->
      <div
        v-else-if="isLoading"
        class="text-center"
      >
        <v-progress-circular
          indeterminate
          color="secondary"
          size="32"
          class="mb-3"
        />

        <p class="text-body-2 text-medium-emphasis">
          Generating documentation...
        </p>
      </div>

      <!-- Documentation content -->
      <div
        v-else-if="hasDocumentation"
        class="documentation-content"
      >
        <!-- Use CodeHighlight if content contains code -->
        <CodeHighlight
          v-if="containsCode"
          :code="documentation"
          title="Documentation"
          copyable
        />

        <!-- Otherwise use regular text display -->
        <div
          v-else
          class="documentation-text"
        >
          {{ documentation }}
        </div>
      </div>

      <!-- No documentation received yet -->
      <v-alert
        v-else
        type="info"
        variant="tonal"
        class="mb-4"
      >
        Documentation will be displayed here.
      </v-alert>
    </div>
  </v-card>
</template>

<style scoped>
.documentation-card {
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: linear-gradient(135deg, rgb(var(--v-theme-secondary), 0.05) 0%, transparent 100%);
}

.documentation-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1) !important;
}

.documentation-content {
  max-height: 400px;
  overflow-y: auto;
}

.documentation-text {
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
  padding: 1rem;
  background: rgb(var(--v-theme-grey-darken-4));
  border-radius: 8px;
  color: #e8eaed;
  font-family: 'Fira Code', 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', 'Source Code Pro', monospace;
  font-size: 0.875rem;
}

.disabled-card {
  opacity: 0.7;
  filter: grayscale(0.3);
}

.disabled-icon {
  opacity: 0.5;
}

.disabled-content {
  padding: 2rem 0;
}

.checkbox-container {
  position: absolute;
  top: 1rem;
  right: 1rem;
  z-index: 1;
}

@media (max-width: 960px) {
  .documentation-card {
    padding: 1rem;
  }

  .documentation-content {
    max-height: 300px;
  }
}
</style>
