import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@/test/utils'
import userEvent from '@testing-library/user-event'
import FileUploadArea from '../FileUploadArea'
import { createMockFile } from '@/test/mockData'

// Mock the ProcessingContext
const mockProcessingContext = {
  currentFile: null,
  processingResults: null,
  isProcessing: false,
  uploadProgress: 0,
  setCurrentFile: vi.fn(),
  setProcessingResults: vi.fn(),
  setIsProcessing: vi.fn(),
  setUploadProgress: vi.fn(),
  processFile: vi.fn(),
  processSampleFile: vi.fn(),
  clearResults: vi.fn()
}

vi.mock('@/contexts/ProcessingContext', () => ({
  useProcessing: () => mockProcessingContext
}))

describe('FileUploadArea Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders upload area with default state', () => {
    render(<FileUploadArea />)

    expect(screen.getByText('Drop files here or click to upload')).toBeInTheDocument()
    expect(screen.getByText('XML or CSV files up to 10MB')).toBeInTheDocument()
  })

  it('shows file input is hidden', () => {
    render(<FileUploadArea />)

    const fileInput = document.getElementById('file-upload')
    expect(fileInput).toHaveClass('hidden')
    expect(fileInput).toHaveAttribute('accept', '.xml,.csv')
  })

  it('handles file selection via click', async () => {
    const user = userEvent.setup()
    render(<FileUploadArea />)

    const dropZone = screen.getByText('Drop files here or click to upload').closest('div')
    expect(dropZone).toBeInTheDocument()

    await user.click(dropZone!)

    // File input should be triggered (can't fully test file selection in jsdom)
    const fileInput = document.getElementById('file-upload')
    expect(fileInput).toHaveAttribute('type', 'file')
  })

  it('displays selected file information', () => {
    const mockFile = createMockFile('test.xml', 'text/xml', 'test content')
    mockProcessingContext.currentFile = mockFile

    render(<FileUploadArea />)

    expect(screen.getByText('test.xml')).toBeInTheDocument()
    expect(screen.getByText('12 B')).toBeInTheDocument() // "test content" is 12 bytes
  })

  it('shows CSV file with database icon', () => {
    const mockFile = createMockFile('test.csv', 'text/csv', 'data,data')
    mockProcessingContext.currentFile = mockFile

    render(<FileUploadArea />)

    // Database icon should be rendered for CSV files
    expect(document.querySelector('.text-green-600')).toBeInTheDocument()
  })

  it('shows XML file with file text icon', () => {
    const mockFile = createMockFile('test.xml', 'text/xml', '<data></data>')
    mockProcessingContext.currentFile = mockFile

    render(<FileUploadArea />)

    // FileText icon should be rendered for XML files
    expect(document.querySelector('.text-green-600')).toBeInTheDocument()
  })

  it('shows process and clear buttons when file is selected', () => {
    const mockFile = createMockFile('test.xml', 'text/xml')
    mockProcessingContext.currentFile = mockFile

    render(<FileUploadArea />)

    expect(screen.getByRole('button', { name: /process/i })).toBeInTheDocument()
    expect(screen.getByRole('button')).toBeInTheDocument() // Clear button (X)
  })

  it('handles process button click', async () => {
    const user = userEvent.setup()
    const mockFile = createMockFile('test.xml', 'text/xml')
    mockProcessingContext.currentFile = mockFile

    render(<FileUploadArea />)

    const processButton = screen.getByRole('button', { name: /process/i })
    await user.click(processButton)

    expect(mockProcessingContext.processFile).toHaveBeenCalledWith('eclaim')
  })

  it('handles CSV file processing', async () => {
    const user = userEvent.setup()
    const mockFile = createMockFile('test.csv', 'text/csv')
    mockProcessingContext.currentFile = mockFile

    render(<FileUploadArea />)

    const processButton = screen.getByRole('button', { name: /process/i })
    await user.click(processButton)

    expect(mockProcessingContext.processFile).toHaveBeenCalledWith('csv')
  })

  it('handles clear button click', async () => {
    const user = userEvent.setup()
    const mockFile = createMockFile('test.xml', 'text/xml')
    mockProcessingContext.currentFile = mockFile

    render(<FileUploadArea />)

    const clearButton = screen.getByRole('button', { name: '' }) // X button has no text
    await user.click(clearButton)

    expect(mockProcessingContext.setCurrentFile).toHaveBeenCalledWith(null)
  })

  it('shows processing state', () => {
    const mockFile = createMockFile('test.xml', 'text/xml')
    mockProcessingContext.currentFile = mockFile
    mockProcessingContext.isProcessing = true

    render(<FileUploadArea />)

    expect(screen.getByText('Processing...')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /processing/i })).toBeDisabled()
  })

  it('shows progress bar when processing', () => {
    const mockFile = createMockFile('test.xml', 'text/xml')
    mockProcessingContext.currentFile = mockFile
    mockProcessingContext.isProcessing = true
    mockProcessingContext.uploadProgress = 45

    render(<FileUploadArea />)

    expect(screen.getByText('Processing...')).toBeInTheDocument()
    expect(screen.getByText('45%')).toBeInTheDocument()

    const progressBar = document.querySelector('.bg-blue-600')
    expect(progressBar).toHaveStyle({ width: '45%' })
  })

  it('shows processing results', () => {
    mockProcessingContext.processingResults = {
      id: 'test-result',
      status: 'completed',
      metadata: {
        processing_time_seconds: 2.5
      }
    }

    render(<FileUploadArea />)

    expect(screen.getByText(/Processed successfully in 2.5s/)).toBeInTheDocument()
    expect(document.querySelector('.text-green-600')).toBeInTheDocument() // CheckCircle icon
  })

  describe('drag and drop functionality', () => {
    it('handles drag over state', async () => {
      render(<FileUploadArea />)

      const dropZone = screen.getByText('Drop files here or click to upload').closest('div')

      // Simulate drag over
      const dragOverEvent = new Event('dragover', { bubbles: true })
      Object.defineProperty(dragOverEvent, 'preventDefault', { value: vi.fn() })

      dropZone?.dispatchEvent(dragOverEvent)

      await waitFor(() => {
        expect(dropZone).toHaveClass('border-blue-400', 'bg-blue-50')
      })
    })

    it('handles drag leave state', async () => {
      render(<FileUploadArea />)

      const dropZone = screen.getByText('Drop files here or click to upload').closest('div')

      // Simulate drag leave
      const dragLeaveEvent = new Event('dragleave', { bubbles: true })
      Object.defineProperty(dragLeaveEvent, 'preventDefault', { value: vi.fn() })

      dropZone?.dispatchEvent(dragLeaveEvent)

      await waitFor(() => {
        expect(dropZone).not.toHaveClass('border-blue-400', 'bg-blue-50')
      })
    })
  })

  describe('file size formatting', () => {
    it('formats bytes correctly', () => {
      const file1 = createMockFile('small.txt', 'text/plain', 'a') // 1 byte
      mockProcessingContext.currentFile = file1

      const { rerender } = render(<FileUploadArea />)
      expect(screen.getByText('1 B')).toBeInTheDocument()

      // Test KB
      const file2 = createMockFile('medium.txt', 'text/plain', 'a'.repeat(1024)) // 1KB
      mockProcessingContext.currentFile = file2
      rerender(<FileUploadArea />)
      expect(screen.getByText('1 KB')).toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('has proper file input attributes', () => {
      render(<FileUploadArea />)

      const fileInput = document.getElementById('file-upload')
      expect(fileInput).toHaveAttribute('type', 'file')
      expect(fileInput).toHaveAttribute('accept', '.xml,.csv')
    })

    it('provides keyboard navigation for buttons', async () => {
      const user = userEvent.setup()
      const mockFile = createMockFile('test.xml', 'text/xml')
      mockProcessingContext.currentFile = mockFile

      render(<FileUploadArea />)

      await user.tab() // Focus first button (process)
      expect(screen.getByRole('button', { name: /process/i })).toHaveFocus()

      await user.tab() // Focus second button (clear)
      const buttons = screen.getAllByRole('button')
      expect(buttons[1]).toHaveFocus()
    })
  })
})
