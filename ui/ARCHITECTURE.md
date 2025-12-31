# Agentry UI Architecture

This document describes the modular architecture of the Agentry UI.

## Overview

The UI has been refactored from a monolithic `chat.html` file (~340KB) to a modular architecture where CSS and JavaScript are separated into logical components. The new `chat-refactored.html` is only ~18KB.

## Directory Structure

```
ui/
├── chat.html                 # Original monolithic file (kept for reference)
├── chat-refactored.html      # New modular HTML entry point
├── ARCHITECTURE.md           # This documentation
├── css/
│   ├── main.css              # Main CSS entry point (imports all components)
│   ├── variables.css         # Design tokens (colors, typography, spacing)
│   ├── base.css              # CSS reset, global styles, utilities
│   └── components/
│       ├── buttons.css       # Button styles
│       ├── cards.css         # Card components
│       ├── forms.css         # Form inputs and controls
│       ├── layout.css        # Main app layout (header, container)
│       ├── loaders.css       # Spinners and loading indicators
│       ├── messages.css      # Chat message styling
│       ├── modals.css        # Modal dialogs
│       ├── sidebar.css       # Sidebar navigation
│       └── tools.css         # Tools popup styling
└── js/
    ├── config.js             # Central configuration
    ├── main.js               # Application entry point
    ├── utils/
    │   ├── dom.js            # DOM utilities
    │   ├── api.js            # API request utilities
    │   └── storage.js        # LocalStorage/SessionStorage utilities
    └── components/
        ├── theme.js          # Light/dark theme management
        ├── clock.js          # Clock widget
        ├── sidebar.js        # Sidebar collapse/resize
        ├── messages.js       # Message rendering & interactions
        ├── websocket.js      # WebSocket connection & handlers
        ├── modals.js         # All modal dialogs
        ├── tools.js          # Tools popup
        ├── sessions.js       # Session management
        └── upload.js         # Image upload handling
```

## CSS Architecture

### Design Tokens (`variables.css`)

All design tokens are centralized using CSS custom properties:

- **Colors**: Primary, accent, text colors for both light and dark themes
- **Typography**: Font families, sizes, weights
- **Spacing**: Consistent spacing scale
- **Borders**: Border radius, widths
- **Shadows**: Elevation levels
- **Transitions**: Animation timings

### Theme System

The app supports light and dark themes via the `data-theme` attribute on `<html>`:

```css
[data-theme="light"] {
    --bg-primary: #ffffff;
    --text-primary: #1a1a2e;
}

[data-theme="dark"] {
    --bg-primary: #0f0f1a;
    --text-primary: #e8e8e8;
}
```

### Import Order (`main.css`)

```css
/* 1. Design tokens */
@import 'variables.css';

/* 2. Base styles and utilities */
@import 'base.css';

/* 3. Component styles */
@import 'components/buttons.css';
@import 'components/forms.css';
@import 'components/cards.css';
@import 'components/sidebar.css';
@import 'components/layout.css';
@import 'components/messages.css';
@import 'components/modals.css';
@import 'components/loaders.css';
@import 'components/tools.css';

/* 4. Legacy Compatibility */
/* Ensures original inline styles are preserved */
@import 'legacy-compat.css';
```

## JavaScript Architecture

### Configuration (`config.js`)

Central configuration for the application:

```javascript
const AppConfig = {
    api: { baseUrl: '' },
    auth: { tokenKey: 'agentry_token', loginPath: '/login' },
    websocket: { reconnectDelay: 3000, pingInterval: 30000 },
    agents: { /* agent type definitions */ },
    tools: { /* tool configuration */ },
    theme: { storageKey: 'agentry_theme', default: 'dark' },
    debug: false
};
```

### Utilities

- **`dom.js`**: DOM manipulation helpers (selectors, element creation, event binding)
- **`api.js`**: HTTP request wrapper with authentication
- **`storage.js`**: Local/Session storage with JSON support

### Components

Each component follows this pattern:

```javascript
const ComponentName = {
    // State
    state: {},
    
    // Initialize component
    init() { /* setup */ },
    
    // Component methods
    methodName() { /* implementation */ }
};

// Export
window.ComponentName = ComponentName;
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| `theme.js` | Light/dark theme toggle, system preference detection |
| `clock.js` | Multi-timezone clock widget display |
| `sidebar.js` | Collapse, resize, mobile toggle |
| `messages.js` | Message rendering, markdown, tool calls, edit/delete |
| `websocket.js` | Connection, message routing, streaming |
| `modals.js` | Approval, search, MCP config, media gallery |
| `tools.js` | Tools popup, toggle states, MCP servers |
| `sessions.js` | Session list, create, delete, load |
| `upload.js` | Image drag-drop, preview, upload |

### Application Entry Point (`main.js`)

The main entry point orchestrates initialization:

```javascript
const App = {
    state: { /* global state */ },
    
    async init() {
        // Check auth
        // Initialize components
        // Load initial data
        // Connect WebSocket
    }
};

DOM.ready(() => App.init());
```

### Script Load Order

Scripts must be loaded in this order in HTML:

1. `config.js` - Configuration first
2. `utils/dom.js` - DOM utilities
3. `utils/api.js` - API utilities  
4. `utils/storage.js` - Storage utilities
5. `components/theme.js` - Theme (runs immediately)
6. `components/clock.js` - Clock widget
7. `components/sidebar.js` - Sidebar controls
8. `components/messages.js` - Message rendering
9. `components/websocket.js` - WebSocket connection
10. `components/modals.js` - Modal dialogs
11. `components/tools.js` - Tools popup
12. `components/sessions.js` - Session management
13. `components/upload.js` - Image upload
14. `main.js` - Entry point (initializes everything)

## Data Flow

```
User Input
    ↓
App.sendMessage()
    ↓
WebSocketManager.sendMessage()
    ↓
WebSocket Server
    ↓
WebSocketManager.handleMessage()
    ↓
Messages.updateAssistantMessageText()
    ↓
UI Update
```

## External Dependencies

- **marked.js**: Markdown parsing
- **highlight.js**: Code syntax highlighting
- **Google Fonts**: Inter, JetBrains Mono

## Migration from Original

To migrate from `chat.html` to the modular version:

1. Ensure all CSS files are created in `css/`
2. Ensure all JS files are created in `js/`
3. Use `chat-refactored.html` as the entry point
4. Test all functionality:
   - Authentication flow
   - Session management (create, load, delete)
   - WebSocket connection
   - Message sending and streaming
   - Tool calls and approvals
   - Image upload
   - Theme toggle
   - MCP configuration

## Benefits

1. **Maintainability**: Each file has a single responsibility
2. **Readability**: Files are small and focused
3. **Caching**: Unchanged files can be cached by browsers
4. **Collaboration**: Easier to work on different components
5. **Debugging**: Issues are isolated to specific components
6. **Extensibility**: Adding new features is straightforward

## Future Improvements

1. **Bundling**: Use Vite/Webpack for production builds
2. **Minification**: Reduce file sizes for production
3. **TypeScript**: Add type safety
4. **Testing**: Add unit tests for components
5. **Module System**: Migrate to ES modules with imports/exports
