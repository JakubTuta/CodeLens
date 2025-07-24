import type { RequestMessage, RequestMessageTypes, SupportedLanguages } from '~/types/websocket'
import { MESSAGE_TYPES } from '~/types/websocket'

export function createRequestMessage(
  id: string,
  type: RequestMessageTypes,
  options?: {
    code?: string
    language?: SupportedLanguages
  },
): RequestMessage {
  return {
    id,
    type,
    ...options,
  }
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
