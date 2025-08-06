*This project is experimental, LLM-generated, and comes with zero recommendations / guarantees.*

# Reduct

A tool for ingesting and reducing information from internet sources.

## Quick Start

```bash
# 1. Install
uv sync

# 2. Set up LLM (required)
export LLM_MODEL="anthropic/claude-3-haiku-20240307"
export LLM_KEY="your-api-key"

# 3. Add a source
uv run reduct add-source "https://example.com/article"

# 4. Summarize it
uv run reduct summarize article

# 5. Transform with custom analysis
uv run reduct transform "Extract key points" --source article

# 6. Or pipe commands together
uv run reduct transcribe "https://youtube.com/watch?v=..." | \
  uv run reduct transform "Create a clean summary"
```

## Help

Always use `--help` for detailed information about each command:

```bash
uv run reduct --help
uv run reduct add-source --help
uv run reduct transcribe --help
# etc.
```

## Commands

### Adding Sources

```bash
# Single URL
uv run reduct add-source "https://example.com/article"

# Multiple URLs from file or comma-separated list
uv run reduct add-sources-batch urls.txt
uv run reduct add-sources-batch "https://url1.com,https://url2.com"

# Options
--verbose              # Show detailed output
--skip-content         # Only save metadata
--delay 2.0           # Delay between requests (batch only)
```

### Transcription

```bash
# YouTube URL or local audio file
uv run reduct transcribe "https://youtube.com/watch?v=..."
uv run reduct transcribe "audio.mp3"

# Options
--output-file FILE    # Save to file instead of stdout
--verbose             # Show detailed output
```

### Summarization

```bash
# Single source
uv run reduct summarize path/to/source

# All sources
uv run reduct summarize-all

# Options
--output-file FILE    # Save to file instead of default location
--delay 1.0          # Delay between API calls (summarize-all)
--verbose            # Show detailed output
```

### Transformation

```bash
# From stdin (default) or source directory
uv run reduct transform "Your custom prompt here"
uv run reduct transform "Extract action items" --source path/to/source

# Options
--source PATH        # Source directory (default: stdin)
--output-file FILE   # Output file (default: stdout)
--verbose           # Show detailed output
```

### Website Crawling

```bash
# Crawl within domain
uv run reduct crawl-site "https://example.com"

# Options
--max-depth 3        # Maximum crawl depth
--max-pages 50       # Maximum pages to crawl
--delay 2.0         # Delay between requests
--skip-content      # Only save metadata
--verbose           # Show detailed output
```

### Other Commands

```bash
# Show compendium status
uv run reduct status

# List available LLM models
uv run reduct models
uv run reduct models --provider anthropic
```

## Directory Structure

```
$REDUCT_OUTPUT_DIRECTORY/  # Default: "compendia"
├── site-name/
│   └── page-title/
│       ├── data.yaml      # Metadata
│       ├── content.md     # Extracted text
│       ├── summary.md     # AI summary
│       └── transform.md   # Custom transformations
└── ...
```

## Environment Variables

- `LLM_MODEL`: Model to use (e.g., "anthropic/claude-3-haiku-20240307")
- `LLM_KEY`: API key for the selected provider
- `REDUCT_OUTPUT_DIRECTORY`: Where to store sources (default: "compendia")

Provider-specific keys also work:
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`

## Common Workflows

```bash
# Process a reading list
uv run reduct add-sources-batch reading_list.txt
uv run reduct summarize-all

# Transcribe and clean up
uv run reduct transcribe "https://youtube.com/watch?v=..." | \
  uv run reduct transform "Clean up transcript, fix errors"

# Crawl documentation site
uv run reduct crawl-site "https://docs.example.com" --max-depth 2
uv run reduct summarize-all

# Analyze specific topics
uv run reduct transform "What does this say about X?" --source article
```