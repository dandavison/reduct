# Reduct

A tool for ingesting information from internet sources and reducing it through AI-powered summarization.

## Quick Start

```bash
# 1. Install
uv sync

# 2. Set up LLM (required)
export LLM_MODEL="anthropic/claude-3-haiku-20240307"
export LLM_KEY="your-api-key"

# 3. Add a source
uv run reduct add-source "https://example.com/article"

# 4. Summarize it (check directory name with 'ls compendia/')
uv run reduct summarize article

# 5. Transform with custom analysis
uv run reduct transform article "Extract key points as bullet list"
```

## Overview

Reduct helps you:
- Extract content from YouTube videos (via transcription) and web articles
- Organize sources in a structured directory format
- Generate AI-powered summaries to reduce information overload
- Track publication dates for rapidly evolving topics (especially useful for AI/ML research)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd reduct

# Install dependencies using uv
uv sync

# Set up environment variables for LLM usage
export LLM_MODEL="anthropic/claude-3-haiku-20240307"  # or "gpt-4o-mini", etc.
export LLM_KEY="your-api-key"  # Or use provider-specific keys:
# export ANTHROPIC_API_KEY="your-anthropic-key"
# export OPENAI_API_KEY="your-openai-key"

# Set output directory (optional, defaults to "compendia")
export REDUCT_OUTPUT_DIRECTORY="/path/to/your/compendia"
```

## Getting Help

```bash
# Main help
uv run reduct --help

# Help for specific commands
uv run reduct summarize --help
uv run reduct add-source --help
uv run reduct transform --help
uv run reduct crawl-site --help
uv run reduct models --help
```

## Directory Structure

Sources are organized in your output directory (default: `compendia/`) with kebab-case subdirectories:

```
compendia/
├── agents/
│   ├── data.yaml          # Metadata (title, URL, dates, etc.)
│   ├── content.md         # Extracted text content
│   ├── summary.md         # AI-generated summary
│   └── transform.md       # Custom transformation output
├── how-to-think-about-agent-frameworks/
│   ├── data.yaml
│   ├── content.md
│   └── summary.md
└── ...
```

## Commands

### Adding Sources

#### Single Source
```bash
# Add a single URL
uv run reduct add-source "https://example.com/article"

# Add with verbose output
uv run reduct add-source "https://example.com/article" --verbose

# Add metadata only (skip content extraction)
uv run reduct add-source "https://example.com/article" --skip-content
```

#### Batch Sources
```bash
# From comma-separated URLs
uv run reduct add-sources-batch "https://url1.com,https://url2.com"

# From file containing URLs (one per line)
uv run reduct add-sources-batch ai_reading_list.txt

# With custom delay between requests
uv run reduct add-sources-batch ai_reading_list.txt --delay 2.0
```

### Transcription

```bash
# Transcribe from YouTube URL
uv run reduct transcribe --transcribe "https://youtube.com/watch?v=..."

# Transcribe from local audio file
uv run reduct transcribe --transcribe "audio.mp3"

# Output to stdout
uv run reduct transcribe --transcribe "https://youtube.com/watch?v=..." --output-file -

# Custom output file
uv run reduct transcribe --transcribe "https://youtube.com/watch?v=..." --output-file "transcript.txt"
```

### Summarization

#### Single Source
```bash
# Summarize a specific source
uv run reduct summarize agents

# Output to stdout
uv run reduct summarize agents --output-file -

# Verbose output
uv run reduct summarize agents --verbose
```

#### Batch Summarization
```bash
# Summarize all sources
uv run reduct summarize-all

# With custom delay between API calls
uv run reduct summarize-all --delay 1.5

# Verbose output
uv run reduct summarize-all --verbose
```

### Transformation

Transform content using custom LLM prompts for specific analysis or reformatting tasks.

```bash
# Extract specific information
uv run reduct transform agents "Extract all technical challenges mentioned"

# Reformat content
uv run reduct transform agents "Rewrite as a bulleted list of key points"

# Analysis
uv run reduct transform agents "Identify and explain all AI/ML concepts mentioned"

# Output to stdout
uv run reduct transform agents "Create a FAQ from this content" --output-file -

# Save to custom file
uv run reduct transform agents "Summarize in 3 paragraphs" --output-file analysis.md

