# CodeLens Frontend - Routing Integration

This document describes the URL routing integration with the stepper component.

## Routes

The application now supports the following routes:

- `/` - Redirects to `/home`
- `/home` - Home page (Step 0)
- `/enter-api-key` - API Key entry page (Step 1)
- `/enter-code` - Code input page (Step 2)
- `/results` - Results display page (Step 3)

## Features

### 1. URL-Stepper Synchronization
- Users can navigate by clicking stepper items
- Users can navigate by typing URLs directly
- Current stepper item reflects the current URL
- Browser back/forward buttons work correctly

### 2. Navigation Controls
- Next/Previous buttons on each page
- Keyboard shortcuts:
  - `Ctrl + →` - Next step
  - `Ctrl + ←` - Previous step
- Stepper items are clickable and navigate to corresponding routes

### 3. State Management
- Current stepper state is synchronized with the URL
- Navigation preserves application state
- WebSocket connection is maintained across navigation

## File Structure

```
frontend/
├── layouts/
│   └── default.vue          # Main layout with stepper header
├── pages/
│   ├── index.vue           # Redirects to /home
│   ├── home.vue            # Home page
│   ├── enter-api-key.vue   # API Key entry
│   ├── enter-code.vue      # Code input
│   └── results.vue         # Results display
└── composables/
    ├── useStepper.ts                    # Main stepper logic
    ├── useStepperNavigation.ts         # Navigation utilities
```

## Usage

### Adding New Steps

1. Add a new item to the `stepperItems` array in `useStepper.ts`:
```typescript
{ title: 'New Step', path: '/new-step', value: 4 }
```

2. Create a new page at `pages/new-step.vue`

3. The navigation will automatically work with the new step

### Customizing Navigation

Use the `useStepperNavigation` composable in your pages:

```typescript
const { goNext, goPrevious, canGoNext, canGoPrevious } = useStepperNavigation()
```

### Keyboard Navigation

Keyboard shortcuts are automatically available on all pages. They are disabled when input elements are focused to avoid conflicts.

## Technical Details

- Uses Nuxt 3's file-based routing
- Vue Router handles navigation
- Watchers sync URL changes with stepper state
- Composables provide reusable navigation logic
- Keyboard shortcuts use @vueuse/core for event handling
