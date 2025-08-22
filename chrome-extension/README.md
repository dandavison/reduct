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
3. (Optional) Click "Advanced Options" to customize the prompt
   - The default prompt is pre-filled and shows {LEVEL} which updates with your slider
4. Click "Reduce Page" to reduce the current page's text
5. A progress indicator appears on the page with:
   - Live progress bar
   - Cancel button to stop and restore original content
6. Click "Restore Original" in the extension to revert changes after completion

The extension preserves:
- Page layout and structure
- Images, videos, and diagrams
- Code blocks and preformatted text
- Navigation and interactive elements

## Features

- Real-time server status checking
- On-page progress indicator with integrated cancel button
- Adjustable reduction level (20-80%)
- Pre-populated custom prompt with dynamic {LEVEL} placeholder
- HTML formatting support (bullet lists, numbered lists, paragraphs)
- One-click restore to original content
- Preserves page structure and non-text elements
- Clean down-arrow icon indicating reduction functionality

## Custom Prompts

The extension allows you to override the default reduction prompt. Examples:

- "Summarize the key technical points only"
- "Extract action items and decisions"  
- "Focus on the data and statistics"
- "Remove examples but keep the explanations"

## Collapsible Details

The extension supports collapsible sections for less important content. The LLM can use this syntax:

```
[Details: Summary of hidden content]
Content that will be hidden by default
Can span multiple lines
[/Details]
```

This renders as an HTML `<details>` element that users can click to expand.

## Requirements

- Chrome browser
- Python environment with reduct installed
- LLM API key (Anthropic, OpenAI, etc.)
