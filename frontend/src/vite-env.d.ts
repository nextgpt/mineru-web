/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_RAGFLOW_BASE_URL: string
  readonly VITE_RAGFLOW_API_KEY: string
  readonly VITE_DEEPSEEK_API_KEY: string
  readonly VITE_DEEPSEEK_BASE_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare module 'markdown-it-katex' {
    import MarkdownIt from 'markdown-it'
    const markdownItKatex: MarkdownIt.PluginSimple
    export default markdownItKatex
}
