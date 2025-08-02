import '@testing-library/jest-dom'
import { expect, afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

// extends Vitest's expect method with methods from react-testing-library
expect.extend(matchers)

// runs a cleanup after each test case (e.g. clearing jsdom)
afterEach(() => {
  cleanup()
})

// Make vi globally available
globalThis.vi = vi

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // Deprecated
    removeListener: vi.fn(), // Deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock window.scrollTo
Object.defineProperty(window, 'scrollTo', {
  writable: true,
  value: vi.fn(),
})

// Mock HTMLCanvasElement.getContext
HTMLCanvasElement.prototype.getContext = vi.fn()

// Mock File and FileReader
global.File = class File {
  constructor(fileBits: BlobPart[], fileName: string, options?: FilePropertyBag) {
    // Basic mock implementation
  }
} as any

global.FileReader = class FileReader {
  result: string | ArrayBuffer | null = null
  error: DOMException | null = null
  readyState: number = 0
  onload: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null
  onerror: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null
  onabort: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null
  onloadstart: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null
  onloadend: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null
  onprogress: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null

  readAsText() {
    setTimeout(() => {
      this.result = 'mock file content'
      this.onload?.call(this, {} as ProgressEvent<FileReader>)
    }, 10)
  }

  readAsDataURL() {
    setTimeout(() => {
      this.result = 'data:text/plain;base64,bW9jayBmaWxlIGNvbnRlbnQ='
      this.onload?.call(this, {} as ProgressEvent<FileReader>)
    }, 10)
  }

  abort() {}
  addEventListener() {}
  removeEventListener() {}
  dispatchEvent() { return true }
} as any
