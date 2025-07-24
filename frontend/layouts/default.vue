<script setup lang="ts">
import { useStepper } from '~/composables/useStepper'

const webSocketStore = useWebSocketStore()

const {
  stepperItems,
  currentStep,
  navigateToStep,
} = useStepper()

function receiveMessage(response: any) {
  console.warn('Received message:', response)
}

function handleStepperClick(stepValue: number) {
  navigateToStep(stepValue)
}

let unregister: () => void

onMounted(() => {
  unregister = webSocketStore.onMessage(receiveMessage)
})

onUnmounted(() => {
  if (unregister) {
    unregister()
  }
})
</script>

<template>
  <v-app>
    <v-main>
      <v-container>
        <div class="d-flex justify-space-between align-center mb-4">
          <h1 class="text-h4">
            CodeLens
          </h1>
        </div>

        <v-stepper
          :model-value="currentStep"
          class="mb-6"
        >
          <v-stepper-header>
            <template
              v-for="(item, index) in stepperItems"
              :key="item.value"
            >
              <v-stepper-item
                :title="item.title"
                :value="item.value"
                :complete="currentStep > item.value"
                editable
                @click="handleStepperClick(item.value)"
              />

              <v-divider
                v-if="index < stepperItems.length - 1"
              />
            </template>
          </v-stepper-header>
        </v-stepper>

        <div class="stepper-content">
          <slot />
        </div>
      </v-container>
    </v-main>

    <!-- Global Snackbar -->
    <AppSnackbar />
  </v-app>
</template>
