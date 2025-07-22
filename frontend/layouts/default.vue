<script setup lang="ts">
import { useStepper } from '~/composables/useStepper'
import { useStepperKeyboardNavigation } from '~/composables/useStepperKeyboardNavigation'
import { useWebSocket } from '~/composables/useWebSocket'

const {
  connect,
  disconnect,
  onMessage,
} = useWebSocket()

const {
  stepperItems,
  currentStep,
  navigateToStep,
} = useStepper()

useStepperKeyboardNavigation()

function connectSocket() {
  connect()
}

function receiveMessage(response: any) {
  console.warn('Received message:', response)
}

function handleStepperClick(stepValue: number) {
  navigateToStep(stepValue)
}

let unregister: () => void

onMounted(() => {
  connectSocket()
  unregister = onMessage(receiveMessage)
})

onUnmounted(() => {
  if (unregister) {
    unregister()
  }

  disconnect()
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

          <v-tooltip bottom>
            <template #activator="{props}">
              <v-icon
                v-bind="props"
                color="grey"
              >
                mdi-keyboard
              </v-icon>
            </template>

            <div>
              Keyboard shortcuts:

              <br>
              Ctrl + ← Previous step

              <br>
              Ctrl + → Next step
            </div>
          </v-tooltip>
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
