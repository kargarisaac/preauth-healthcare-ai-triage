import { chromium, FullConfig } from '@playwright/test'

async function globalSetup(config: FullConfig) {
  const { baseURL } = config.projects[0].use

  // Launch browser for pre-test setup
  const browser = await chromium.launch()
  const page = await browser.newPage()

  try {
    // Wait for the dev server to be ready
    if (baseURL) {
      await page.goto(baseURL)
      await page.waitForLoadState('networkidle')
    }
  } catch (error) {
    console.error('Global setup failed:', error)
  } finally {
    await browser.close()
  }
}

export default globalSetup
