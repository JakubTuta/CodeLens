<script setup lang="ts">
import { useStepperNavigation } from '~/composables/useStepperNavigation'

const code = ref('')

const { goNext, goPrevious, canGoNext, canGoPrevious, nextStepName, previousStepName } = useStepperNavigation()

function analyzeCode() {
  console.warn('Analyzing code:', code.value
    ? `${code.value.length} characters`
    : 'Empty')

  if (canGoNext.value) {
    goNext()
  }
}
</script>

<template>
  <v-container>
    <v-card>
      <v-card-title>Enter Code</v-card-title>

      <v-card-text>
        <v-textarea
          v-model="code"
          label="Code"
          placeholder="Paste your code here..."
          rows="15"
        />

        <v-btn
          color="primary"
          class="mt-4"
          @click="analyzeCode"
        >
          Analyze Code
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
