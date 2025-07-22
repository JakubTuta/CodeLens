// TypeScript mappings for Python WebSocket models

export type AvailableAiModels = 'gemini' | 'sonnet'

export type ResponseMessageTypes
  = | 'error'
    | 'return_unit_tests'
    | 'return_memory_tests'
    | 'return_performance_tests'
    | 'return_docs'
    | 'return_improvements'
    | 'ai_test_result'
    | 'verify_code_result'

export type RequestMessageTypes = 'send_code' | 'test_ai' | 'verify_code'

export type SupportedLanguages = 'python'

export type TestType = 'unit' | 'memory' | 'performance'

export interface RequestMessage {
  id: string
  type: RequestMessageTypes
  code?: string
  language?: SupportedLanguages
}

export interface Test {
  type: TestType
  name: string
  code: string
}

export interface ResponseMessage {
  id: string
  type: ResponseMessageTypes

  // Error message or general message
  error_message?: string

  // Tests
  unit_tests?: Test[]
  memory_tests?: Test[]
  performance_tests?: Test[]

  // Documentation
  docs?: string

  // Improvements
  improvements?: string[]

  // AI test / code verification result
  is_ok?: boolean

  // Detected AI model name
  detected_model?: AvailableAiModels
}

export const MESSAGE_TYPES = {
  request: {
    SEND_CODE: 'send_code' as const,
    TEST_AI: 'test_ai' as const,
    VERIFY_CODE: 'verify_code' as const,
  },
  response: {
    ERROR: 'error' as const,
    RETURN_UNIT_TESTS: 'return_unit_tests' as const,
    RETURN_MEMORY_TESTS: 'return_memory_tests' as const,
    RETURN_PERFORMANCE_TESTS: 'return_performance_tests' as const,
    RETURN_DOCS: 'return_docs' as const,
    RETURN_IMPROVEMENTS: 'return_improvements' as const,
    AI_TEST_RESULT: 'ai_test_result' as const,
    VERIFY_CODE_RESULT: 'verify_code_result' as const,
  },
} as const
