<script setup lang="ts">
import type { Test } from '~/types/websocket'

defineProps<{
  test: Test
  index: number
}>()

function getStatusColor(test: Test) {
  if (!test.status) {
    return 'grey'
  }

  switch (test.status) {
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
}

function getStatusIcon(test: Test) {
  if (!test.status) {
    return 'mdi-clock-outline'
  }

  switch (test.status) {
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
}
</script>

<template>
  <v-expansion-panel
    :color="getStatusColor(test)"
    :class="{
      'test-running': test.status === 'running',
      'test-success': test.status === 'success',
      'test-failed': test.status === 'failed',
    }"
  >
    <v-expansion-panel-title>
      <div class="d-flex align-center ga-3">
        <!-- Status Icon -->
        <v-icon
          :icon="getStatusIcon(test)"
          :color="getStatusColor(test)"
          :class="{'rotating': test.status === 'running'}"
          size="24"
          class="status-icon"
        />

        <!-- Test Title -->
        <span class="text-body-1 font-weight-medium">
          {{ test.title }}
        </span>

        <!-- Execution Time -->
        <div
          v-if="test.execution_time"
          class="ml-auto"
        >
          <v-chip
            color="info"
            variant="elevated"
            size="x-small"
            prepend-icon="mdi-clock-outline"
            class="ml-auto"
          >
            {{ test.execution_time.toFixed(2) }}ms
          </v-chip>
        </div>
      </div>
    </v-expansion-panel-title>

    <v-expansion-panel-text>
      <!-- Test Code -->
      <div class="mb-4">
        <h4 class="text-subtitle-2 mb-2">
          Test Code
        </h4>

        <CodeHighlight
          :code="test.code"
          copyable
        />
      </div>

      <!-- Execution Results -->
      <div v-if="test.status && test.status !== 'pending'">
        <!-- Success Results -->
        <div v-if="test.status === 'success' && test.execution_output">
          <v-alert
            type="success"
            variant="tonal"
            class="mb-3"
          >
            <template #title>
              Test Passed Successfully
            </template>
          </v-alert>
        </div>

        <!-- Failed Results -->
        <div v-else-if="test.status === 'failed'">
          <v-alert
            type="error"
            variant="tonal"
            class="mb-3"
          >
            <template #title>
              Test Failed
            </template>

            <div
              v-if="test.execution_error"
              class="text-body-2 mt-2"
            >
              <strong>Error:</strong>

              <pre class="test-output">{{ test.execution_error }}</pre>
            </div>

            <div
              v-if="test.execution_output"
              class="text-body-2 mt-2"
            >
              <strong>Output:</strong>

              <pre class="test-output">{{ test.execution_output }}</pre>
            </div>
          </v-alert>
        </div>

        <!-- Running Status -->
        <div v-else-if="test.status === 'running'">
          <v-alert
            type="warning"
            variant="tonal"
            class="mb-3"
          >
            <template #title>
              Test Running...
            </template>

            <div class="d-flex align-center ga-2 mt-2">
              <v-progress-circular
                indeterminate
                size="16"
                width="2"
                color="warning"
              />

              <span class="text-body-2">Executing test case...</span>
            </div>
          </v-alert>
        </div>
      </div>
    </v-expansion-panel-text>
  </v-expansion-panel>
</template>

<style scoped>
.v-expansion-panel {
  transition: all 0.2s ease;
  border-radius: 8px !important;
  margin-bottom: 8px;
}

.v-expansion-panel:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.test-running {
  border-left: 4px solid rgb(var(--v-theme-warning));
  background: linear-gradient(90deg, rgba(var(--v-theme-warning), 0.1) 0%, transparent 100%);
}

.test-success {
  border-left: 4px solid rgb(var(--v-theme-success));
  background: linear-gradient(90deg, rgba(var(--v-theme-success), 0.1) 0%, transparent 100%);
}

.test-failed {
  border-left: 4px solid rgb(var(--v-theme-error));
  background: linear-gradient(90deg, rgba(var(--v-theme-error), 0.1) 0%, transparent 100%);
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

.test-output {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.875rem;
  line-height: 1.4;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  padding: 8px 12px;
  border-radius: 4px;
  margin: 8px 0;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
}

.status-icon {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  padding: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

@media (max-width: 960px) {
  .test-output {
    font-size: 0.8rem;
    max-height: 150px;
  }
}
</style>
