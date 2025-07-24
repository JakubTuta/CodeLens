<template>
  <v-alert
    v-if="show"
    :type="type"
    :variant="alertVariant"
    :class="{'alert-loading': isLoading}"
    class="mt-4"
    closable
    @click:close="$emit('close')"
  >
    <div class="d-flex align-center">
      <v-progress-circular
        v-if="isLoading"
        indeterminate
        size="20"
        color="primary"
        class="mr-3"
      />
      {{ message }}
    </div>
  </v-alert>
</template>

<script setup lang="ts">
interface Props {
  show: boolean
  type: 'success' | 'error' | 'info'
  message: string
  isLoading?: boolean
}

const props = defineProps<Props>()

defineEmits<{
  close: []
}>()

const alertVariant = computed(() => {
  return props.isLoading
    ? 'tonal'
    : 'flat'
})
</script>

<style scoped>
.alert-loading {
  position: relative;
  overflow: hidden;
  border: 2px dashed rgb(var(--v-theme-primary)) !important;
}

.alert-loading::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  animation: loading-shimmer 1.5s infinite;
  z-index: 1;
}

@keyframes loading-shimmer {
  0% {
    left: -100%;
  }
  100% {
    left: 100%;
  }
}
</style>
