import { useStepper } from '~/composables/useStepper'

export function useStepperNavigation() {
  const { nextStep, previousStep, currentStep, stepperItems } = useStepper()

  const canGoNext = computed(() => {
    return currentStep.value < stepperItems.length - 1
  })

  const canGoPrevious = computed(() => {
    return currentStep.value > 0
  })

  const nextStepName = computed(() => {
    const nextStepValue = currentStep.value + 1
    const nextItem = stepperItems.find(item => item.value === nextStepValue)

    return nextItem
      ? nextItem.title
      : ''
  })

  const previousStepName = computed(() => {
    const prevStepValue = currentStep.value - 1
    const prevItem = stepperItems.find(item => item.value === prevStepValue)

    return prevItem
      ? prevItem.title
      : ''
  })

  const goNext = () => {
    if (canGoNext.value) {
      nextStep()
    }
  }

  const goPrevious = () => {
    if (canGoPrevious.value) {
      previousStep()
    }
  }

  return {
    goNext,
    goPrevious,
    canGoNext,
    canGoPrevious,
    nextStepName,
    previousStepName,
    nextStep,
    previousStep,
    currentStep,
  }
}
