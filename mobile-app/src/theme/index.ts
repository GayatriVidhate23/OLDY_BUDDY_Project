export const theme = {
  colors: {
    primary: '#1F6CFA',
    secondary: '#FF3B30',
    background: '#FFFFFF',
    surface: '#F2F2F7',
    text: '#000000',
    textSecondary: '#666666',
    border: '#E5E5EA',
    error: '#FF3B30',
    success: '#34C759',
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },
  typography: {
    h1: {
      fontSize: 34,
      fontWeight: 'bold',
      lineHeight: 41,
    },
    h2: {
      fontSize: 28,
      fontWeight: 'bold',
      lineHeight: 34,
    },
    body: {
      fontSize: 22,
      fontWeight: 'normal',
      lineHeight: 28,
    },
    button: {
      fontSize: 24,
      fontWeight: 'bold',
    },
    caption: {
      fontSize: 18,
      lineHeight: 22,
    },
  },
  roundness: 12,
} as const;

export type Theme = typeof theme;
