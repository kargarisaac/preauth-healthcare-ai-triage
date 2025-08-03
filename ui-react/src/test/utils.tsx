import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import { AppProvider } from '@contexts/AppContext'
import { ProcessingProvider } from '@contexts/ProcessingContext'
import { ToastProvider } from '@contexts/ToastContext'
import { ThemeProvider } from '@contexts/ThemeContext'

import fileProcessingReducer from '@/store/slices/fileProcessingSlice'
import validationReducer from '@/store/slices/validationSlice'
import userPreferencesReducer from '@/store/slices/userPreferencesSlice'
import notificationReducer from '@/store/slices/notificationSlice'

import type { RootState } from '@/store'

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  initialEntries?: string[]
  preloadedState?: Partial<RootState>
  store?: ReturnType<typeof configureStore>
}

// Create a test store factory
export function createTestStore(preloadedState?: Partial<RootState>) {
  return configureStore({
    reducer: {
      fileProcessing: fileProcessingReducer,
      validation: validationReducer,
      userPreferences: userPreferencesReducer,
      notifications: notificationReducer,
    },
    preloadedState,
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: {
          ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
        },
      }),
  })
}

const AllTheProviders = ({
  children,
  initialEntries = ['/'],
  store
}: {
  children: React.ReactNode
  initialEntries?: string[]
  store?: ReturnType<typeof configureStore>
}) => {
  return (
    <BrowserRouter>
      <Provider store={store || createTestStore()}>
        <AppProvider>
          <ToastProvider>
            <ThemeProvider>
              <ProcessingProvider>
                {children}
              </ProcessingProvider>
            </ThemeProvider>
          </ToastProvider>
        </AppProvider>
      </Provider>
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
