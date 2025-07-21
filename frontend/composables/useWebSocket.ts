import { ref } from 'vue'

const socket = ref<WebSocket | null>(null)
const isConnected = ref(false)
const error = ref<string | null>(null)

const messageHandlers = ref<((data: any) => void)[]>([])

export function useWebSocket() {
  const config = useRuntimeConfig()
  const baseUrl = config.public.websocketServerUrl
  const url = baseUrl.endsWith('/')
    ? `${baseUrl}ws`
    : `${baseUrl}/ws`

  const connect = () => {
    if (socket.value) {
      return
    }

    try {
      socket.value = new WebSocket(url)

      socket.value.onopen = () => {
        isConnected.value = true
        error.value = null
        console.log('WebSocket connected')
      }

      socket.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
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
        messageHandlers.value = []
        console.log('WebSocket disconnected')
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

  const onSendMessage = (data: any) => {
    if (socket.value && isConnected.value) {
      socket.value.send(JSON.stringify(data))
    }
    else {
      console.warn('WebSocket is not connected.')
    }
  }

  const onMessage = (handler: (data: any) => void) => {
    messageHandlers.value.push(handler)

    const unregister = () => {
      const index = messageHandlers.value.indexOf(handler)
      if (index > -1) {
        messageHandlers.value.splice(index, 1)
      }
    }

    return unregister
  }

  return {
    isConnected,
    error,
    connect,
    disconnect,
    onSendMessage,
    onMessage,
  }
}
