<script setup lang="ts">
import type { ResponseMessage } from '~/types/websocket'
import { useStepperNavigation } from '~/composables/useStepperNavigation'
import { MESSAGE_TYPES } from '~/types/websocket'
import { createTestAiMessage, generateMessageId } from '~/utils/websocket-helpers'

const apiKey = ref('')
let saveTimeout: NodeJS.Timeout | null = null

const { goNext, goPrevious, canGoNext, canGoPrevious, nextStepName, previousStepName } = useStepperNavigation()
const webSocketStore = useWebSocketStore()
const { getApiKey, setApiKey, setAiModel } = useCookieStore()

const showAlert = ref(false)
const alertType = ref<'success' | 'error' | 'info'>('success')
const alertMessage = ref('')
const detectedModel = ref<string | null>(null)
const isVerifying = ref(false)

let unregisterMessage: (() => void) | null = null

onMounted(() => {
  const savedApiKey = getApiKey()
  if (savedApiKey.value) {
    apiKey.value = savedApiKey.value
  }

  unregisterMessage = webSocketStore.onMessage((data: ResponseMessage) => {
    if (data.type === MESSAGE_TYPES.response.AI_TEST_RESULT) {
      isVerifying.value = false
      if (data.detected_model) {
        detectedModel.value = data.detected_model
        setAiModel(data.detected_model)
        alertType.value = 'success'
        alertMessage.value = `AI model detected: ${data.detected_model}`
      }
      else {
        detectedModel.value = null
        alertType.value = 'error'
        alertMessage.value = data.error_message || 'Failed to detect AI model'
      }
      showAlert.value = true
    }
    else if (data.type === MESSAGE_TYPES.response.ERROR) {
      isVerifying.value = false
      detectedModel.value = null
      alertType.value = 'error'
      alertMessage.value = data.error_message || 'An error occurred'
      showAlert.value = true
    }
  })
})

onUnmounted(() => {
  if (unregisterMessage) {
    unregisterMessage()
  }
})

function testApiKey(apiKeyValue: string) {
  if (apiKeyValue && webSocketStore.isConnected) {
    isVerifying.value = true
    showAlert.value = true
    alertType.value = 'info'
    alertMessage.value = 'Verifying API key...'
    const message = createTestAiMessage(generateMessageId())
    webSocketStore.sendMessage(message)
  }
}

watch(apiKey, (newValue) => {
  if (saveTimeout) {
    clearTimeout(saveTimeout)
  }

  if (newValue.trim()) {
    isVerifying.value = true
    showAlert.value = true
    alertType.value = 'info'
    alertMessage.value = 'Verifying API key...'
  }
  else {
    showAlert.value = false
    detectedModel.value = null
    isVerifying.value = false
  }

  setApiKey(newValue)

  saveTimeout = setTimeout(() => {
    if (newValue.trim()) {
      testApiKey(newValue)
    }
  }, 1000)
})
</script>

