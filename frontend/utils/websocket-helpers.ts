import type { AvailableAiModels, RequestMessage, RequestMessageTypes, SupportedLanguages } from '~/types/websocket'
import { useCookieStore } from '~/composables/useCookieStore'
import { MESSAGE_TYPES } from '~/types/websocket'

export function createRequestMessage(
  id: string,
  type: RequestMessageTypes,
  options?: {
    code?: string
    language?: SupportedLanguages
    ai_model?: AvailableAiModels
    ai_api_key?: string
    generate_tests?: boolean
    generate_docs?: boolean
    generate_improvements?: boolean
  },
): RequestMessage {
  const cookieStore = useCookieStore()

  const message: RequestMessage = {
    id,
    type,
    ...options,
  }

  if (cookieStore.hasApiKey())
    message.ai_api_key = cookieStore.getApiKey().value

  if (cookieStore.hasAiModel())
    message.ai_model = cookieStore.getAiModel().value as AvailableAiModels

  if (cookieStore.hasGenerateTests())
    message.generate_tests = cookieStore.getGenerateTests()

  if (cookieStore.hasGenerateDocumentation())
    message.generate_docs = cookieStore.getGenerateDocumentation()

  if (cookieStore.hasGenerateImprovements())
    message.generate_improvements = cookieStore.getGenerateImprovements()

  return message
}

export function createGenerateTestsMessage(id: string, code: string, language: SupportedLanguages = 'python'): RequestMessage {
  return createRequestMessage(id, MESSAGE_TYPES.request.GENERATE_TESTS, { code, language })
}

export function createGenerateDocsMessage(id: string, code: string, language: SupportedLanguages = 'python'): RequestMessage {
  return createRequestMessage(id, MESSAGE_TYPES.request.GENERATE_DOCS, { code, language })
}

export function createGenerateImprovementsMessage(id: string, code: string, language: SupportedLanguages = 'python'): RequestMessage {
  return createRequestMessage(id, MESSAGE_TYPES.request.GENERATE_IMPROVEMENTS, { code, language })
}

export function createTestAiMessage(id: string): RequestMessage {
  return createRequestMessage(id, MESSAGE_TYPES.request.TEST_AI)
}

export function createVerifyCodeMessage(id: string, code: string, language: SupportedLanguages = 'python'): RequestMessage {
  return createRequestMessage(id, MESSAGE_TYPES.request.VERIFY_CODE, { code, language })
}

export function generateMessageId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}
