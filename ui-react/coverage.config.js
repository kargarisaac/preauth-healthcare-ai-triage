export default {
  // Coverage thresholds
  thresholds: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    },
    // Per-file thresholds for critical components
    './src/components/ui/**/*.tsx': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90
    },
    './src/hooks/**/*.ts': {
      branches: 85,
      functions: 85,
      lines: 85,
      statements: 85
    },
    './src/contexts/**/*.tsx': {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },

  // Files to include in coverage
  include: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/test/**/*',
    '!src/**/*.stories.{ts,tsx}',
    '!src/**/*.test.{ts,tsx}',
    '!src/**/*.spec.{ts,tsx}',
    '!src/main.tsx',
    '!src/vite-env.d.ts'
  ],

  // Files to exclude from coverage
  exclude: [
    'node_modules/',
    'dist/',
    'build/',
    'coverage/',
    '**/*.config.{js,ts}',
    '**/*.d.ts',
    'src/test/**/*',
    'tests/**/*',
    '**/__tests__/**/*',
    '**/*.stories.{ts,tsx}'
  ],

  // Coverage reporters
  reporters: [
    'text',
    'text-summary',
    'html',
    'json',
    'lcov',
    'cobertura'
  ],

  // Output directory for coverage reports
  reportsDirectory: 'coverage',

  // Clean coverage directory before each run
  clean: true,

  // Skip files with no statements
  skipEmpty: true,

  // Include untested files in coverage report
  all: true,

  // Watermarks for coverage levels
  watermarks: {
    statements: [70, 90],
    functions: [70, 90],
    branches: [70, 90],
    lines: [70, 90]
  }
}
