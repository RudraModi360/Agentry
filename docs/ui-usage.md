# Scratchy UI Documentation
## *The Modern Web Interface*

For a more visual experience, Scratchy provides a local web server with a modern chat interface.

### Running the Server

Start the UI backend:

```bash
python ui/server.py
```

Then visit **http://localhost:8000** in your browser.

### Features

- **Rich Tool Cards**: See tool execution steps clearly visualized.
- **Drag & Drop**: Easily upload files by dragging them into the chat.
- **Session Sidebar**: Switch between past conversations instantly.
- **Markdown Support**: Full rendering for code blocks and tables.

### Configuration

The UI connects to the same backend agent as the CLI. It uses WebSockets for real-time streaming, ensuring low latency.