# Verbose output
uv run reduct transform agents "Extract action items" --verbose
```

The transform command saves results to `transform.md` by default, allowing you to keep multiple analysis outputs alongside the original content and summary.

### Status

Check the current state of your sources compendium.

```bash
# Show overview of all sources
uv run reduct status

# See total sources, with/without content, summaries, etc.
uv run reduct status
```

### Website Crawling

Crawl an entire website within a specific domain.

```bash
# Crawl a documentation site
uv run reduct crawl-site "https://modelcontextprotocol.io/introduction"

# Limit crawl depth and pages
uv run reduct crawl-site "https://example.com" --max-depth 2 --max-pages 20

# With custom delay between requests
uv run reduct crawl-site "https://example.com" --delay 3.0

# Skip content extraction (metadata only)
uv run reduct crawl-site "https://example.com" --skip-content

# Verbose output
uv run reduct crawl-site "https://example.com" --verbose
```

Crawled pages are organized in a site-specific subdirectory (e.g., `compendia/example-com/`).

### List Available Models

View all supported LLM models.

```bash
# List all models
uv run reduct models

# Filter by provider
uv run reduct models --provider anthropic
uv run reduct models --provider openai
```

## Supported Models

Set the model using the `LLM_MODEL` environment variable. To see all available models:

```bash
uv run reduct models

# Filter by provider
uv run reduct models --provider anthropic
uv run reduct models --provider openai
```

### Common Models

#### Claude (Anthropic)
- `anthropic/claude-3-haiku-20240307` - Fast and cost-effective
- `anthropic/claude-3-sonnet-20240229` - Balanced performance
- `anthropic/claude-3-opus-20240229` - Most capable
- `anthropic/claude-3-5-sonnet-20241022` - Latest Sonnet

#### OpenAI
- `gpt-4o-mini` - Fast and affordable
- `gpt-4-turbo` - High performance
- `gpt-4` - Most capable GPT-4
- `gpt-3.5-turbo` - Fast, older model

Note: Models with '/' use prefixed names (e.g., 'anthropic/claude-3-sonnet'), others use default provider routing.

## Example Workflow

Here's how to build a knowledge base from a reading list:

```bash
# 1. Set up API keys
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"

# 2. Set the LLM model to use
export LLM_MODEL="anthropic/claude-3-haiku-20240307"
# or export LLM_MODEL="gpt-4o-mini"

# 3. Add sources from a file
uv run reduct add-sources-batch reading_list.txt --verbose

# 4. Generate summaries for all sources
uv run reduct summarize-all --verbose

# 5. Transform specific sources for analysis
uv run reduct transform agents "Extract key challenges and solutions"

# 6. Check results
ls compendia/*/summary.md
ls compendia/agents/transform.md
```

## Features

### Content Extraction
- **YouTube Videos**: Uses `yt-dlp` + `whisper` for audio transcription
- **Web Articles**: Uses `BeautifulSoup` for HTML content extraction
- **Metadata**: Extracts titles, descriptions, publication dates, and more

### Date Tracking
- `published_date`: When the original content was published
- `date_added`: When you captured the content
- Essential for tracking rapidly evolving topics (AI/ML research)

### Error Handling
- Graceful failure for inaccessible sources
- Continues processing remaining sources in batch operations
- Detailed error reporting with emojis

### Respectful Web Scraping
- Configurable delays between requests
- Proper User-Agent headers
- Skips sources that require authentication

## Tips

1. **Use batch processing** for large reading lists
2. **Set appropriate delays** (1-2 seconds) for web scraping
3. **Track publication dates** for time-sensitive research
4. **Use --verbose** for debugging and progress tracking
5. **Use transform for specific analysis** - extract key points, create FAQs, identify patterns
6. **Chain operations** - first summarize, then transform summaries for meta-analysis
7. **Environment variables** - Set `LLM_MODEL` and `REDUCT_OUTPUT_DIRECTORY` in your shell profile

## Next Steps

The system is designed for further "reduction" workflows:
1. Analyze summaries to identify similar content
2. Cluster related sources together
3. Generate consolidated summaries for each cluster
4. Avoid information loss while reducing total bytes

## Dependencies

- `openai-whisper`: Audio transcription
- `yt-dlp`: YouTube video/audio downloading
- `litellm`: Multi-provider LLM access
- `beautifulsoup4`: Web content extraction
- `typer`: CLI interface
- `pyyaml`: Metadata storage
- `python-slugify`: URL-safe directory names
- `python-dateutil`: Date parsing
