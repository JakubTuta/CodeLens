<script setup lang="ts">
import { useStepperNavigation } from '~/composables/useStepperNavigation'

const apiKey = ref('')

const { goNext, goPrevious, canGoNext, canGoPrevious, nextStepName, previousStepName } = useStepperNavigation()

function saveApiKey() {
  console.warn('API Key saved:', apiKey.value
    ? '[REDACTED]'
    : 'Empty')

  if (canGoNext.value) {
    goNext()
  }
}
</script>

<template>
  <v-container>
    <v-card>
      <v-card-title>Enter AI API Key</v-card-title>

      <v-card-text>
        <v-text-field
          v-model="apiKey"
          label="API Key"
          type="password"
          placeholder="Enter your AI API key"
        />

        <v-btn
          color="primary"
          class="mt-4"
          @click="saveApiKey"
        >
          Save API Key
        </v-btn>
      </v-card-text>
    </v-card>

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
