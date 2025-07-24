export interface SnackbarOptions {
  message: string
  color?: string
  timeout?: number
  actions?: Array<{
    label: string
    action: () => void
  }>
}

const isVisible = ref(false)
const message = ref('')
const color = ref('error')
const timeout = ref(5000)
const actions = ref<Array<{ label: string, action: () => void }>>([])

export function useSnackbar() {
  const show = (options: SnackbarOptions) => {
    message.value = options.message
    color.value = options.color || 'error'
    timeout.value = options.timeout || 5000
    actions.value = options.actions || []
    isVisible.value = true
  }

  const hide = () => {
    isVisible.value = false
  }

  const showError = (errorMessage: string, timeoutMs?: number) => {
    show({
      message: errorMessage,
      color: 'error',
      timeout: timeoutMs || 5000,
    })
  }

  const showSuccess = (successMessage: string, timeoutMs?: number) => {
    show({
      message: successMessage,
      color: 'success',
      timeout: timeoutMs || 3000,
    })
  }

  const showWarning = (warningMessage: string, timeoutMs?: number) => {
    show({
      message: warningMessage,
      color: 'warning',
      timeout: timeoutMs || 4000,
    })
  }

  const showInfo = (infoMessage: string, timeoutMs?: number) => {
    show({
      message: infoMessage,
      color: 'info',
      timeout: timeoutMs || 3000,
    })
  }

  const showConnectionError = () => {
    show({
      message: 'Connection lost. Please refresh the page to reconnect.',
      color: 'error',
      timeout: 0,
      actions: [
        {
          label: 'Refresh',
          action: () => {
            if (typeof window !== 'undefined') {
              window.location.reload()
            }
          },
        },
      ],
    })
  }

  return {
    isVisible,
    message,
    color,
    timeout,
    actions,
    show,
    hide,
    showError,
    showSuccess,
    showWarning,
    showInfo,
    showConnectionError,
  }
}
