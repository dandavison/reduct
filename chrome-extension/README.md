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
2. Adjust the reduction level (5-80%)
3. (Optional) Click "Advanced Options" to customize the prompt
   - The default prompt shows {REDUCT_FACTOR} as a placeholder
   - This will be replaced with the slider value when you reduce
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
- Adjustable reduction level (5-80%)
- Pre-populated custom prompt with {REDUCT_FACTOR} placeholder
- Rich HTML formatting support
- One-click restore to original content
- Preserves page structure and non-text elements
- Clean down-arrow icon indicating reduction functionality

## HTML Output

The extension uses direct HTML generation for maximum formatting flexibility:

### Supported HTML Elements
- **Structure**: `<p>`, `<h1>`-`<h6>`, `<blockquote>`, `<hr>`
- **Lists**: `<ul>`, `<ol>`, `<li>`
- **Emphasis**: `<strong>`, `<em>`, `<mark>`, `<del>`, `<ins>`
- **Code**: `<code>`, `<pre>`
- **Collapsible**: `<details>`, `<summary>`

### Collapsible Details

Less important content can be collapsed using:
```html
<details>
  <summary>Click to expand technical details</summary>
  <p>Detailed technical information here...</p>
</details>
```

## Custom Prompts

When writing custom prompts, you can use {REDUCT_FACTOR} as a placeholder:

- "Condense to {REDUCT_FACTOR}% focusing on technical details"
- "Create a {REDUCT_FACTOR}% summary as an HTML list"
- "Reduce to {REDUCT_FACTOR}% with <strong> tags for key terms"
- "Extract the top {REDUCT_FACTOR}% most important points"

The {REDUCT_FACTOR} placeholder will be replaced with your slider value (5-80).

## Requirements

- Chrome browser
- Python environment with reduct installed
- LLM API key (Anthropic, OpenAI, etc.)
