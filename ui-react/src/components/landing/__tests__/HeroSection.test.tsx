import { describe, it, expect } from 'vitest'
import { render, screen } from '@/test/utils'
import userEvent from '@testing-library/user-event'
import HeroSection from '../HeroSection'

describe('HeroSection Component', () => {
  it('renders hero section with main heading', () => {
    render(<HeroSection />)

    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
    expect(screen.getByText(/Turn Pre-Authorization into/)).toBeInTheDocument()
    expect(screen.getByText(/Prevention/)).toBeInTheDocument()
  })

  it('displays the clinical intelligence platform badge', () => {
    render(<HeroSection />)

    expect(screen.getByText('Clinical Intelligence Platform')).toBeInTheDocument()
  })

  it('shows the main value proposition', () => {
    render(<HeroSection />)

    expect(screen.getByText('Clinical Intelligence for UAE Payers')).toBeInTheDocument()
    expect(screen.getByText(/Nazmito enriches every authorization/)).toBeInTheDocument()
  })

  it('displays call-to-action buttons', () => {
    render(<HeroSection />)

    expect(screen.getByRole('button', { name: /try dashboard/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /book a demo/i })).toBeInTheDocument()
  })

  it('renders dashboard link with correct navigation', () => {
    render(<HeroSection />)

    const dashboardLink = screen.getByRole('link')
    expect(dashboardLink).toHaveAttribute('href', '/dashboard')
  })

  it('displays feature cards with benefits', () => {
    render(<HeroSection />)

    expect(screen.getByText('Smart Processing')).toBeInTheDocument()
    expect(screen.getByText('90%+ Automated')).toBeInTheDocument()

    expect(screen.getByText('Lightning Fast')).toBeInTheDocument()
    expect(screen.getByText('Minutes not Days')).toBeInTheDocument()

    expect(screen.getByText('AI Intelligence')).toBeInTheDocument()
    expect(screen.getByText('Predictive Care')).toBeInTheDocument()
  })

  it('handles button interactions', async () => {
    const user = userEvent.setup()
    render(<HeroSection />)

    const demoButton = screen.getByRole('button', { name: /book a demo/i })
    await user.click(demoButton)

    // Button should be clickable (no error thrown)
    expect(demoButton).toBeInTheDocument()
  })

  it('has proper semantic structure', () => {
    render(<HeroSection />)

    // Should be a section element
    const section = document.querySelector('section')
    expect(section).toBeInTheDocument()

    // Should have proper heading hierarchy
    const h1 = screen.getByRole('heading', { level: 1 })
    expect(h1).toBeInTheDocument()
  })

  it('applies correct CSS classes for styling', () => {
    render(<HeroSection />)

    const section = document.querySelector('section')
    expect(section).toHaveClass('relative', 'py-20', 'lg:py-32')

    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toHaveClass('text-5xl', 'lg:text-6xl', 'font-bold')
  })

  it('displays gradient text for "Prevention"', () => {
    render(<HeroSection />)

    const preventionSpan = screen.getByText('Prevention')
    expect(preventionSpan).toHaveClass('bg-gradient-to-r', 'from-primary-500', 'to-primary-600', 'bg-clip-text', 'text-transparent')
  })

  it('shows animated elements with proper classes', () => {
    render(<HeroSection />)

    // Check for animation classes
    const badge = screen.getByText('Clinical Intelligence Platform').closest('div')
    expect(badge).toHaveClass('animate-fade-in-up')

    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toHaveClass('animate-fade-in-up', 'delay-200')
  })

  it('renders emoji icons in feature cards', () => {
    render(<HeroSection />)

    expect(screen.getByText('🏥')).toBeInTheDocument()
    expect(screen.getByText('⚡')).toBeInTheDocument()
    expect(screen.getByText('💡')).toBeInTheDocument()
  })

  describe('responsive behavior', () => {
    it('adapts layout for different screen sizes', () => {
      render(<HeroSection />)

      const gridContainer = document.querySelector('.grid.grid-cols-1.lg\\:grid-cols-2')
      expect(gridContainer).toBeInTheDocument()

      const textContainer = document.querySelector('.text-center.lg\\:text-left')
      expect(textContainer).toBeInTheDocument()
    })

    it('stacks buttons vertically on mobile', () => {
      render(<HeroSection />)

      const buttonContainer = document.querySelector('.flex.flex-col.sm\\:flex-row')
      expect(buttonContainer).toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('provides proper heading structure', () => {
      render(<HeroSection />)

      const headings = screen.getAllByRole('heading')
      expect(headings).toHaveLength(1)
      expect(headings[0]).toHaveProperty('tagName', 'H1')
    })

    it('has descriptive link text', () => {
      render(<HeroSection />)

      const dashboardLink = screen.getByRole('link')
      expect(dashboardLink).toHaveAccessibleName(/try dashboard/i)
    })

    it('uses semantic HTML elements', () => {
      render(<HeroSection />)

      expect(document.querySelector('section')).toBeInTheDocument()
      expect(screen.getByRole('heading')).toBeInTheDocument()
      expect(screen.getByRole('link')).toBeInTheDocument()
    })
  })

  describe('visual elements', () => {
    it('renders gradient orbs for visual appeal', () => {
      render(<HeroSection />)

      const orbs = document.querySelectorAll('.rounded-full.opacity-20.blur-3xl')
      expect(orbs).toHaveLength(3)
    })

    it('applies hover effects to feature cards', () => {
      render(<HeroSection />)

      const featureCards = document.querySelectorAll('.hover\\:rotate-0')
      expect(featureCards.length).toBeGreaterThan(0)
    })

    it('includes ArrowRight icon in CTA button', () => {
      render(<HeroSection />)

      // ArrowRight should be rendered as SVG
      const svg = document.querySelector('svg')
      expect(svg).toBeInTheDocument()
    })
  })
})
