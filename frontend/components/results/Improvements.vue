<script setup lang="ts">
import type { ResponseMessage } from '~/types/websocket'
import { MESSAGE_TYPES } from '~/types/websocket'
import { createGenerateImprovementsMessage, generateMessageId } from '~/utils/websocket-helpers'

const webSocketStore = useWebSocketStore()
const { getGenerateImprovements, setGenerateImprovements, getCode, getLanguage, getApiKey, hasApiKey } = useCookieStore()

const generateImprovements = ref(getGenerateImprovements())
const code = getCode()
const language = getLanguage()
const apiKey = getApiKey()

const isLoading = ref(false)
const messageSent = ref(false)
const improvements = ref<string[]>([])
const showApiKeyError = ref(false)

const hasImprovements = computed(() => improvements.value.length > 0)
const hasCode = computed(() => !!code)
const hasValidApiKey = computed(() => hasApiKey() && apiKey.value.trim() !== '')

function sendImprovementsRequest() {
  if (!generateImprovements.value || !code || !code.value.trim() || messageSent.value) {
    return
  }

  if (!hasValidApiKey.value) {
    showApiKeyError.value = true

    return
  }

  const message = createGenerateImprovementsMessage(
    generateMessageId(),
    code.value,
    language.value as 'python',
  )

  webSocketStore.sendMessage(message)
  messageSent.value = true
  isLoading.value = true
  showApiKeyError.value = false
}

function handleMessage(message: ResponseMessage) {
  if (!generateImprovements.value) {
    return
  }

  if (message.type === MESSAGE_TYPES.response.ERROR && message.error_message) {
    isLoading.value = false
    if (message.error_message === 'AI model or API key is invalid.') {
      showApiKeyError.value = true
    }
  }
  else if (message.type === MESSAGE_TYPES.response.RETURN_IMPROVEMENTS && message.improvements) {
    improvements.value = message.improvements
    isLoading.value = false
    showApiKeyError.value = false
  }
}

let unregisterHandler: (() => void) | null = null

watch(generateImprovements, (newValue) => {
  setGenerateImprovements(newValue)
  if (newValue) {
    messageSent.value = false
    showApiKeyError.value = false
    sendImprovementsRequest()
  }
})

watch(
  () => webSocketStore.isConnected,
  (isConnected) => {
    if (isConnected) {
      sendImprovementsRequest()
    }
  },
  { immediate: true },
)

onMounted(() => {
  unregisterHandler = webSocketStore.onMessage(handleMessage)
  if (generateImprovements.value && hasCode.value) {
    sendImprovementsRequest()
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
    class="improvements-card h-100 pa-6"
    elevation="4"
    :class="{'disabled-card': !generateImprovements}"
  >
    <!-- Header with checkbox -->
    <div class="d-flex align-center justify-space-between mb-4">
      <div class="flex-grow-1 text-center">
        <v-icon
          size="48"
          color="accent"
          class="mb-3"
          :class="{'disabled-icon': !generateImprovements}"
        >
          mdi-brush
        </v-icon>

        <h2 class="text-h4 mb-2">
          Improvements
        </h2>

        <p class="text-body-1 text-medium-emphasis">
          Code optimization tips and suggestions
        </p>
      </div>

      <div class="checkbox-container">
        <v-checkbox
          v-model="generateImprovements"
          color="success"
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
      v-if="!generateImprovements"
      class="disabled-content text-center"
    >
      <v-icon
        size="64"
        color="grey-lighten-1"
        class="mb-3"
      >
        mdi-brush-off
      </v-icon>

      <h3 class="text-h6 text-medium-emphasis mb-2">
        Improvements Generation Disabled
      </h3>

      <p class="text-body-2 text-medium-emphasis">
        Enable improvements generation to see optimization tips and suggestions.
      </p>
    </div>

    <!-- Enabled state -->
    <div v-else>
      <!-- API Key Error -->
      <v-alert
        v-if="showApiKeyError"
        type="warning"
        variant="tonal"
        class="mb-4"
        closable
        @click:close="showApiKeyError = false"
      >
        <div class="d-flex flex-column">
          <div class="text-h6 mb-2">
            API Key Required
          </div>

          <div class="text-body-2 mb-3">
            Please enter a valid API key to generate improvements. Go to the API Key page to set up your credentials.
          </div>

          <div>
            <v-btn
              color="warning"
              variant="outlined"
              size="small"
              to="/enter-api-key"
            >
              Enter API Key
            </v-btn>
          </div>
        </div>
      </v-alert>

      <!-- Waiting for code -->
      <v-alert
        v-else-if="!hasCode"
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
          color="accent"
          size="32"
          class="mb-3"
        />

        <p class="text-body-2 text-medium-emphasis">
          Analyzing code for improvements...
        </p>
      </div>

      <!-- Improvements content -->
      <div
        v-else-if="hasImprovements"
        class="improvements-content"
      >
        <v-list class="improvements-list">
          <v-list-item
            v-for="(improvement, index) in improvements"
            :key="index"
            class="improvement-item mb-2 pa-3"
            lines="three"
          >
            <template #prepend>
              <v-icon
                color="accent"
                size="20"
              >
                mdi-lightbulb-on
              </v-icon>
            </template>

            <v-list-item-title class="improvement-text">
              <div class="improvement-content">
                {{ improvement }}
              </div>
            </v-list-item-title>
          </v-list-item>
        </v-list>
      </div>

      <!-- No improvements received yet -->
      <v-alert
        v-else
        type="info"
        variant="tonal"
        class="mb-4"
      >
        Improvement suggestions will be displayed here.
      </v-alert>
    </div>
  </v-card>
</template>

<style scoped>
.improvements-card {
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: linear-gradient(135deg, rgb(var(--v-theme-accent), 0.05) 0%, transparent 100%);
}

.improvements-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1) !important;
}

.improvements-content {
  overflow-y: auto;
}

.improvements-list {
  background: transparent;
}

.improvement-item {
  border-radius: 8px;
  background: rgba(var(--v-theme-surface), 0.5);
  border: 1px solid rgba(var(--v-theme-accent), 0.2);
  transition: all 0.2s ease;
  min-height: auto;
  height: auto;
  align-items: flex-start;
}

.improvement-item:hover {
  background: rgba(var(--v-theme-accent), 0.1);
  border-color: rgba(var(--v-theme-accent), 0.4);
}

.improvement-text {
  line-height: 1.5;
  word-wrap: break-word;
  white-space: normal;
  overflow: visible;
}

.improvement-content {
  white-space: pre-wrap;
  word-break: break-word;
  hyphens: auto;
  line-height: 1.6;
  padding: 4px 0;
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
  .improvements-card {
    padding: 1rem;
  }

  .improvements-content {
    max-height: 300px;
  }
}
</style>
