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

const { type } = toRefs(props)

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

const config = computed(() => typeConfig[type.value])
</script>

<template>
  <div
    v-if="tests.length > 0"
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
          {{ title }}
        </h3>

        <v-chip
          :color="config.color"
          variant="tonal"
          size="small"
        >
          {{ tests.length }} {{ tests.length === 1
            ? 'test'
            : 'tests' }}
        </v-chip>
      </div>

      <p class="text-body-2 text-medium-emphasis ml-9">
        {{ config.description }}
      </p>
    </div>

    <v-expansion-panels
      variant="accordion"
      class="test-expansion-panels"
    >
      <TestCase
        v-for="(test, index) in tests"
        :key="`${type}-${index}`"
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

@media (max-width: 960px) {
  .test-group {
    padding: 12px;
  }
}
</style>
