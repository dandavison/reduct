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
3. (Optional) Click "Advanced Options" to enter a custom prompt
4. Click "Reduce Page" to reduce the current page's text
5. Watch the progress bar as text blocks are processed
6. Click "Restore Original" to revert changes

The extension preserves:
- Page layout and structure
- Images, videos, and diagrams
- Code blocks and preformatted text
- Navigation and interactive elements

## Features

- Real-time server status checking
- Visual progress bar showing reduction progress
- Adjustable reduction level (20-80%)
- Custom prompt support for specialized reductions
- One-click restore to original content
- Preserves page structure and non-text elements

## Custom Prompts

The extension allows you to override the default reduction prompt. Examples:

- "Summarize the key technical points only"
- "Extract action items and decisions"
- "Focus on the data and statistics"
- "Remove examples but keep the explanations"

## Requirements

- Chrome browser
- Python environment with reduct installed
- LLM API key (Anthropic, OpenAI, etc.)
