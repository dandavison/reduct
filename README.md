# Reduct

A tool for ingesting information from internet sources and reducing it through AI-powered summarization.

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

# Set up API keys (required for summarization)
export ANTHROPIC_API_KEY="your-anthropic-key"
export OPENAI_API_KEY="your-openai-key"
```

## Getting Help

```bash
# Main help
uv run reduct --help

# Help for specific commands
uv run reduct summarize --help
uv run reduct add-source --help
```

## Directory Structure

Sources are organized in `sources/` with kebab-case subdirectories:

```
sources/
├── agents/
│   ├── data.yaml          # Metadata (title, URL, dates, etc.)
│   ├── content.md         # Extracted text content
│   └── summary.md         # AI-generated summary
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
# Summarize a specific source (uses Claude by default)
uv run reduct summarize agents

# Use OpenAI GPT-4
uv run reduct summarize agents --model gpt-4o-mini

# Output to stdout
uv run reduct summarize agents --output-file -

# Verbose output
uv run reduct summarize agents --verbose
```

#### Batch Summarization
```bash
# Summarize all sources
uv run reduct summarize-all

# Use specific model
uv run reduct summarize-all --model claude-3-haiku-20240307

# With custom delay between API calls
uv run reduct summarize-all --delay 1.5

# Verbose output
uv run reduct summarize-all --verbose
```

## Supported Models

### Claude (Anthropic)
- `claude-3-haiku-20240307` (default)
- `claude-3-sonnet-20240229`
- `claude-3-opus-20240229`

### OpenAI
- `gpt-4o-mini`
- `gpt-4-turbo`
- `gpt-4`
- `gpt-3.5-turbo`

## Example Workflow

Here's how to build a knowledge base from a reading list:

```bash
# 1. Set up API keys
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"

# 2. Add sources from a file
uv run reduct add-sources-batch reading_list.txt --verbose

# 3. Generate summaries for all sources
uv run reduct summarize-all --verbose

# 4. Check results
ls sources/*/summary.md
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
5. **Mix models** (Claude for analysis, GPT for different perspectives)

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
