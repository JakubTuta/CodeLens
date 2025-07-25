<script setup lang="ts">
import type { ResponseMessage, Test } from '~/types/websocket'
import { MESSAGE_TYPES } from '~/types/websocket'
import { createGenerateTestsMessage, generateMessageId } from '~/utils/websocket-helpers'
import TestGroup from './TestGroup.vue'

const webSocketStore = useWebSocketStore()
const { getGenerateTests, setGenerateTests, getCode, getLanguage } = useCookieStore()

const generateTests = ref(getGenerateTests())
const code = getCode()
const language = getLanguage()

const isLoading = ref(false)
const messageSent = ref(false)
const unitTests = ref<Test[]>([])
const memoryTests = ref<Test[]>([])
const performanceTests = ref<Test[]>([])

const hasAnyTests = computed(() => (
  unitTests.value.length > 0
  || memoryTests.value.length > 0
  || performanceTests.value.length > 0
))
const hasCode = computed(() => !!code)

function sendTestsRequest() {
  if (!generateTests.value || !code.value.trim() || messageSent.value) {
    return
  }

  const message = createGenerateTestsMessage(
    generateMessageId(),
    code.value,
    language.value as 'python',
  )

  webSocketStore.sendMessage(message)
  messageSent.value = true
  isLoading.value = true
}

function handleMessage(message: ResponseMessage) {
  if (!generateTests.value) {
    return
  }

  if (message.type === MESSAGE_TYPES.response.ERROR && message.error_message) {
    isLoading.value = false
  }
  else if (message.type === MESSAGE_TYPES.response.RETURN_UNIT_TESTS && message.unit_tests) {
    unitTests.value = message.unit_tests
    isLoading.value = false
  }
  else if (message.type === MESSAGE_TYPES.response.RETURN_MEMORY_TESTS && message.memory_tests) {
    memoryTests.value = message.memory_tests
    isLoading.value = false
  }
  else if (message.type === MESSAGE_TYPES.response.RETURN_PERFORMANCE_TESTS && message.performance_tests) {
    performanceTests.value = message.performance_tests
    isLoading.value = false
  }
}

let unregisterHandler: (() => void) | null = null

watch(generateTests, (newValue) => {
  setGenerateTests(newValue)
  if (newValue) {
    messageSent.value = false
    sendTestsRequest()
  }
})

watch(
  () => webSocketStore.isConnected,
  (isConnected) => {
    if (isConnected) {
      sendTestsRequest()
    }
  },
  { immediate: true },
)

onMounted(() => {
  unregisterHandler = webSocketStore.onMessage(handleMessage)
  if (generateTests.value && hasCode.value) {
    sendTestsRequest()
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
    class="test-results-card h-100 pa-6"
    elevation="4"
    :class="{'disabled-card': !generateTests}"
  >
    <!-- Header with checkbox -->
    <div class="d-flex align-center justify-space-between mb-4">
      <div class="flex-grow-1 text-center">
        <v-icon
          size="48"
          color="primary"
          class="mb-3"
          :class="{'disabled-icon': !generateTests}"
        >
          mdi-test-tube
        </v-icon>

        <h2 class="text-h4 mb-2">
          Test Results
        </h2>

        <p class="text-body-1 text-medium-emphasis">
          Comprehensive test cases generated for your function
        </p>
      </div>

      <div class="checkbox-container">
        <v-checkbox
          v-model="generateTests"
          color="primary"
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
      v-if="!generateTests"
      class="disabled-content text-center"
    >
      <v-icon
        size="64"
        color="grey-lighten-1"
        class="mb-3"
      >
        mdi-test-tube-off
      </v-icon>

      <h3 class="text-h6 text-medium-emphasis mb-2">
        Test Generation Disabled
      </h3>

      <p class="text-body-2 text-medium-emphasis">
        Enable test generation to see comprehensive test cases for your function.
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

      <!-- Loading state or waiting for results -->
      <div
        v-else-if="isLoading"
        class="text-center"
      >
        <v-progress-circular
          indeterminate
          color="primary"
          size="32"
          class="mb-3"
        />

        <p class="text-body-2 text-medium-emphasis">
          Generating test cases...
        </p>
      </div>

      <!-- Test results -->
      <div v-else>
        <!-- Test Groups with transition -->
        <transition-group
          name="test-group"
          tag="div"
          appear
        >
          <TestGroup
            v-if="unitTests.length > 0"
            key="unit"
            :tests="unitTests"
            type="unit"
            title="Unit Tests"
            icon="mdi-test-tube"
            color="primary"
          />

          <TestGroup
            v-if="memoryTests.length > 0"
            key="memory"
            :tests="memoryTests"
            type="memory"
            title="Memory Tests"
            icon="mdi-memory"
            color="warning"
          />

          <TestGroup
            v-if="performanceTests.length > 0"
            key="performance"
            :tests="performanceTests"
            type="performance"
            title="Performance Tests"
            icon="mdi-speedometer"
            color="success"
          />
        </transition-group>

        <!-- No tests received yet -->
        <v-alert
          v-if="!hasAnyTests"
          type="info"
          variant="tonal"
          class="mb-4"
        >
          Test results will be displayed here.
        </v-alert>
      </div>
    </div>
  </v-card>
</template>

<style scoped>
.test-results-card {
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: linear-gradient(135deg, rgb(var(--v-theme-primary), 0.05) 0%, transparent 100%);
}

.test-results-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1) !important;
}

/* Test group transition animations */
.test-group-enter-active,
.test-group-leave-active {
  transition: all 0.5s ease;
}

.test-group-enter-from {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

.test-group-leave-to {
  opacity: 0;
  transform: translateY(-20px) scale(0.95);
}

.test-group-move {
  transition: transform 0.5s ease;
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
  .test-results-card {
    padding: 1rem;
  }
}
</style>
