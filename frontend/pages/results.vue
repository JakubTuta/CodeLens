<script setup lang="ts">
import { useStepperNavigation } from '~/composables/useStepperNavigation'

const { goPrevious, canGoPrevious, previousStepName } = useStepperNavigation()

function startOver() {
  navigateTo('/home')
}
</script>

<template>
  <v-container>
    <v-card>
      <v-card-title>Analysis Results</v-card-title>

      <v-card-text>
        <v-alert
          type="info"
          variant="tonal"
        >
          Analysis results will be displayed here.
        </v-alert>

        <v-btn
          color="success"
          class="mt-4"
          @click="startOver"
        >
          Start Over
        </v-btn>
      </v-card-text>
    </v-card>

    <v-divider class="my-6" />

    <v-row justify="start">
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
    </v-row>
  </v-container>
</template>
