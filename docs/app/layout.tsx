import { Footer, Navbar } from 'nextra-theme-docs'
import { SkipNavLink } from 'nextra/components'
import { getPageMap } from 'nextra/page-map'
import { ThemeProvider } from 'next-themes'
// @ts-expect-error Internal Nextra module used to preserve docs-theme behavior in App Router.
import { LayoutPropsSchema } from '../node_modules/nextra-theme-docs/dist/schemas.js'
// @ts-expect-error Internal Nextra modules used to preserve docs-theme behavior in App Router.
import { ConfigProvider, ThemeConfigProvider } from '../node_modules/nextra-theme-docs/dist/stores/index.js'
// @ts-expect-error Internal Nextra module used to preserve docs-theme behavior in App Router.
import { MobileNav } from '../node_modules/nextra-theme-docs/dist/components/sidebar.js'
import 'nextra-theme-docs/style.css'

export const metadata = {
  title: {
    default: 'AgentFOS',
    template: '%s | AgentFOS'
  },
  description: 'Financial decision infrastructure for autonomous agents'
}

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const pageMap = await getPageMap()
  const navbar = (
    <Navbar
      logo={<strong>AgentFOS</strong>}
      projectLink="https://github.com/Surojit012/AgentFOS"
    />
  )
  const footer = (
    <Footer>AgentFOS: financial decision infrastructure for autonomous agents.</Footer>
  )
  const parsed = LayoutPropsSchema.parse({
    children,
    navbar,
    footer,
    pageMap,
    docsRepositoryBase: 'https://github.com/Surojit012/AgentFOS/tree/main/docs',
    sidebar: { defaultMenuCollapseLevel: 1 },
    editLink: null,
    feedback: { content: null }
  })
  const {
    banner,
    footer: parsedFooter,
    navbar: parsedNavbar,
    nextThemes,
    pageMap: parsedPageMap,
    children: parsedChildren,
    ...themeConfig
  } = parsed

  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeConfigProvider value={themeConfig}>
          <ThemeProvider {...nextThemes}>
            <SkipNavLink />
            {banner}
            <ConfigProvider pageMap={parsedPageMap} navbar={parsedNavbar} footer={parsedFooter}>
              <MobileNav />
              {parsedChildren}
            </ConfigProvider>
          </ThemeProvider>
        </ThemeConfigProvider>
      </body>
    </html>
  )
}
