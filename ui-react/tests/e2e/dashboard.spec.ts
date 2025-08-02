import { test, expect } from '@playwright/test'

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard')
  })

  test('should display dashboard layout', async ({ page }) => {
    // Check for main dashboard elements
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible()
    await expect(page.getByText(/file processing/i)).toBeVisible()
    await expect(page.getByText(/analytics/i)).toBeVisible()
  })

  test('should display file upload area', async ({ page }) => {
    // Check for upload zone
    await expect(page.getByText(/drop files here/i)).toBeVisible()
    await expect(page.getByText(/XML or CSV files/i)).toBeVisible()

    // Check for file input
    const fileInput = page.locator('input[type="file"]')
    await expect(fileInput).toBeAttached()
    await expect(fileInput).toHaveAttribute('accept', '.xml,.csv')
  })

  test('should handle file upload flow', async ({ page }) => {
    // Create a test file
    const testFile = Buffer.from(`<?xml version="1.0" encoding="UTF-8"?>
      <eClaim>
        <Header>
          <AuthorizationId>TEST-001</AuthorizationId>
        </Header>
      </eClaim>`)

    // Upload file
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles({
      name: 'test-claim.xml',
      mimeType: 'text/xml',
      buffer: testFile,
    })

    // Check that file is selected
    await expect(page.getByText('test-claim.xml')).toBeVisible()

    // Check for process button
    const processBtn = page.getByRole('button', { name: /process/i })
    await expect(processBtn).toBeVisible()
    await expect(processBtn).toBeEnabled()
  })

  test('should display processing progress', async ({ page }) => {
    // Mock a file upload first
    const testFile = Buffer.from('<test>data</test>')
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles({
      name: 'test.xml',
      mimeType: 'text/xml',
      buffer: testFile,
    })

    // Click process button
    await page.getByRole('button', { name: /process/i }).click()

    // Should show processing state
    await expect(page.getByText(/processing/i)).toBeVisible()

    // Should show progress bar (wait for it to appear)
    await expect(page.locator('[role="progressbar"]')).toBeVisible({ timeout: 10000 })
  })

  test('should display metrics and analytics', async ({ page }) => {
    // Check for metrics cards
    await expect(page.getByText(/total files/i)).toBeVisible()
    await expect(page.getByText(/success rate/i)).toBeVisible()
    await expect(page.getByText(/processing time/i)).toBeVisible()

    // Check for charts
    await expect(page.locator('[data-testid="analytics-chart"]')).toBeVisible()
  })

  test('should display request history', async ({ page }) => {
    // Navigate to request history
    await page.getByRole('link', { name: /request history/i }).click()

    // Check for table headers
    await expect(page.getByText(/request number/i)).toBeVisible()
    await expect(page.getByText(/member name/i)).toBeVisible()
    await expect(page.getByText(/status/i)).toBeVisible()
    await expect(page.getByText(/amount/i)).toBeVisible()

    // Check for search functionality
    await expect(page.getByPlaceholder(/search requests/i)).toBeVisible()
  })

  test('should handle search and filtering', async ({ page }) => {
    // Navigate to request history
    await page.getByRole('link', { name: /request history/i }).click()

    // Perform search
    const searchInput = page.getByPlaceholder(/search requests/i)
    await searchInput.fill('Ahmed')

    // Should update results
    await page.waitForTimeout(500) // Wait for debounce

    // Check filter options
    const statusFilter = page.getByRole('combobox', { name: /status/i })
    if (await statusFilter.isVisible()) {
      await statusFilter.click()
      await expect(page.getByText(/approved/i)).toBeVisible()
      await expect(page.getByText(/pending/i)).toBeVisible()
    }
  })

  test('should display member search', async ({ page }) => {
    // Check for member search functionality
    const memberSearch = page.getByPlaceholder(/search members/i)
    if (await memberSearch.isVisible()) {
      await memberSearch.fill('784-1990')

      // Should show search results
      await expect(page.locator('[data-testid="member-result"]')).toBeVisible({ timeout: 5000 })
    }
  })

  test('should handle bulk operations', async ({ page }) => {
    // Navigate to request history
    await page.getByRole('link', { name: /request history/i }).click()

    // Select multiple items
    const checkboxes = page.locator('input[type="checkbox"]')
    const firstCheckbox = checkboxes.first()
    if (await firstCheckbox.isVisible()) {
      await firstCheckbox.check()

      // Should show bulk actions
      await expect(page.getByText(/bulk actions/i)).toBeVisible()
      await expect(page.getByRole('button', { name: /approve selected/i })).toBeVisible()
    }
  })

  test('should display results modal', async ({ page }) => {
    // Mock successful file processing
    const testFile = Buffer.from('<test>data</test>')
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles({
      name: 'test.xml',
      mimeType: 'text/xml',
      buffer: testFile,
    })

    // Process file
    await page.getByRole('button', { name: /process/i }).click()

    // Wait for processing to complete and results modal
    await expect(page.getByText(/processing complete/i)).toBeVisible({ timeout: 15000 })

    // Should show FHIR bundle viewer
    const resultsModal = page.locator('[role="dialog"]')
    if (await resultsModal.isVisible()) {
      await expect(page.getByText(/FHIR bundle/i)).toBeVisible()
      await expect(page.getByText(/raw data/i)).toBeVisible()
    }
  })

  test('should be responsive on tablet and mobile', async ({ page }) => {
    // Test tablet view
    await page.setViewportSize({ width: 768, height: 1024 })
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible()

    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 })

    // Check for mobile navigation
    const mobileMenu = page.getByRole('button', { name: /menu/i })
    if (await mobileMenu.isVisible()) {
      await mobileMenu.click()
      await expect(page.getByRole('navigation')).toBeVisible()
    }
  })

  test('should handle keyboard navigation', async ({ page }) => {
    // Test tab navigation
    await page.keyboard.press('Tab')

    // Should focus on first interactive element
    const focusedElement = page.locator(':focus')
    await expect(focusedElement).toBeVisible()

    // Continue tabbing through interface
    await page.keyboard.press('Tab')
    await page.keyboard.press('Tab')

    // Ensure multiple elements can receive focus
    await expect(page.locator(':focus')).toBeVisible()
  })

  test('should display error states appropriately', async ({ page }) => {
    // Try to process without file
    const processBtn = page.getByRole('button', { name: /process/i })

    // Button should be disabled when no file selected
    await expect(processBtn).toBeDisabled()

    // Test with invalid file
    const invalidFile = Buffer.from('invalid file content')
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles({
      name: 'invalid.txt',
      mimeType: 'text/plain',
      buffer: invalidFile,
    })

    // Should show error or validation message
    if (await processBtn.isEnabled()) {
      await processBtn.click()

      // Should show error message
      await expect(page.getByText(/error/i)).toBeVisible({ timeout: 10000 })
    }
  })
})
