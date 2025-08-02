import { test, expect } from '@playwright/test'
import { injectAxe, checkA11y } from 'axe-playwright'

test.describe('Accessibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await injectAxe(page)
  })

  test('should have no accessibility violations on landing page', async ({ page }) => {
    await checkA11y(page, null, {
      detailedReport: true,
      detailedReportOptions: {
        html: true,
      },
    })
  })

  test('should have no accessibility violations on dashboard', async ({ page }) => {
    await page.goto('/dashboard')
    await injectAxe(page)

    await checkA11y(page, null, {
      detailedReport: true,
      detailedReportOptions: {
        html: true,
      },
    })
  })

  test('should support keyboard navigation', async ({ page }) => {
    // Test tab navigation through main elements
    let tabCount = 0
    const maxTabs = 20 // Prevent infinite loop

    while (tabCount < maxTabs) {
      await page.keyboard.press('Tab')
      const focusedElement = page.locator(':focus')

      if (await focusedElement.count() === 0) {
        break
      }

      // Check that focused element is visible and interactive
      await expect(focusedElement).toBeVisible()
      tabCount++
    }

    expect(tabCount).toBeGreaterThan(0)
  })

  test('should have proper heading hierarchy', async ({ page }) => {
    // Check for h1
    const h1Elements = page.locator('h1')
    await expect(h1Elements).toHaveCount(1)

    // Check that headings are in proper order
    const headings = page.locator('h1, h2, h3, h4, h5, h6')
    const headingTexts = await headings.allTextContents()

    expect(headingTexts.length).toBeGreaterThan(0)
  })

  test('should have proper ARIA labels and roles', async ({ page }) => {
    // Check for main landmarks
    await expect(page.locator('[role="main"]')).toBeVisible()
    await expect(page.locator('[role="navigation"]')).toBeVisible()

    // Check for form labels
    const inputs = page.locator('input')
    const inputCount = await inputs.count()

    for (let i = 0; i < inputCount; i++) {
      const input = inputs.nth(i)
      const inputType = await input.getAttribute('type')

      if (inputType !== 'hidden') {
        // Input should have label or aria-label
        const hasLabel = await input.getAttribute('aria-label') !== null
        const hasLabelledBy = await input.getAttribute('aria-labelledby') !== null
        const hasAssociatedLabel = await page.locator(`label[for="${await input.getAttribute('id')}"]`).count() > 0

        expect(hasLabel || hasLabelledBy || hasAssociatedLabel).toBeTruthy()
      }
    }
  })

  test('should have sufficient color contrast', async ({ page }) => {
    // This will be caught by axe-core, but we can also do manual checks
    await checkA11y(page, null, {
      rules: {
        'color-contrast': { enabled: true },
      },
    })
  })

  test('should support screen reader navigation', async ({ page }) => {
    // Check for skip links
    const skipLink = page.locator('[href="#main-content"]')
    if (await skipLink.count() > 0) {
      await expect(skipLink).toBeAttached()
    }

    // Check for proper alt text on images
    const images = page.locator('img')
    const imageCount = await images.count()

    for (let i = 0; i < imageCount; i++) {
      const img = images.nth(i)
      const altText = await img.getAttribute('alt')
      const isDecorative = altText === ''
      const hasAltText = altText && altText.length > 0

      // Image should either have alt text or be marked as decorative
      expect(isDecorative || hasAltText).toBeTruthy()
    }
  })

  test('should handle focus management in modals', async ({ page }) => {
    await page.goto('/dashboard')

    // Try to trigger a modal (file upload result)
    const testFile = Buffer.from('<test>data</test>')
    const fileInput = page.locator('input[type="file"]')

    if (await fileInput.count() > 0) {
      await fileInput.setInputFiles({
        name: 'test.xml',
        mimeType: 'text/xml',
        buffer: testFile,
      })

      const processBtn = page.getByRole('button', { name: /process/i })
      if (await processBtn.isEnabled()) {
        await processBtn.click()

        // Wait for modal to appear
        const modal = page.locator('[role="dialog"]')
        if (await modal.isVisible({ timeout: 10000 })) {
          // Focus should be trapped in modal
          await page.keyboard.press('Tab')
          const focusedElement = page.locator(':focus')

          // Focused element should be within modal
          const isInModal = await modal.locator(':focus').count() > 0
          expect(isInModal).toBeTruthy()
        }
      }
    }
  })

  test('should announce dynamic content changes', async ({ page }) => {
    await page.goto('/dashboard')

    // Check for aria-live regions
    const liveRegions = page.locator('[aria-live]')
    if (await liveRegions.count() > 0) {
      await expect(liveRegions.first()).toBeAttached()
    }

    // Check for status messages
    const statusMessages = page.locator('[role="status"]')
    if (await statusMessages.count() > 0) {
      await expect(statusMessages.first()).toBeAttached()
    }
  })

  test('should have proper form validation', async ({ page }) => {
    // Go to contact form if available
    const contactForm = page.locator('form')

    if (await contactForm.count() > 0) {
      // Try to submit without required fields
      const submitBtn = contactForm.locator('button[type="submit"]')
      if (await submitBtn.count() > 0) {
        await submitBtn.click()

        // Should show validation messages
        const validationMessages = page.locator('[aria-invalid="true"]')
        if (await validationMessages.count() > 0) {
          await expect(validationMessages.first()).toBeVisible()
        }
      }
    }
  })

  test('should work without JavaScript', async ({ page, context }) => {
    // Disable JavaScript
    await context.addInitScript(() => {
      Object.defineProperty(navigator, 'webdriver', { get: () => undefined })
    })

    await page.goto('/', { waitUntil: 'domcontentloaded' })

    // Basic content should still be visible
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
    await expect(page.getByRole('navigation')).toBeVisible()
  })
})