<template>
  <v-container>
    <v-card
      class="mx-auto"
      max-width="800"
    >
      <v-card-title class="text-center">
        Enter AI API Key
      </v-card-title>

      <v-card-text class="text-center">
        <v-text-field
          v-model="apiKey"
          label="API Key"
          placeholder="Enter your AI API key"
          class="mx-auto mt-4 max-w-600px"
          clearable
          @click:clear="apiKey = ''"
        />

        <ValidationAlert
          :show="showAlert"
          :type="alertType"
          :message="alertMessage"
          :is-loading="isVerifying"
          @close="showAlert = false"
        />
      </v-card-text>
    </v-card>

    <!-- Information Section -->
    <v-container class="info-section mt-10 py-8">
      <v-row justify="center">
        <v-col
          cols="12"
          md="10"
        >
          <!-- Optional Notice -->
          <v-alert
            type="info"
            class="mb-6"
            icon="mdi-information-outline"
            variant="tonal"
          >
            <v-alert-title class="text-h6 mb-2">
              API Key is Optional
            </v-alert-title>
            You can use this application without an API key for basic functionality,
            or provide one to unlock advanced AI-powered features.
          </v-alert>

          <!-- Feature Comparison -->
          <v-row class="mb-6">
            <v-col
              cols="12"
              md="6"
            >
              <v-card
                class="feature-card h-100 pa-6"
                elevation="2"
              >
                <div class="text-center">
                  <v-icon
                    size="48"
                    color="primary"
                    class="mb-4"
                  >
                    mdi-test-tube
                  </v-icon>

                  <h3 class="text-h5 mb-3">
                    Without API Key
                  </h3>

                  <v-list
                    class="feature-list"
                    lines="one"
                  >
                    <v-list-item>
                      <template #prepend>
                        <v-icon color="success">
                          mdi-check-circle
                        </v-icon>
                      </template>

                      <v-list-item-title>Automatic test generation</v-list-item-title>
                    </v-list-item>

                    <v-list-item>
                      <template #prepend>
                        <v-icon color="success">
                          mdi-check-circle
                        </v-icon>
                      </template>

                      <v-list-item-title>Test execution and results</v-list-item-title>
                    </v-list-item>

                    <v-list-item>
                      <template #prepend>
                        <v-icon color="success">
                          mdi-check-circle
                        </v-icon>
                      </template>

                      <v-list-item-title>Basic code validation</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </div>
              </v-card>
            </v-col>

            <v-col
              cols="12"
              md="6"
            >
              <v-card
                class="feature-card h-100 pa-6"
                color="primary-lighten-5"
                elevation="4"
              >
                <div class="text-center">
                  <v-icon
                    size="48"
                    color="primary"
                    class="mb-4"
                  >
                    mdi-auto-fix
                  </v-icon>

                  <h3 class="text-h5 mb-3">
                    With Valid API Key
                  </h3>

                  <v-list
                    class="feature-list"
                    lines="one"
                  >
                    <v-list-item>
                      <template #prepend>
                        <v-icon color="success">
                          mdi-check-circle
                        </v-icon>
                      </template>

                      <v-list-item-title>Everything from basic plan</v-list-item-title>
                    </v-list-item>

                    <v-list-item>
                      <template #prepend>
                        <v-icon color="yellow">
                          mdi-star
                        </v-icon>
                      </template>

                      <v-list-item-title>AI-generated documentation</v-list-item-title>
                    </v-list-item>

                    <v-list-item>
                      <template #prepend>
                        <v-icon color="yellow">
                          mdi-star
                        </v-icon>
                      </template>

                      <v-list-item-title>Code optimization tips</v-list-item-title>
                    </v-list-item>

                    <v-list-item>
                      <template #prepend>
                        <v-icon color="yellow">
                          mdi-star
                        </v-icon>
                      </template>

                      <v-list-item-title>Enhanced test suggestions</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </div>
              </v-card>
            </v-col>
          </v-row>

          <!-- Supported Models -->
          <v-card
            class="models-card pa-6"
            elevation="3"
          >
            <div class="mb-4 text-center">
              <v-icon
                size="40"
                color="secondary"
                class="mb-3"
              >
                mdi-brain
              </v-icon>

              <h3 class="text-h5 mb-2">
                Supported AI Models
              </h3>

              <p class="text-body-1 text-medium-emphasis mb-4">
                We support popular AI providers for the best experience
              </p>
            </div>

            <v-row class="model-list">
              <v-col
                cols="12"
                sm="6"
              >
                <div class="d-flex align-center model-item pa-3">
                  <v-avatar
                    size="32"
                    color="success"
                    class="mr-3"
                  >
                    <v-icon color="white">
                      mdi-google
                    </v-icon>
                  </v-avatar>

                  <div>
                    <div class="font-weight-medium">
                      Google Gemini
                    </div>

                    <div class="text-caption text-medium-emphasis">
                      Advanced reasoning and code analysis
                    </div>
                  </div>
                </div>
              </v-col>

              <v-col
                cols="12"
                sm="6"
              >
                <div class="model-item d-flex align-center pa-3">
                  <v-avatar
                    size="32"
                    color="info"
                    class="mr-3"
                  >
                    <v-icon color="white">
                      mdi-robot
                    </v-icon>
                  </v-avatar>

                  <div>
                    <div class="font-weight-medium">
                      Claude Sonnet
                    </div>

                    <div class="text-caption text-medium-emphasis">
                      Excellent for documentation and improvements
                    </div>
                  </div>
                </div>
              </v-col>
            </v-row>
          </v-card>
        </v-col>
      </v-row>
    </v-container>

    <v-divider class="my-6" />

    <v-row justify="space-between">
      <v-col cols="auto">
        <v-btn
          v-if="canGoPrevious"
          variant="outlined"
          @click="goPrevious"
        >
          <v-icon start>
            mdi-arrow-left
          </v-icon>
          {{ previousStepName }}
        </v-btn>
      </v-col>

      <v-col cols="auto">
        <v-btn
          v-if="canGoNext"
          color="primary"
          @click="goNext"
        >
          {{ nextStepName }}
          <v-icon end>
            mdi-arrow-right
          </v-icon>
        </v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>

<style scoped>
.info-section {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary), 0.02) 0%, rgb(var(--v-theme-secondary), 0.02) 100%);
}

.feature-card {
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1) !important;
}

.feature-list .v-list-item {
  padding-left: 0;
  margin-bottom: 0.5rem;
}

.models-card {
  position: relative;
  backdrop-filter: blur(10px);
  border: 1px solid rgb(var(--v-theme-secondary), 0.2);
}

.model-item {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.model-item:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

@media (max-width: 960px) {
  .info-section {
    padding-top: 1rem;
    padding-bottom: 1rem;
  }

  .feature-card {
    margin-bottom: 1rem;
  }
}
</style>
