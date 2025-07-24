import { createVuetify } from 'vuetify'

import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

export default defineNuxtPlugin((app) => {
  const vuetify = createVuetify({
    theme: {
      defaultTheme: 'dark',
      themes: {
        light: {
          dark: false,
          colors: {
            // Primary colors - sage green
            'primary': 'rgb(106, 127, 83)', // Darker sage for better contrast
            'primary-lighten-1': 'rgb(142, 147, 108)', // Your original color
            'primary-lighten-2': 'rgb(168, 176, 140)',
            'primary-darken-1': 'rgb(85, 102, 66)',
            'primary-darken-2': 'rgb(64, 77, 50)',

            // Secondary colors - muted purple
            'secondary': 'rgb(89, 82, 127)', // Darker purple for better contrast
            'secondary-lighten-1': 'rgb(113, 108, 147)', // Your original color
            'secondary-lighten-2': 'rgb(140, 136, 168)',
            'secondary-darken-1': 'rgb(71, 66, 102)',
            'secondary-darken-2': 'rgb(53, 49, 76)',

            // Accent colors
            'accent': 'rgb(191, 155, 108)', // Warm brown
            'info': 'rgb(79, 143, 186)', // Muted blue
            'success': 'rgb(95, 158, 124)', // Muted green
            'warning': 'rgb(204, 156, 73)', // Muted orange
            'error': 'rgb(181, 99, 99)', // Muted red

            // Background colors
            'background': 'rgb(250, 250, 248)', // Warm white
            'surface': 'rgb(255, 255, 255)', // Pure white for cards
            'surface-variant': 'rgb(235, 235, 235)', // Slightly off-white
            'surface-variant-light': 'rgb(245, 245, 245)', // Lighter variant for contrast
            'surface-variant-dark': 'rgb(220, 220, 220)', // Darker variant for contrast

            // Text colors
            'on-primary': 'rgb(255, 255, 255)', // White text on primary
            'on-secondary': 'rgb(255, 255, 255)', // White text on secondary
            'on-background': 'rgb(33, 37, 41)', // Dark text on background
            'on-surface': 'rgb(33, 37, 41)', // Dark text on surface
            'on-surface-variant': 'rgb(73, 80, 87)', // Medium text

            // Transparent variants (for CSS usage)
            'primary-transparent': 'rgb(106, 127, 83)',
            'secondary-transparent': 'rgb(89, 82, 127)',
          },
        },
        dark: {
          dark: true,
          colors: {
            // Primary colors - brighter sage for dark theme
            'primary': 'rgb(152, 170, 120)', // Brighter sage
            'primary-lighten-1': 'rgb(178, 186, 150)',
            'primary-lighten-2': 'rgb(204, 211, 180)',
            'primary-darken-1': 'rgb(128, 143, 101)',
            'primary-darken-2': 'rgb(104, 116, 83)',

            // Secondary colors - brighter purple for dark theme
            'secondary': 'rgb(136, 128, 174)', // Brighter purple
            'secondary-lighten-1': 'rgb(161, 154, 194)',
            'secondary-lighten-2': 'rgb(186, 180, 214)',
            'secondary-darken-1': 'rgb(111, 104, 141)',
            'secondary-darken-2': 'rgb(86, 81, 108)',

            // Accent colors - brighter for dark theme
            'accent': 'rgb(225, 189, 142)', // Brighter warm brown
            'info': 'rgb(113, 177, 220)', // Brighter blue
            'success': 'rgb(129, 192, 158)', // Brighter green
            'warning': 'rgb(238, 190, 107)', // Brighter orange
            'error': 'rgb(215, 133, 133)', // Brighter red

            // Background colors - significantly brighter
            'background': 'rgb(32, 36, 40)', // Much brighter background
            'surface': 'rgb(48, 54, 60)', // Brighter surface for cards
            'surface-variant': 'rgb(58, 64, 70)', // Brighter surface variant
            'surface-variant-light': 'rgb(68, 74, 80)', // Even brighter variant
            'surface-variant-dark': 'rgb(42, 48, 54)', // Brighter dark variant

            // Text colors for dark theme
            'on-primary': 'rgb(255, 255, 255)', // White text on primary
            'on-secondary': 'rgb(255, 255, 255)', // White text on secondary
            'on-background': 'rgb(240, 240, 240)', // Brighter text on dark background
            'on-surface': 'rgb(240, 240, 240)', // Brighter text on dark surface
            'on-surface-variant': 'rgb(200, 200, 200)', // Brighter medium text

            // Transparent variants (for CSS usage)
            'primary-transparent': 'rgb(152, 170, 120)',
            'secondary-transparent': 'rgb(136, 128, 174)',
          },
        },
      },
    },
    defaults: {
      VTextField: {
        variant: 'outlined',
      },
      VAutocomplete: {
        variant: 'outlined',
      },
      VSelect: {
        variant: 'outlined',
      },
      VBtn: {
        variant: 'outlined',
        rounded: 'xl',
      },
      VContainer: {
        style: 'max-width: 1400px',
      },
      VCard: {
        rounded: 'lg',
        width: '100%',
      },
      VTab: {
        rounded: 'xl',
      },
      VListItem: {
        rounded: 'lg',
      },
    },
    display: {
      mobileBreakpoint: 'sm',
    },
  })
  app.vueApp.use(vuetify)
})
