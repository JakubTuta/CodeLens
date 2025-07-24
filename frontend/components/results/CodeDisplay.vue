<script setup lang="ts">
const { getCode, hasCode } = useCookieStore()

const code = getCode()
const codeExists = hasCode()

function goToEnterCode() {
  navigateTo('/enter-code')
}
</script>

<template>
  <v-container class="code-section py-8">
    <v-row justify="center">
      <v-col
        cols="12"
        md="10"
        lg="8"
      >
        <v-card
          v-if="codeExists"
          class="code-display-card pa-6"
          elevation="4"
        >
          <div class="mb-4 text-center">
            <v-icon
              size="40"
              color="primary"
              class="mb-3"
            >
              mdi-code-brackets
            </v-icon>

            <h2 class="text-h5 mb-2">
              Your Code
            </h2>

            <p class="text-body-1 text-medium-emphasis">
              The function being analyzed
            </p>
          </div>

          <CodeHighlight
            :code="code"
            title="Your Code"
            copyable
          />
        </v-card>

        <v-card
          v-else
          class="no-code-card pa-6"
          color="warning-lighten-5"
          elevation="4"
        >
          <div class="text-center">
            <v-icon
              size="64"
              color="warning"
              class="mb-4"
            >
              mdi-alert-circle
            </v-icon>

            <h2 class="text-h4 mb-3">
              No Code Found
            </h2>

            <p class="text-h6 text-medium-emphasis mb-6">
              Please enter your function code to see analysis results
            </p>

            <v-alert
              type="info"
              class="mb-6"
              icon="mdi-information"
            >
              <strong>Next Step:</strong> Paste your Python function in the code editor
              to generate comprehensive test cases, documentation, and optimization tips.
            </v-alert>

            <v-btn
              size="large"
              color="primary"
              variant="flat"
              rounded="xl"
              class="px-8"
              @click="goToEnterCode"
            >
              <v-icon start>
                mdi-code-tags
              </v-icon>
              Enter Your Code
            </v-btn>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<style scoped>
.code-section {
  background: linear-gradient(135deg, rgb(var(--v-theme-info), 0.03) 0%, rgb(var(--v-theme-primary), 0.03) 100%);
}

.code-display-card {
  transition: all 0.3s ease;
  border: 1px solid rgb(var(--v-theme-primary), 0.2);
  background: linear-gradient(135deg, rgb(var(--v-theme-primary), 0.05) 0%, transparent 100%);
}

.code-display-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1) !important;
}

.no-code-card {
  transition: all 0.3s ease;
  border: 1px solid rgb(var(--v-theme-warning), 0.3);
}

.no-code-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1) !important;
}
</style>
