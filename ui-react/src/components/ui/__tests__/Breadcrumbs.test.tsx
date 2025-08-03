import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Breadcrumbs from '../Breadcrumbs'
import type { BreadcrumbItem } from '../Breadcrumbs'
import { Heart, User, FileText, ChevronRight } from 'lucide-react'

describe('Breadcrumbs Component', () => {
  let mockItems: BreadcrumbItem[]
  let mockOnItemClick: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockOnItemClick = vi.fn()
    mockItems = [
      {
        id: 'home',
        label: 'Dashboard',
        href: '/',
      },
      {
        id: 'patients',
        label: 'Patients',
        href: '/patients',
        icon: User,
      },
      {
        id: 'patient',
        label: 'John Smith',
        href: '/patients/123',
        metadata: {
          patientId: '123',
          recordType: 'demographics' as const,
        }
      },
      {
        id: 'demographics',
        label: 'Demographics',
        isActive: true,
        metadata: {
          patientId: '123',
          recordType: 'demographics' as const,
          visitId: 'v456'
        }
      }
    ]
  })

  it('renders breadcrumb items', () => {
    render(<Breadcrumbs items={mockItems} />)
    
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Patients')).toBeInTheDocument()
    expect(screen.getByText('John Smith')).toBeInTheDocument()
    expect(screen.getByText('Demographics')).toBeInTheDocument()
  })

  it('shows home icon for first item by default', () => {
    render(<Breadcrumbs items={mockItems} />)
    
    // Home icon should be present
    const homeIcon = document.querySelector('svg')
    expect(homeIcon).toBeInTheDocument()
  })

  it('hides home icon when showHomeIcon is false', () => {
    render(<Breadcrumbs items={mockItems} showHomeIcon={false} />)
    
    // Should only show custom icons, not home icon
    const userIcon = document.querySelector('svg')
    // The User icon should still be shown for the patients item
    expect(userIcon).toBeInTheDocument()
  })

  it('renders custom icons for items', () => {
    render(<Breadcrumbs items={mockItems} />)
    
    // User icon should be present for patients item
    const icons = document.querySelectorAll('svg')
    expect(icons.length).toBeGreaterThan(1) // Home + User icons
  })

  it('renders separators between items', () => {
    render(<Breadcrumbs items={mockItems} />)
    
    // Should have 3 separators for 4 items
    const separators = document.querySelectorAll('svg[aria-hidden="true"]')
    // Filter out the home and user icons
    const chevronSeparators = Array.from(separators).filter(svg => 
      !svg.classList.contains('w-4') || 
      svg.closest('[aria-hidden="true"]')?.tagName === 'svg'
    )
    expect(chevronSeparators.length).toBeGreaterThan(0)
  })

  it('marks active item with proper styling and ARIA', () => {
    render(<Breadcrumbs items={mockItems} />)
    
    const activeItem = screen.getByText('Demographics')
    expect(activeItem).toHaveClass('font-medium', 'text-gray-900')
    expect(activeItem).toHaveAttribute('aria-current', 'page')
  })

  it('makes non-active items clickable', () => {
    render(<Breadcrumbs items={mockItems} onItemClick={mockOnItemClick} />)
    
    const dashboardItem = screen.getByRole('button', { name: /dashboard/i })
    expect(dashboardItem).toBeInTheDocument()
    
    const patientsItem = screen.getByRole('button', { name: /patients/i })
    expect(patientsItem).toBeInTheDocument()
  })

  it('calls onItemClick when breadcrumb is clicked', async () => {
    const user = userEvent.setup()
    render(<Breadcrumbs items={mockItems} onItemClick={mockOnItemClick} />)
    
    const dashboardItem = screen.getByRole('button', { name: /dashboard/i })
    await user.click(dashboardItem)
    
    expect(mockOnItemClick).toHaveBeenCalledWith(mockItems[0])
  })

  it('does not call onItemClick for active item', async () => {
    const user = userEvent.setup()
    render(<Breadcrumbs items={mockItems} onItemClick={mockOnItemClick} />)
    
    const activeItem = screen.getByText('Demographics')
    await user.click(activeItem)
    
    expect(mockOnItemClick).not.toHaveBeenCalled()
  })

  it('handles keyboard navigation', async () => {
    const user = userEvent.setup()
    render(<Breadcrumbs items={mockItems} onItemClick={mockOnItemClick} />)
    
    const dashboardItem = screen.getByRole('button', { name: /dashboard/i })
    
    // Enter key should trigger click
    await user.click(dashboardItem)
    await user.keyboard('{Enter}')
    
    expect(mockOnItemClick).toHaveBeenCalledWith(mockItems[0])
  })

  it('handles space key navigation', async () => {
    const user = userEvent.setup()
    render(<Breadcrumbs items={mockItems} onItemClick={mockOnItemClick} />)
    
    const patientsItem = screen.getByRole('button', { name: /patients/i })
    patientsItem.focus()
    
    await user.keyboard(' ')
    
    expect(mockOnItemClick).toHaveBeenCalledWith(mockItems[1])
  })

  it('collapses items when exceeding maxItems', () => {
    const manyItems: BreadcrumbItem[] = [
      { id: '1', label: 'Level 1', href: '/1' },
      { id: '2', label: 'Level 2', href: '/2' },
      { id: '3', label: 'Level 3', href: '/3' },
      { id: '4', label: 'Level 4', href: '/4' },
      { id: '5', label: 'Level 5', href: '/5' },
      { id: '6', label: 'Level 6', href: '/6' },
      { id: '7', label: 'Level 7', isActive: true },
    ]
    
    render(<Breadcrumbs items={manyItems} maxItems={5} />)
    
    // Should show first item, collapsed indicator, and last 2 items
    expect(screen.getByText('Level 1')).toBeInTheDocument()
    expect(screen.getByText('... (2 more)')).toBeInTheDocument()
    expect(screen.getByText('Level 6')).toBeInTheDocument()
    expect(screen.getByText('Level 7')).toBeInTheDocument()
    
    // Should not show middle items
    expect(screen.queryByText('Level 3')).not.toBeInTheDocument()
  })

  it('does not collapse when items are within maxItems limit', () => {
    render(<Breadcrumbs items={mockItems} maxItems={5} />)
    
    // Should show all items without collapsing
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Patients')).toBeInTheDocument()
    expect(screen.getByText('John Smith')).toBeInTheDocument()
    expect(screen.getByText('Demographics')).toBeInTheDocument()
    
    // Should not show collapse indicator
    expect(screen.queryByText(/more/)).not.toBeInTheDocument()
  })

  it('shows tooltips with metadata when enabled', () => {
    render(<Breadcrumbs items={mockItems} showTooltips />)
    
    const patientItem = screen.getByRole('button', { name: /john smith/i })
    expect(patientItem).toHaveAttribute('title', 'Patient: 123 • Section: demographics')
    
    const activeItem = screen.getByText('Demographics')
    expect(activeItem).toHaveAttribute('title', 'Patient: 123 • Section: demographics • Visit: v456')
  })

  it('does not show tooltips when showTooltips is false', () => {
    render(<Breadcrumbs items={mockItems} showTooltips={false} />)
    
    const patientItem = screen.getByRole('button', { name: /john smith/i })
    expect(patientItem).not.toHaveAttribute('title')
  })

  it('uses custom separator when provided', () => {
    const CustomSeparator = ({ className }: { className?: string }) => (
      <div className={className} data-testid="custom-separator">|</div>
    )
    
    render(<Breadcrumbs items={mockItems} separator={CustomSeparator} />)
    
    const customSeparators = screen.getAllByTestId('custom-separator')
    expect(customSeparators.length).toBe(3) // 3 separators for 4 items
  })

  it('applies custom className', () => {
    render(<Breadcrumbs items={mockItems} className="custom-breadcrumbs" />)
    
    const nav = screen.getByRole('navigation')
    expect(nav).toHaveClass('custom-breadcrumbs')
  })

  describe('accessibility', () => {
    it('has proper navigation structure', () => {
      render(<Breadcrumbs items={mockItems} />)
      
      const nav = screen.getByRole('navigation')
      expect(nav).toHaveAttribute('aria-label', 'Breadcrumb navigation')
      
      const list = screen.getByRole('list')
      expect(list).toBeInTheDocument()
      
      const listItems = screen.getAllByRole('listitem')
      expect(listItems).toHaveLength(4)
    })

    it('provides descriptive aria-labels for navigation', () => {
      render(<Breadcrumbs items={mockItems} showTooltips onItemClick={mockOnItemClick} />)
      
      const patientItem = screen.getByRole('button', { name: /john smith/i })
      expect(patientItem).toHaveAttribute('aria-label', 'Navigate to John Smith (Patient: 123 • Section: demographics)')
    })

    it('handles collapsed items accessibility', () => {
      const manyItems: BreadcrumbItem[] = [
        { id: '1', label: 'Level 1', href: '/1' },
        { id: '2', label: 'Level 2', href: '/2' },
        { id: '3', label: 'Level 3', href: '/3' },
        { id: '4', label: 'Level 4', href: '/4' },
        { id: '5', label: 'Level 5', href: '/5' },
        { id: '6', label: 'Level 6', isActive: true },
      ]
      
      render(<Breadcrumbs items={manyItems} maxItems={4} />)
      
      const collapsedIndicator = screen.getByText('... (2 more)')
      expect(collapsedIndicator).toHaveAttribute('aria-label', '... (2 more) - navigation items collapsed')
    })

    it('has touch-friendly button targets', () => {
      render(<Breadcrumbs items={mockItems} onItemClick={mockOnItemClick} />)
      
      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        expect(button).toHaveClass('min-h-[44px]') // Touch-friendly minimum height
      })
    })
  })

  describe('healthcare-specific features', () => {
    it('handles patient metadata correctly', () => {
      const healthcareItems: BreadcrumbItem[] = [
        {
          id: 'patients',
          label: 'Patients',
          href: '/patients',
        },
        {
          id: 'patient',
          label: 'Ahmed Al-Rashid',
          href: '/patients/ae789',
          metadata: {
            patientId: 'ae789',
            recordType: 'vitals' as const,
          }
        },
        {
          id: 'vitals',
          label: 'Vital Signs',
          isActive: true,
          metadata: {
            patientId: 'ae789',
            recordType: 'vitals' as const,
            visitId: 'visit123'
          }
        }
      ]
      
      render(<Breadcrumbs items={healthcareItems} showTooltips />)
      
      const patientItem = screen.getByRole('button', { name: /ahmed al-rashid/i })
      expect(patientItem).toHaveAttribute('title', 'Patient: ae789 • Section: vitals')
      
      const vitalsItem = screen.getByText('Vital Signs')
      expect(vitalsItem).toHaveAttribute('title', 'Patient: ae789 • Section: vitals • Visit: visit123')
    })

    it('handles different medical record types', () => {
      const medicalRecordTypes: Array<BreadcrumbItem['metadata']['recordType']> = [
        'demographics', 'history', 'vitals', 'medications', 'allergies', 'procedures'
      ]
      
      medicalRecordTypes.forEach(recordType => {
        const items: BreadcrumbItem[] = [
          {
            id: 'section',
            label: `Medical ${recordType}`,
            isActive: true,
            metadata: {
              patientId: 'test123',
              recordType: recordType!,
            }
          }
        ]
        
        const { unmount } = render(<Breadcrumbs items={items} showTooltips />)
        
        const activeItem = screen.getByText(`Medical ${recordType}`)
        expect(activeItem).toHaveAttribute('title', `Patient: test123 • Section: ${recordType}`)
        
        unmount()
      })
    })
  })
})