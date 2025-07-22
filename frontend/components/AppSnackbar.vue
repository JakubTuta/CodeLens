<script setup lang="ts">
import { useSnackbar } from '~/composables/useSnackbar'

const {
  isVisible,
  message,
  color,
  timeout,
  actions,
  hide,
} = useSnackbar()

function handleActionClick(action: () => void) {
  action()
  hide()
}
</script>

<template>
  <v-snackbar
    v-model="isVisible"
    :color="color"
    :timeout="timeout"
    location="top"
    rounded="pill"
  >
    <div class="d-flex align-center justify-space-between w-100">
      <span>{{ message }}</span>

      <div
        v-if="actions.length > 0"
        class="ml-4"
      >
        <v-btn
          v-for="(action, index) in actions"
          :key="index"
          variant="text"
          size="small"
          @click="handleActionClick(action.action)"
        >
          {{ action.label }}
        </v-btn>
      </div>
    </div>

    <template #actions>
      <v-btn
        variant="text"
        @click="hide"
      >
        <v-icon>mdi-close</v-icon>
      </v-btn>
    </template>
  </v-snackbar>
</template>
