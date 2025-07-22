export interface StepperItem {
  title: string
  path: string
  value: number
}

export const stepperItems: StepperItem[] = [
  { title: 'Home Page', path: '/home', value: 0 },
  { title: 'Enter AI API Key', path: '/enter-api-key', value: 1 },
  { title: 'Enter Code', path: '/enter-code', value: 2 },
  { title: 'Results', path: '/results', value: 3 },
]

export function useStepper() {
  const router = useRouter()
  const route = useRoute()

  const getCurrentStepFromRoute = () => {
    const currentPath = route.path
    const item = stepperItems.find(item => item.path === currentPath)

    return item
      ? item.value
      : 0
  }

  const currentStep = ref(getCurrentStepFromRoute())

  const currentStepperItem = computed(() => {
    return stepperItems.find(item => item.value === currentStep.value) || stepperItems[0]
  })

  watch(() => route.path, (newPath) => {
    const item = stepperItems.find(item => item.path === newPath)
    if (item && item.value !== currentStep.value) {
      currentStep.value = item.value
    }
  })

  const navigateToStep = async (stepValue: number) => {
    const item = stepperItems.find(item => item.value === stepValue)
    if (item) {
      currentStep.value = stepValue
      await router.push(item.path)
    }
  }

  const nextStep = async () => {
    const nextStepValue = Math.min(currentStep.value + 1, stepperItems.length - 1)
    await navigateToStep(nextStepValue)
  }

  const previousStep = async () => {
    const prevStepValue = Math.max(currentStep.value - 1, 0)
    await navigateToStep(prevStepValue)
  }

  const isStepComplete = (_stepValue: number) => {
    return true
  }

  return {
    stepperItems,
    currentStep: readonly(currentStep),
    currentStepperItem,
    navigateToStep,
    nextStep,
    previousStep,
    isStepComplete,
  }
}
