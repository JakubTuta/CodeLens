<script setup lang="ts">
import type { Test, TestType } from '~/types/websocket'
import TestCase from './TestCase.vue'

const props = defineProps<{
  tests: Test[]
  type: TestType
  title: string
  icon: string
  color: string
}>()

const typeConfig = {
  unit: {
    icon: 'mdi-test-tube',
    color: 'primary',
    description: 'Basic functionality and edge case testing',
  },
  memory: {
    icon: 'mdi-memory',
    color: 'warning',
    description: 'Memory usage and leak detection',
  },
  performance: {
    icon: 'mdi-speedometer',
    color: 'success',
    description: 'Performance benchmarks and optimization',
  },
}

const config = computed(() => typeConfig[props.type as keyof typeof typeConfig])

const testStats = computed(() => {
  const total = props.tests.length
  const completed = props.tests.filter((test: Test) => test.status === 'success' || test.status === 'failed').length
  const successful = props.tests.filter((test: Test) => test.status === 'success').length
  const failed = props.tests.filter((test: Test) => test.status === 'failed').length
  const running = props.tests.filter((test: Test) => test.status === 'running').length
  const pending = props.tests.filter((test: Test) => !test.status || test.status === 'pending').length

  return {
    total,
    completed,
    successful,
    failed,
    running,
    pending,
    isRunning: running > 0,
  }
})

const overallStatus = computed(() => {
  if (testStats.value.running > 0) {
    return 'running'
  }
  if (testStats.value.pending > 0 && testStats.value.completed === 0) {
    return 'pending'
  }
  if (testStats.value.failed > 0) {
    return 'failed'
  }
  if (testStats.value.successful === testStats.value.total && testStats.value.total > 0) {
    return 'success'
  }

  return 'pending'
})

const statusColor = computed(() => {
  switch (overallStatus.value) {
    case 'pending':
      return 'grey'
    case 'running':
      return 'warning'
    case 'success':
      return 'success'
    case 'failed':
      return 'error'
    default:
      return 'grey'
  }
})

const statusIcon = computed(() => {
  switch (overallStatus.value) {
    case 'pending':
      return 'mdi-clock-outline'
    case 'running':
      return 'mdi-loading'
    case 'success':
      return 'mdi-check-circle'
    case 'failed':
      return 'mdi-alert-circle'
    default:
      return 'mdi-clock-outline'
  }
})
</script>

<template>
  <div
    v-if="props.tests.length > 0"
    class="test-group mb-6"
  >
    <div class="test-group-header mb-4">
      <div class="d-flex align-center ga-3 mb-2">
        <v-icon
          :icon="config.icon"
          :color="config.color"
          size="24"
        />

        <h3 class="text-h6 font-weight-bold">
          {{ props.title }}
        </h3>

        <!-- Overall Status -->
        <div class="d-flex align-center ga-2 ml-auto">
          <!-- Execution Statistics -->
          <div
            v-if="testStats.completed > 0"
            class="text-caption text-medium-emphasis"
          >
            {{ testStats.successful }}/{{ testStats.total }} passed
          </div>

          <!-- Status Icon -->
          <v-icon
            :icon="statusIcon"
            :color="statusColor"
            :class="{'rotating': overallStatus === 'running'}"
            size="20"
          />
        </div>
      </div>

      <p class="text-body-2 text-medium-emphasis ml-9">
        {{ config.description }}
      </p>

      <!-- Progress Bar for Running Tests -->
      <div
        v-if="testStats.isRunning || testStats.pending > 0"
        class="ml-9 mt-3"
      >
        <v-progress-linear
          :model-value="testStats.completed / testStats.total * 100"
          :color="statusColor"
          height="4"
          rounded
        />

        <div class="d-flex justify-space-between mt-1">
          <span class="text-caption text-medium-emphasis">
            {{ testStats.completed }}/{{ testStats.total }} completed
          </span>

          <span
            v-if="testStats.isRunning"
            class="text-caption text-warning"
          >
            {{ testStats.running }} running
          </span>
        </div>
      </div>
    </div>

    <v-expansion-panels
      variant="accordion"
      class="test-expansion-panels"
    >
      <TestCase
        v-for="(test, index) in props.tests"
        :key="`${props.type}-${index}`"
        :test="test"
        :index="index"
      />
    </v-expansion-panels>
  </div>
</template>

<style scoped>
.test-group {
  border-radius: 12px;
  padding: 16px;
  background: linear-gradient(135deg, rgba(var(--v-theme-surface-variant), 0.3) 0%, transparent 100%);
  border: 1px solid rgba(var(--v-theme-outline), 0.1);
  transition: all 0.3s ease;
}

.test-group:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.test-group-header {
  border-bottom: 1px solid rgba(var(--v-theme-outline), 0.1);
  padding-bottom: 12px;
}

.test-expansion-panels {
  border-radius: 8px;
}

.rotating {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 960px) {
  .test-group {
    padding: 12px;
  }
}
</style>
