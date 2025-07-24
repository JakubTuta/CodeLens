export default defineNuxtPlugin(() => {
  if (import.meta.client) {
    const webSocketStore = useWebSocketStore()
    webSocketStore.init()
  }
})
