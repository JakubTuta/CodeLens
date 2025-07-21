import { useEventListener } from '@vueuse/core'
import { useStepperNavigation } from './useStepperNavigation'

export function useStepperKeyboardNavigation() {
  const { goNext, goPrevious, canGoNext, canGoPrevious } = useStepperNavigation()

  useEventListener('keydown', (e: KeyboardEvent) => {
    if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
      return
    }

    if (e.ctrlKey && e.key === 'ArrowRight' && canGoNext.value) {
      e.preventDefault()
      goNext()
    }

    if (e.ctrlKey && e.key === 'ArrowLeft' && canGoPrevious.value) {
      e.preventDefault()
      goPrevious()
    }
  })

  return {
    goNext,
    goPrevious,
    canGoNext,
    canGoPrevious,
  }
}
