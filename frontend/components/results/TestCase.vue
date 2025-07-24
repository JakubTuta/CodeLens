<script setup lang="ts">
import type { Test } from '~/types/websocket'

defineProps<{
  test: Test
  index: number
}>()
</script>

<template>
  <v-expansion-panel>
    <v-expansion-panel-title>
      <div class="d-flex align-center ga-3">
        <v-chip
          :color="test.type === 'unit'
            ? 'primary'
            : test.type === 'memory'
              ? 'warning'
              : 'success'"
          variant="tonal"
          size="small"
          class="text-caption"
        >
          {{ test.type.toUpperCase() }}
        </v-chip>

        <span class="text-body-1 font-weight-medium">
          {{ test.title }}
        </span>
      </div>
    </v-expansion-panel-title>

    <v-expansion-panel-text>
      <CodeHighlight
        :code="test.code"
        copyable
      />
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
</style>
