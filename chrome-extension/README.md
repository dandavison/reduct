# Reduct Chrome Extension

Chrome extension for reducing web page text content using AI while preserving layout.

## Installation

1. Start the reduct server:
   ```bash
   export LLM_MODEL=anthropic/claude-3-haiku-20240307  # or your preferred model
   export LLM_KEY=your-api-key  # or ANTHROPIC_API_KEY/OPENAI_API_KEY
   uv run reduct-server
   ```

2. Load the extension in Chrome:
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top right)
   - Click "Load unpacked"
   - Select the `chrome-extension` directory

## Usage

1. Click the Reduct extension icon in your toolbar
2. Adjust the reduction level (20-80%)
3. Click "Reduce Page" to reduce the current page's text
4. Click "Restore Original" to revert changes

The extension preserves:
- Page layout and structure
- Images, videos, and diagrams
- Code blocks and preformatted text
- Navigation and interactive elements

## Features

- Real-time server status checking
- Visual indicators for loading and reduced state
- Adjustable reduction level
- One-click restore to original content

## Requirements

- Chrome browser
- Python environment with reduct installed
- LLM API key (Anthropic, OpenAI, etc.)
