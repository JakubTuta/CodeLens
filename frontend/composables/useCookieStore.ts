export interface CookieStoreOptions {
  default?: () => string
  maxAge?: number
  path?: string
  domain?: string
  secure?: boolean
  sameSite?: 'strict' | 'lax' | 'none'
}

export function useCookieStore() {
  const COOKIE_PREFIX = 'CodeLens-'

  const getCookie = (key: string, options?: CookieStoreOptions) => {
    const cookieKey = `${COOKIE_PREFIX}${key}`

    return useCookie(cookieKey, {
      default: options?.default || (() => ''),
      maxAge: options?.maxAge
        ? options.maxAge * 24 * 60 * 60
        : undefined,
      path: options?.path,
      domain: options?.domain,
      secure: options?.secure,
      sameSite: options?.sameSite,
    })
  }

  const getBooleanCookie = (key: string, defaultValue: boolean = true) => {
    const cookie = getCookie(key, {
      default: () => String(defaultValue),
    })

    const value = cookie.value
    if (typeof value === 'boolean') {
      return value
    }
    if (typeof value === 'string') {
      return value === 'true'
    }

    return defaultValue
  }

  const setBooleanCookie = (key: string, value: boolean, options?: CookieStoreOptions) => {
    const cookie = getCookie(key, options)

    cookie.value = String(value)

    return value
  }

  const setCookie = (key: string, value: string, options?: CookieStoreOptions) => {
    const cookie = getCookie(key, options)
    cookie.value = value

    return cookie
  }

  const removeCookie = (key: string) => {
    const cookie = getCookie(key)
    cookie.value = ''

    return cookie
  }

  const hasCookie = (key: string) => {
    const cookie = getCookie(key)

    return !!cookie.value.trim()
  }

  const getApiKey = () => getCookie('aiApiKey')
  const getAiModel = () => getCookie('aiModel')
  const getCode = () => getCookie('code')
  const getLanguage = () => getCookie('language', { default: () => 'python' })
  const getGenerateTests = () => getBooleanCookie('generateTests', true)
  const getGenerateDocumentation = () => getBooleanCookie('generateDocumentation', true)
  const getGenerateImprovements = () => getBooleanCookie('generateImprovements', true)

  const setApiKey = (value: string) => setCookie('aiApiKey', value)
  const setAiModel = (value: string) => setCookie('aiModel', value)
  const setCode = (value: string) => setCookie('code', value)
  const setLanguage = (value: string) => setCookie('language', value)
  const setGenerateTests = (value: boolean) => setBooleanCookie('generateTests', value)
  const setGenerateDocumentation = (value: boolean) => setBooleanCookie('generateDocumentation', value)
  const setGenerateImprovements = (value: boolean) => setBooleanCookie('generateImprovements', value)

  const removeApiKey = () => removeCookie('aiApiKey')
  const removeAiModel = () => removeCookie('aiModel')
  const removeCode = () => removeCookie('code')
  const removeLanguage = () => removeCookie('language')
  const removeGenerateTests = () => removeCookie('generateTests')
  const removeGenerateDocumentation = () => removeCookie('generateDocumentation')
  const removeGenerateImprovements = () => removeCookie('generateImprovements')

  const hasApiKey = () => hasCookie('aiApiKey')
  const hasAiModel = () => hasCookie('aiModel')
  const hasCode = () => hasCookie('code')
  const hasLanguage = () => hasCookie('language')
  const hasGenerateTests = () => hasCookie('generateTests')
  const hasGenerateDocumentation = () => hasCookie('generateDocumentation')
  const hasGenerateImprovements = () => hasCookie('generateImprovements')

  return {
    getCookie,
    getBooleanCookie,
    setCookie,
    setBooleanCookie,
    removeCookie,
    hasCookie,

    getApiKey,
    setApiKey,
    removeApiKey,
    hasApiKey,

    getAiModel,
    setAiModel,
    removeAiModel,
    hasAiModel,

    getCode,
    setCode,
    removeCode,
    hasCode,

    getLanguage,
    setLanguage,
    removeLanguage,
    hasLanguage,

    getGenerateTests,
    setGenerateTests,
    removeGenerateTests,
    hasGenerateTests,

    getGenerateDocumentation,
    setGenerateDocumentation,
    removeGenerateDocumentation,
    hasGenerateDocumentation,

    getGenerateImprovements,
    setGenerateImprovements,
    removeGenerateImprovements,
    hasGenerateImprovements,
  }
}
