# Scratchy Agent UI

A clean, modern, and eye-catching web interface for the Scratchy Agent chatbot.

![UI Preview](preview.png)

## Features

- 🎨 **Clean Modern Design** - Dark/Light theme with smooth animations
- 📁 **Document Upload** - Drag & drop or click to upload files
- 📂 **Generated Files Sidebar** - View all files created by the agent
- 💬 **Chat Interface** - Claude-like conversational experience
- 🔧 **Tool Approval** - Approve/deny tool executions in real-time
- 🔄 **Session Management** - Multiple chat sessions support
- ⚡ **Real-time Streaming** - See agent responses as they're generated

## Quick Start

### Option 1: Static UI (Demo Mode)

Simply open the `index.html` file in your browser:

```bash
# Windows
start ui/index.html

# Or double-click index.html in File Explorer
```

### Option 2: With Backend Server (Full Functionality)

1. **Install dependencies:**
   ```bash
   pip install websockets
   ```

2. **Start the backend server:**
   ```bash
   python ui/server.py
   ```

3. **Open the UI in your browser:**
   ```
   file:///d:/Scratchy/ui/index.html
   ```
   
   Or use a local server:
   ```bash
   # Python 3
   cd ui
   python -m http.server 3000
   # Then open http://localhost:3000
   ```

## Configuration

### Model Selection

Use the dropdown in the top bar to select your preferred model:
- Ollama (Local models)
- Google Gemini
- Groq

### Settings

Click the ⚙️ Settings button in the sidebar to:
- Change API provider
- Enter API keys for cloud providers
- Switch between Dark/Light themes

## File Structure

```
ui/
├── index.html      # Main HTML structure
├── styles.css      # Design system & styles
├── app.js          # Frontend JavaScript
├── server.py       # WebSocket backend
└── README.md       # This file
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Send message |
| `Shift + Enter` | New line in input |
| `Drag & Drop` | Upload files |

## Customization

### Themes

Edit the CSS variables in `styles.css` to customize colors:

```css
:root {
    --accent-primary: #4a9eff;    /* Primary accent color */
    --accent-secondary: #7b68ee;  /* Secondary accent */
    --bg-primary: #0f0f0f;        /* Main background */
    /* ... more variables */
}
```

### Adding Quick Actions

Add new quick action buttons in `index.html`:

```html
<button class="quick-action" data-action="custom">
    <!-- SVG icon -->
    <span>Custom Action</span>
</button>
```

Then handle it in `app.js`:

```javascript
handleQuickAction(event) {
    const action = event.currentTarget.dataset.action;
    if (action === 'custom') {
        // Your custom logic
    }
}
```

## API Integration

The UI communicates with the backend via WebSocket. Message types:

### Client → Server

| Type | Description |
|------|-------------|
| `message` | Send a chat message |
| `new_session` | Create new session |
| `switch_session` | Switch to session |
| `tool_approval_response` | Approve/deny tool |

### Server → Client

| Type | Description |
|------|-------------|
| `token` | Streaming token |
| `tool_start` | Tool execution started |
| `tool_end` | Tool execution completed |
| `tool_approval` | Request tool approval |
| `file_generated` | New file created |
| `complete` | Response complete |
| `error` | Error message |

## Browser Support

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## License

MIT License - Part of the Scratchy Agent project.
