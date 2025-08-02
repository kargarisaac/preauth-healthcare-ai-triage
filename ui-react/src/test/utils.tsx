import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AppProvider } from '@contexts/AppContext'
import { ProcessingProvider } from '@contexts/ProcessingContext'
import { ToastProvider } from '@contexts/ToastContext'

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  initialEntries?: string[]
}

const AllTheProviders = ({ 
  children, 
  initialEntries = ['/']
}: {
  children: React.ReactNode
  initialEntries?: string[]
}) => {
  return (
    <BrowserRouter>
      <AppProvider>
        <ToastProvider>
          <ProcessingProvider>
            {children}
          </ProcessingProvider>
        </ToastProvider>
      </AppProvider>
    </BrowserRouter>
  )
}

const customRender = (
  ui: ReactElement,
  options: CustomRenderOptions = {}
) => {
  const {
    initialEntries,
    ...renderOptions
  } = options

  return render(ui, {
    wrapper: ({ children }) => (
      <AllTheProviders initialEntries={initialEntries}>
        {children}
      </AllTheProviders>
    ),
    ...renderOptions,
  })
}

// Export everything
export * from '@testing-library/react'
export { customRender as render }