declare module 'prismjs' {
  interface Grammar {
    [key: string]: any
  }

  interface Prism {
    languages: { [key: string]: Grammar }
    highlight: (text: string, grammar: Grammar, language: string) => string
    highlightElement: (element: Element) => void
  }

  const prism: Prism
  export default prism
}
