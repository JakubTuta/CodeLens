<script setup lang="ts">
import type { ResponseMessage } from '~/types/websocket'
import { useStepperNavigation } from '~/composables/useStepperNavigation'
import { MESSAGE_TYPES } from '~/types/websocket'
import { createVerifyCodeMessage, generateMessageId } from '~/utils/websocket-helpers'

const code = ref('')
const showAlert = ref(false)
const alertType = ref<'success' | 'error' | 'info'>('success')
const alertMessage = ref('')
const isVerifying = ref(false)
let saveTimeout: NodeJS.Timeout | null = null

const { goNext, goPrevious, canGoNext, canGoPrevious, nextStepName, previousStepName } = useStepperNavigation()
const webSocketStore = useWebSocketStore()
const { getCode, setCode, getGenerateTests, getGenerateDocumentation, getGenerateImprovements, setGenerateTests, setGenerateDocumentation, setGenerateImprovements } = useCookieStore()

const generateTests = ref(getGenerateTests())
const generateDocumentation = ref(getGenerateDocumentation())
const generateImprovements = ref(getGenerateImprovements())

let unregisterMessage: (() => void) | null = null

onMounted(() => {
  const savedCode = getCode()
  if (savedCode.value) {
    code.value = savedCode.value
  }

  unregisterMessage = webSocketStore.onMessage((data: ResponseMessage) => {
    if (data.type === MESSAGE_TYPES.response.VERIFY_CODE_RESULT) {
      isVerifying.value = false
      if (data.is_ok) {
        alertType.value = 'success'
        alertMessage.value = 'Code validation successful! Your function is ready for analysis.'
      }
      else {
        alertType.value = 'error'
        alertMessage.value = data.error_message || 'Code validation failed'
      }
      showAlert.value = true
    }
    else if (data.type === MESSAGE_TYPES.response.ERROR) {
      isVerifying.value = false
      alertType.value = 'error'
      alertMessage.value = data.error_message || 'An error occurred during code validation'
      showAlert.value = true
    }
  })
})

onUnmounted(() => {
  if (unregisterMessage) {
    unregisterMessage()
  }
})

function verifyCode(codeValue: string) {
  if (codeValue && webSocketStore.isConnected) {
    isVerifying.value = true
    showAlert.value = true
    alertType.value = 'info'
    alertMessage.value = 'Validating your code...'
    const message = createVerifyCodeMessage(generateMessageId(), codeValue, 'python')
    webSocketStore.sendMessage(message)
  }
}

watch(code, (newValue) => {
  if (saveTimeout) {
    clearTimeout(saveTimeout)
  }

  if (newValue.trim()) {
    isVerifying.value = true
    showAlert.value = true
    alertType.value = 'info'
    alertMessage.value = 'Validating your code...'
  }
  else {
    showAlert.value = false
    isVerifying.value = false
  }

  saveTimeout = setTimeout(() => {
    setCode(newValue)

    if (newValue.trim()) {
      verifyCode(newValue)
    }
  }, 1000)
})

watch(generateTests, (newValue) => {
  setGenerateTests(newValue)
})

watch(generateDocumentation, (newValue) => {
  setGenerateDocumentation(newValue)
})

watch(generateImprovements, (newValue) => {
  setGenerateImprovements(newValue)
})
</script>

