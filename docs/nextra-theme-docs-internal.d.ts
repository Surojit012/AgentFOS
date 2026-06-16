declare module '../node_modules/nextra-theme-docs/dist/schemas.js' {
  export const LayoutPropsSchema: {
    parse(input: unknown): any
  }
}

declare module '../node_modules/nextra-theme-docs/dist/stores/index.js' {
  import type { ComponentType, ReactNode } from 'react'

  export const ConfigProvider: ComponentType<{
    children: ReactNode
    footer?: ReactNode
    navbar?: ReactNode
    pageMap: any[]
  }>

  export const ThemeConfigProvider: ComponentType<{
    children: ReactNode
    value: Record<string, unknown>
  }>
}

declare module '../node_modules/nextra-theme-docs/dist/components/sidebar.js' {
  import type { ComponentType } from 'react'

  export const MobileNav: ComponentType
}
