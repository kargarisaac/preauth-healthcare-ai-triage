import { test, expect } from '@playwright/test'

test.describe('Landing Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('should display main navigation', async ({ page }) => {
    // Check for main navigation elements
    await expect(page.getByRole('navigation')).toBeVisible()
    
    // Check for key navigation links
    await expect(page.getByRole('link', { name: /home/i })).toBeVisible()
    await expect(page.getByRole('link', { name: /features/i })).toBeVisible()
    await expect(page.getByRole('link', { name: /pricing/i })).toBeVisible()
    await expect(page.getByRole('link', { name: /contact/i })).toBeVisible()
  })

  test('should display hero section', async ({ page }) => {
    // Check for hero section elements
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
    await expect(page.getByText(/AI-powered pre-authorization/i)).toBeVisible()
    
    // Check for CTA buttons
    const ctaButtons = page.getByRole('button')
    await expect(ctaButtons.first()).toBeVisible()
  })

  test('should navigate to dashboard on CTA click', async ({ page }) => {
    // Find and click the main CTA button
    const ctaButton = page.getByRole('button', { name: /get started/i }).first()
    await ctaButton.click()
    
    // Should navigate to dashboard
    await expect(page).toHaveURL(/\/dashboard/)
  })

  test('should display problem section', async ({ page }) => {
    await expect(page.getByText(/current challenges/i)).toBeVisible()
    await expect(page.getByText(/manual processing/i)).toBeVisible()
    await expect(page.getByText(/slow turnaround/i)).toBeVisible()
  })

  test('should display solution features', async ({ page }) => {
    await expect(page.getByText(/automated processing/i)).toBeVisible()
    await expect(page.getByText(/FHIR compliance/i)).toBeVisible()
    await expect(page.getByText(/real-time analytics/i)).toBeVisible()
  })

  test('should display UAE-specific content', async ({ page }) => {
    await expect(page.getByText(/UAE healthcare/i)).toBeVisible()
    await expect(page.getByText(/eClaimLink/i)).toBeVisible()
    await expect(page.getByText(/Shafafiya/i)).toBeVisible()
    await expect(page.getByText(/Dubai Health Authority/i)).toBeVisible()
  })

  test('should display pricing section', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /pricing/i })).toBeVisible()
    
    // Check for pricing tiers
    await expect(page.getByText(/starter/i)).toBeVisible()
    await expect(page.getByText(/professional/i)).toBeVisible()
    await expect(page.getByText(/enterprise/i)).toBeVisible()
  })

  test('should display FAQ section', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /frequently asked questions/i })).toBeVisible()
    
    // Check for expandable FAQ items
    const faqItems = page.locator('[data-testid="faq-item"]')
    await expect(faqItems.first()).toBeVisible()
  })

  test('should display contact section', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /contact/i })).toBeVisible()
    await expect(page.getByRole('textbox', { name: /email/i })).toBeVisible()
    await expect(page.getByRole('textbox', { name: /message/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /send message/i })).toBeVisible()
  })

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })
    
    // Check that mobile navigation works
    const mobileMenuToggle = page.getByRole('button', { name: /menu/i })
    if (await mobileMenuToggle.isVisible()) {
      await mobileMenuToggle.click()
      await expect(page.getByRole('navigation')).toBeVisible()
    }
  })

  test('should have proper SEO elements', async ({ page }) => {
    // Check for essential SEO elements
    await expect(page).toHaveTitle(/Nazmito/i)
    
    const metaDescription = page.locator('meta[name="description"]')
    await expect(metaDescription).toHaveAttribute('content', /.+/)
    
    // Check for structured data
    const structuredData = page.locator('script[type="application/ld+json"]')
    await expect(structuredData).toBeAttached()
  })

  test('should handle smooth scrolling', async ({ page }) => {
    // Click on a navigation link that should scroll to section
    await page.getByRole('link', { name: /features/i }).click()
    
    // Wait for scroll animation
    await page.waitForTimeout(1000)
    
    // Check that we scrolled to the features section
    const featuresSection = page.locator('[data-testid="features-section"]')
    await expect(featuresSection).toBeInViewport()
  })
})