<template>
  <v-container>
    <v-card
      class="mx-auto"
      max-width="1000"
    >
      <v-card-title class="text-center">
        Enter Your Code
      </v-card-title>

      <v-card-text>
        <!-- Information Sections -->
        <v-row class="mb-6">
          <v-col
            cols="12"
            md="6"
          >
            <v-card
              class="info-card pa-4"
              color="primary-lighten-5"
              elevation="2"
            >
              <div class="text-center">
                <v-icon
                  size="32"
                  color="primary"
                  class="mb-2"
                >
                  mdi-code-tags
                </v-icon>

                <h3 class="text-h6 mb-2">
                  Supported Languages
                </h3>

                <div class="align-center d-flex justify-center">
                  <v-chip
                    color="primary"
                    variant="flat"
                    class="mr-2"
                  >
                    <v-icon start>
                      mdi-language-python
                    </v-icon>
                    Python
                  </v-chip>

                  <v-chip
                    color="grey"
                    variant="outlined"
                    disabled
                  >
                    More coming soon...
                  </v-chip>
                </div>
              </div>
            </v-card>
          </v-col>

          <v-col
            cols="12"
            md="6"
          >
            <v-card
              class="info-card pa-4"
              color="secondary-lighten-5"
              elevation="2"
            >
              <div class="text-center">
                <v-icon
                  size="32"
                  color="secondary"
                  class="mb-2"
                >
                  mdi-function
                </v-icon>

                <h3 class="text-h6 mb-2">
                  Code Requirements
                </h3>

                <v-list
                  class="requirement-list"
                  lines="one"
                >
                  <v-list-item>
                    <template #prepend>
                      <v-icon color="success">
                        mdi-check-circle
                      </v-icon>
                    </template>

                    <v-list-item-title class="text-body-2">
                      Paste or write only one function
                    </v-list-item-title>
                  </v-list-item>

                  <v-list-item>
                    <template #prepend>
                      <v-icon color="success">
                        mdi-check-circle
                      </v-icon>
                    </template>

                    <v-list-item-title class="text-body-2">
                      Include function definition and body
                    </v-list-item-title>
                  </v-list-item>
                </v-list>
              </div>
            </v-card>
          </v-col>
        </v-row>

        <!-- Code Input -->
        <v-textarea
          v-model="code"
          label="Your Function Code"
          placeholder="def your_function(param1, param2):
    '''Your function description here'''
    # Your implementation here
    return result"
          rows="15"
          variant="outlined"
          class="code-textarea"
          clearable
          counter
          @click:clear="code = ''"
        />

        <!-- Generation Options -->
        <v-card
          class="generation-options mb-4 pa-4"
          color="surface-variant"
          elevation="1"
        >
          <div class="d-flex align-center text-h6 mb-3">
            <v-icon
              color="primary"
              class="mr-2"
            >
              mdi-cog
            </v-icon>
            Generation Options
          </div>

          <v-row>
            <v-col
              cols="12"
              sm="4"
            >
              <v-checkbox
                v-model="generateTests"
                color="primary"
                hide-details
              >
                <template #label>
                  <div class="d-flex align-center">
                    <v-icon
                      size="20"
                      class="mr-2"
                      color="primary"
                    >
                      mdi-test-tube
                    </v-icon>

                    <span class="text-body-1">Generate Tests</span>
                  </div>
                </template>
              </v-checkbox>
            </v-col>

            <v-col
              cols="12"
              sm="4"
            >
              <v-checkbox
                v-model="generateDocumentation"
                color="secondary"
                hide-details
              >
                <template #label>
                  <div class="d-flex align-center">
                    <v-icon
                      size="20"
                      class="mr-2"
                      color="secondary"
                    >
                      mdi-book-open-variant
                    </v-icon>

                    <span class="text-body-1">Generate Documentation</span>
                  </div>
                </template>
              </v-checkbox>
            </v-col>

            <v-col
              cols="12"
              sm="4"
            >
              <v-checkbox
                v-model="generateImprovements"
                color="success"
                hide-details
              >
                <template #label>
                  <div class="d-flex align-center">
                    <v-icon
                      size="20"
                      class="mr-2"
                      color="success"
                    >
                      mdi-lightbulb-on
                    </v-icon>

                    <span class="text-body-1">Generate Improvements</span>
                  </div>
                </template>
              </v-checkbox>
            </v-col>
          </v-row>
        </v-card>

        <!-- Validation Alert -->
        <ValidationAlert
          :show="showAlert"
          :type="alertType"
          :message="alertMessage"
          :is-loading="isVerifying"
          @close="showAlert = false"
        />
      </v-card-text>
    </v-card>

    <!-- Additional Information Section -->
    <v-container class="info-section py-8">
      <v-row justify="center">
        <v-col
          cols="12"
          md="8"
        >
          <v-card
            class="tips-card pa-6"
            color="info-lighten-5"
            elevation="3"
          >
            <div class="mb-4 text-center">
              <v-icon
                size="40"
                color="info"
                class="mb-3"
              >
                mdi-lightbulb-on
              </v-icon>

              <h3 class="text-h5 mb-2">
                Tips for Best Results
              </h3>
            </div>

            <v-row>
              <v-col
                cols="12"
                sm="6"
              >
                <div class="d-flex tip-item pa-2 align-start">
                  <v-icon
                    color="success"
                    class="mr-3 mt-1"
                  >
                    mdi-check-bold
                  </v-icon>

                  <div>
                    <div class="font-weight-medium mb-1">
                      Use meaningful names
                    </div>

                    <div class="text-body-2 text-medium-emphasis">
                      Clear variable and parameter names help generate better tests
                    </div>
                  </div>
                </div>
              </v-col>

              <v-col
                cols="12"
                sm="6"
              >
                <div class="d-flex tip-item pa-2 align-start">
                  <v-icon
                    color="warning"
                    class="mr-3 mt-1"
                  >
                    mdi-alert
                  </v-icon>

                  <div>
                    <div class="font-weight-medium mb-1">
                      One function only
                    </div>

                    <div class="text-body-2 text-medium-emphasis">
                      Focus on a single function for comprehensive analysis
                    </div>
                  </div>
                </div>
              </v-col>

              <v-col
                cols="12"
                sm="6"
              >
                <div class="d-flex tip-item pa-2 align-start">
                  <v-icon
                    color="info"
                    class="mr-3 mt-1"
                  >
                    mdi-information
                  </v-icon>

                  <div>
                    <div class="font-weight-medium mb-1">
                      Include imports
                    </div>

                    <div class="text-body-2 text-medium-emphasis">
                      Add necessary imports if your function depends on external libraries
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

.info-card {
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.info-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
}

.requirement-list .v-list-item {
  padding-left: 0;
  margin-bottom: 0.25rem;
  min-height: auto;
}

.code-textarea {
  font-family: 'Fira Code', 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', 'Source Code Pro', monospace;
}

.tips-card {
  position: relative;
  backdrop-filter: blur(10px);
  border: 1px solid rgb(var(--v-theme-info), 0.2);
}

.tip-item {
  transition: all 0.2s ease;
  border-radius: 8px;
}

.tip-item:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

.generation-options {
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.generation-options:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
}

@media (max-width: 960px) {
  .info-section {
    padding-top: 1rem;
    padding-bottom: 1rem;
  }

  .info-card {
    margin-bottom: 1rem;
  }
}
</style>
