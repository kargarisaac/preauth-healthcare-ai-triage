import { FullConfig } from '@playwright/test'

async function globalTeardown(config: FullConfig) {
  // Perform any global cleanup here
  console.log('E2E tests completed')
}

export default globalTeardown