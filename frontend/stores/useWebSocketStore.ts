import type { RequestMessage, ResponseMessage } from '~/types/websocket'

export const useWebSocketStore = defineStore('websocket', () => {
  const socket = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const error = ref<string | null>(null)
  const messageHandlers = ref<((data: ResponseMessage) => void)[]>([])
  const initialized = ref(false)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5
  const reconnectDelay = 3000

  const getConnectionStatus = computed(() => isConnected.value)
  const getError = computed(() => error.value)

  const connect = () => {
    if (socket.value) {
      return
    }

    try {
      const config = useRuntimeConfig()
      const baseUrl = config.public.websocketServerUrl || 'ws://localhost:8000'
      const url = baseUrl.endsWith('/')
        ? `${baseUrl}ws`
        : `${baseUrl}/ws`

      socket.value = new WebSocket(url)

      socket.value.onopen = () => {
        isConnected.value = true
        error.value = null
        reconnectAttempts.value = 0
        console.warn('WebSocket connected')
      }

      socket.value.onmessage = (event) => {
        try {
          const data: ResponseMessage = JSON.parse(event.data)

          // Handle ping messages
          if (data.type === 'ping') {
            // Send pong response
            const pongMessage = {
              type: 'pong',
              timestamp: Date.now(),
            }
            socket.value?.send(JSON.stringify(pongMessage))

            return
          }

          messageHandlers.value.forEach(handler => handler(data))
        }
        catch (e) {
          console.error('Failed to parse WebSocket message data:', e)
        }
      }

      socket.value.onerror = (event) => {
        console.error('WebSocket error:', event)
        error.value = 'WebSocket connection failed.'
        isConnected.value = false
      }

      socket.value.onclose = () => {
        isConnected.value = false
        socket.value = null
        console.warn('WebSocket disconnected')

        if (import.meta.client) {
          const { showConnectionError } = useSnackbar()
          showConnectionError()

          // Attempt to reconnect
          if (reconnectAttempts.value < maxReconnectAttempts) {
            reconnectAttempts.value++
            console.warn(`Attempting to reconnect... (${reconnectAttempts.value}/${maxReconnectAttempts})`)
            setTimeout(() => {
              connect()
            }, reconnectDelay * reconnectAttempts.value)
          }
        }

        messageHandlers.value = []
      }
    }
    catch (e: any) {
      console.error('Failed to create WebSocket:', e)
      error.value = e.message || 'An unknown error occurred.'
    }
  }

  const disconnect = () => {
    if (socket.value) {
      socket.value.close()
    }
  }

  const sendMessage = (data: RequestMessage) => {
    if (socket.value && isConnected.value) {
      socket.value.send(JSON.stringify(data))
    }
    else {
      console.warn('WebSocket is not connected.')
    }
  }

  const onMessage = (handler: (data: ResponseMessage) => void) => {
    messageHandlers.value.push(handler)

    const unregister = () => {
      const index = messageHandlers.value.indexOf(handler)
      if (index > -1) {
        messageHandlers.value.splice(index, 1)
      }
    }

    return unregister
  }

  const init = () => {
    if (!initialized.value && import.meta.client) {
      initialized.value = true
      connect()
    }
  }

  return {
    isConnected: readonly(isConnected),
    error: readonly(error),
    getConnectionStatus,
    getError,
    connect,
    disconnect,
    sendMessage,
    onMessage,
    init,
  }
})
