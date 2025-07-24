<script setup lang="ts">
import CodeDisplay from '~/components/results/CodeDisplay.vue'
import Documentation from '~/components/results/Documentation.vue'
import Improvements from '~/components/results/Improvements.vue'
import TestResults from '~/components/results/TestResults.vue'
import { useStepperNavigation } from '~/composables/useStepperNavigation'

const { goPrevious, canGoPrevious, previousStepName } = useStepperNavigation()
const webSocketStore = useWebSocketStore()

onMounted(() => {
  webSocketStore.init()
})
</script>

<template>
  <v-container class="results-page pa-6">
    <!-- Code Display Section -->
    <div class="code-display-section mb-6">
      <CodeDisplay />
    </div>

    <!-- Results Section -->
    <div class="results-section mb-6">
      <h2 class="text-h5 section-title pb-4">
        Results
      </h2>

      <div class="results-content">
        <v-row>
          <!-- Tests Column -->
          <v-col
            cols="12"
            lg="4"
            class="mb-6"
          >
            <TestResults />
          </v-col>

          <!-- Documentation Column -->
          <v-col
            cols="12"
            lg="4"
            class="mb-6"
          >
            <Documentation />
          </v-col>

          <!-- Improvements Column -->
          <v-col
            cols="12"
            lg="4"
            class="mb-6"
          >
            <Improvements />
          </v-col>
        </v-row>
      </div>
    </div>

    <!-- Navigation Section -->
    <div class="navigation-section">
      <div class="navigation-content">
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
      </div>
    </div>
  </v-container>
</template>

<style scoped>
.results-page {
  min-height: 100vh;
}

.hero-section {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary-lighten-1), 0.1) 0%, rgb(var(--v-theme-secondary-lighten-1), 0.1) 100%);
  position: relative;
}

.hero-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image:
    radial-gradient(circle at 20% 50%, rgb(var(--v-theme-success), 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgb(var(--v-theme-info), 0.1) 0%, transparent 50%);
  pointer-events: none;
}

.hero-title {
  font-size: clamp(2.5rem, 5vw, 3.5rem);
  font-weight: 700;
  line-height: 1.2;
}

.gradient-text {
  background: linear-gradient(45deg, rgb(var(--v-theme-success)), rgb(var(--v-theme-info)));
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 200% 200%;
  animation: gradient-shift 3s ease-in-out infinite;
}

@keyframes gradient-shift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.hero-subtitle {
  max-width: 600px;
  margin: 0 auto;
  opacity: 0.9;
}

.results-section {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary), 0.02) 0%, rgb(var(--v-theme-secondary), 0.02) 100%);
}

@media (max-width: 1264px) {
  .results-section .v-col {
    margin-bottom: 2rem;
  }
}

@media (max-width: 960px) {
  .hero-section {
    padding-top: 2rem;
    padding-bottom: 2rem;
  }
}
</style>
