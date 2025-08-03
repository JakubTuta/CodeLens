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
    | 'test_result_update'

export type RequestMessageTypes = 'generate_tests' | 'generate_docs' | 'generate_improvements' | 'test_ai' | 'verify_code'

export type SupportedLanguages = 'python'

export type TestType = 'unit' | 'memory' | 'performance'

export type TestStatus = 'pending' | 'running' | 'success' | 'failed'

export interface RequestMessage {
  id: string
  type: RequestMessageTypes
  code?: string
  language?: SupportedLanguages
  ai_model?: AvailableAiModels
  ai_api_key?: string
  generate_tests?: boolean
  generate_docs?: boolean
  generate_improvements?: boolean
}

export interface Test {
  id?: string
  type: TestType
  name: string
  title: string
  code: string
  status?: TestStatus
  execution_success?: boolean
  execution_output?: string
  execution_error?: string
  execution_time?: number
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

  // Individual test result update
  test_result?: Test
}

export const MESSAGE_TYPES = {
  request: {
    GENERATE_TESTS: 'generate_tests' as const,
    GENERATE_DOCS: 'generate_docs' as const,
    GENERATE_IMPROVEMENTS: 'generate_improvements' as const,
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
    TEST_RESULT_UPDATE: 'test_result_update' as const,
  },
} as const
