import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@/test/utils'
import userEvent from '@testing-library/user-event'
import Modal from '../Modal'

describe('Modal Component', () => {
  let mockOnClose: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockOnClose = vi.fn()
    // Create a div with id 'root' for portal rendering
    const portalRoot = document.createElement('div')
    portalRoot.setAttribute('id', 'root')
    document.body.appendChild(portalRoot)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    vi.clearAllMocks()
  })

  it('does not render when isOpen is false', () => {
    render(
      <Modal isOpen={false} onClose={mockOnClose}>
        <div>Modal Content</div>
      </Modal>
    )
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('renders when isOpen is true', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose}>
        <div>Modal Content</div>
      </Modal>
    )
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText('Modal Content')).toBeInTheDocument()
  })

  it('renders with title', () => {
    render(
      <Modal isOpen={true} title="Test Modal" onClose={mockOnClose}>
        <div>Modal Content</div>
      </Modal>
    )
    expect(screen.getByText('Test Modal')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Test Modal' })).toBeInTheDocument()
  })

  it('renders close button by default', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose}>
        <div>Modal Content</div>
      </Modal>
    )
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('hides close button when showCloseButton is false', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose} showCloseButton={false}>
        <div>Modal Content</div>
      </Modal>
    )
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', async () => {
    const user = userEvent.setup()
    render(
      <Modal isOpen={true} onClose={mockOnClose}>
        <div>Modal Content</div>
      </Modal>
    )
    
    await user.click(screen.getByRole('button'))
    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when Escape key is pressed', async () => {
    const user = userEvent.setup()
    render(
      <Modal isOpen={true} onClose={mockOnClose}>
        <div>Modal Content</div>
      </Modal>
    )
    
    await user.keyboard('{Escape}')
    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when overlay is clicked by default', async () => {
    const user = userEvent.setup()
    render(
      <Modal isOpen={true} onClose={mockOnClose}>
        <div>Modal Content</div>
      </Modal>
    )
    
    const overlay = screen.getByRole('dialog')
    await user.click(overlay)
    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('does not call onClose when overlay is clicked if closeOnOverlayClick is false', async () => {
    const user = userEvent.setup()
    render(
      <Modal isOpen={true} onClose={mockOnClose} closeOnOverlayClick={false}>
        <div>Modal Content</div>
      </Modal>
    )
    
    const overlay = screen.getByRole('dialog')
    await user.click(overlay)
    expect(mockOnClose).not.toHaveBeenCalled()
  })

  it('does not call onClose when modal content is clicked', async () => {
    const user = userEvent.setup()
    render(
      <Modal isOpen={true} onClose={mockOnClose}>
        <div>Modal Content</div>
      </Modal>
    )
    
    await user.click(screen.getByText('Modal Content'))
    expect(mockOnClose).not.toHaveBeenCalled()
  })

  it('applies correct size classes', () => {
    const { rerender } = render(
      <Modal isOpen={true} onClose={mockOnClose} size="lg">
        <div>Modal Content</div>
      </Modal>
    )
    
    let modalContent = document.querySelector('.modal-content')
    expect(modalContent).toHaveClass('modal-content-lg')

    rerender(
      <Modal isOpen={true} onClose={mockOnClose} size="xl">
        <div>Modal Content</div>
      </Modal>
    )
    
    modalContent = document.querySelector('.modal-content')
    expect(modalContent).toHaveClass('modal-content-xl')
  })

  it('sets body overflow to hidden when open', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose}>
        <div>Modal Content</div>
      </Modal>
    )
    expect(document.body.style.overflow).toBe('hidden')
  })

  it('restores body overflow when closed', () => {
    const { rerender } = render(
      <Modal isOpen={true} onClose={mockOnClose}>
        <div>Modal Content</div>
      </Modal>
    )
    expect(document.body.style.overflow).toBe('hidden')

    rerender(
      <Modal isOpen={false} onClose={mockOnClose}>
        <div>Modal Content</div>
      </Modal>
    )
    expect(document.body.style.overflow).toBe('unset')
  })

  describe('accessibility', () => {
    it('has proper ARIA attributes', () => {
      render(
        <Modal isOpen={true} title="Accessible Modal" onClose={mockOnClose}>
          <div>Modal Content</div>
        </Modal>
      )
      
      const dialog = screen.getByRole('dialog')
      expect(dialog).toHaveAttribute('aria-modal', 'true')
      expect(dialog).toHaveAttribute('aria-labelledby', 'modal-title')
    })

    it('focuses modal content when opened', () => {
      render(
        <Modal isOpen={true} onClose={mockOnClose}>
          <div>Modal Content</div>
        </Modal>
      )
      
      const modalContent = document.querySelector('.modal-content')
      expect(modalContent).toHaveFocus()
    })

    it('does not have aria-labelledby when no title is provided', () => {
      render(
        <Modal isOpen={true} onClose={mockOnClose}>
          <div>Modal Content</div>
        </Modal>
      )
      
      const dialog = screen.getByRole('dialog')
      expect(dialog).not.toHaveAttribute('aria-labelledby')
    })
  })

  describe('keyboard navigation', () => {
    it('does not call onClose on other keys', async () => {
      const user = userEvent.setup()
      render(
        <Modal isOpen={true} onClose={mockOnClose}>
          <div>Modal Content</div>
        </Modal>
      )
      
      await user.keyboard('{Enter}')
      await user.keyboard(' ')
      await user.keyboard('{Tab}')
      expect(mockOnClose).not.toHaveBeenCalled()
    })
  })
})