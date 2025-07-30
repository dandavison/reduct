import os
import tempfile
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import litellm
import requests
import typer
import whisper
import yaml
import yt_dlp
from bs4 import BeautifulSoup
from slugify import slugify

app = typer.Typer()


def get_output_directory() -> str:
    """Get the output directory from environment variable or default to 'sources'."""
    return os.environ.get("REDUCT_OUTPUT_DIRECTORY", "compendia")


def summarize_content(content: str) -> str:
    """Summarize content using LLM."""
    if "LLM_MODEL" not in os.environ:
        print("Error: Set LLM_MODEL environment variable")
        raise typer.Exit(1)

    model = os.environ["LLM_MODEL"]

    # Get API key - check LLM_KEY first, then fall back to provider-specific keys
    api_key = None
    if "LLM_KEY" in os.environ:
        api_key = os.environ["LLM_KEY"]
    elif model.startswith("anthropic/") and "ANTHROPIC_API_KEY" in os.environ:
        api_key = os.environ["ANTHROPIC_API_KEY"]
    elif (
        model.startswith("openai/") or model.startswith("gpt-")
    ) and "OPENAI_API_KEY" in os.environ:
        api_key = os.environ["OPENAI_API_KEY"]

    if not api_key:
        print(
            "Error: Set LLM_KEY or provider-specific API key (ANTHROPIC_API_KEY, OPENAI_API_KEY)"
        )
        raise typer.Exit(1)

    # Set the appropriate API key for litellm
    if model.startswith("anthropic/"):
        os.environ["ANTHROPIC_API_KEY"] = api_key
    elif model.startswith("openai/") or model.startswith("gpt-"):
        os.environ["OPENAI_API_KEY"] = api_key
    else:
        # For other providers, use the generic API_KEY
        os.environ["API_KEY"] = api_key

    prompt = f"""Provide a concise summary of the following content. Focus on:
1. Main topics and key points
2. Important insights or conclusions
3. Any novel ideas or approaches mentioned
4. Practical applications or implications

Keep the summary to approximately 200-300 words while capturing the essential information.

Content to summarize:
{content}"""

    response = litellm.completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.3,
    )

    return str(response.choices[0].message.content)


def get_sources_list() -> list[Path]:
    """Get list of all source directories."""
    sources_dir = Path(get_output_directory())
    if not sources_dir.exists():
        return []
    return [d for d in sources_dir.iterdir() if d.is_dir()]


def is_url(input_str: str) -> bool:
    """Check if input string is a URL."""
    try:
        result = urllib.parse.urlparse(input_str)
        return all([result.scheme, result.netloc])
    except:
        return False


def get_output_filename(input_source: str, is_url_input: bool) -> str:
    """Generate output filename based on input source."""
    if is_url_input:
        # For URLs, try to get title from yt-dlp
        ydl_opts = {"quiet": True, "no_warnings": True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(input_source, download=False)
                if info:
                    title = info.get("title", "youtube_video")
                    # Clean title for filename
                    title = "".join(
                        c for c in title if c.isalnum() or c in (" ", "-", "_")
                    ).rstrip()
                    title = title.replace(" ", "_")
                    return f"tmp/{title}.txt"
                else:
                    return "tmp/youtube_video.txt"
        except:
            return "tmp/youtube_video.txt"
    else:
        # For files, use the filename
        filename = Path(input_source).stem
        return f"tmp/{filename}.txt"


def transcribe_from_url(url: str, verbose: bool = False) -> str:
    """Download and transcribe from YouTube URL."""
    with tempfile.TemporaryDirectory() as temp_dir:
        audio_path = os.path.join(temp_dir, "audio.%(ext)s")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": audio_path,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "quiet": not verbose,
        }

        if verbose:
            print(f"Downloading audio from: {url}")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        audio_file = os.path.join(temp_dir, "audio.mp3")

        if verbose:
            print("Loading Whisper model...")
        model = whisper.load_model("base")

        if verbose:
            print("Transcribing audio...")
        result = model.transcribe(audio_file, verbose=verbose)

        return str(result["text"])


def transcribe_from_file(filepath: str, verbose: bool = False) -> str:
    """Transcribe from local file."""
    if not os.path.exists(filepath):
        raise typer.BadParameter(f"File not found: {filepath}")

    if verbose:
        print("Loading Whisper model...")
    model = whisper.load_model("base")

    if verbose:
        print(f"Transcribing file: {filepath}")
    result = model.transcribe(filepath, verbose=verbose)

    return str(result["text"])


def create_source_slug(title: str) -> str:
    """Create a kebab-case slug from a title."""
    return slugify(title, lowercase=True, separator="-")


def get_source_info(url: str) -> Dict[str, Any]:
    """Extract source information from URL."""
    if "youtube.com" in url or "youtu.be" in url:
        return get_youtube_info(url)
    else:
        return get_web_info(url)


def get_youtube_info(url: str) -> Dict[str, Any]:
    """Get YouTube video information."""
    ydl_opts = {"quiet": True, "no_warnings": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info:
                upload_date = info.get("upload_date")
                date_added = datetime.now().isoformat()

                # Parse upload_date from YYYYMMDD format
                parsed_date = None
                if upload_date:
                    try:
                        parsed_date = datetime.strptime(
                            upload_date, "%Y%m%d"
                        ).isoformat()
                    except ValueError:
                        pass

                return {
                    "title": info.get("title", "YouTube Video"),
                    "url": url,
                    "type": "video",
                    "duration": info.get("duration"),
                    "description": info.get("description", ""),
                    "channel": info.get("uploader", ""),
                    "published_date": parsed_date,
                    "date_added": date_added,
                }
    except Exception as e:
        print(f"Error extracting YouTube info: {e}")
        return {
            "title": "YouTube Video",
            "url": url,
            "type": "video",
            "error": str(e),
            "date_added": datetime.now().isoformat(),
        }

    return {
        "title": "YouTube Video",
        "url": url,
        "type": "video",
        "date_added": datetime.now().isoformat(),
    }


def get_web_info(url: str) -> Dict[str, Any]:
    """Get web page information."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract title
        title = soup.find("title")
        title_text = title.get_text().strip() if title else "Web Page"

        # Extract description
        description = ""
        desc_tag = soup.find("meta", attrs={"name": "description"})
        if desc_tag:
            description = (
                desc_tag.get("content", "") if hasattr(desc_tag, "get") else ""
            )

        # Try to extract publication date
        published_date = None
        date_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="publish-date"]',
            'meta[name="date"]',
            "time[datetime]",
            ".published-date",
            ".publish-date",
        ]

        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                if hasattr(date_elem, "get"):
                    date_str = date_elem.get("content") or date_elem.get("datetime")
                    if date_str:
                        try:
                            # Try parsing common date formats
                            from dateutil import parser

                            parsed_date = parser.parse(date_str)
                            published_date = parsed_date.isoformat()
                            break
                        except:
                            continue

        return {
            "title": title_text,
            "url": url,
            "type": "article",
            "description": description,
            "published_date": published_date,
            "date_added": datetime.now().isoformat(),
        }
    except Exception as e:
        print(f"Error extracting web info from {url}: {e}")
        return {
            "title": "Web Page",
            "url": url,
            "type": "article",
            "error": str(e),
            "date_added": datetime.now().isoformat(),
        }


def create_source_directory(
    source_info: Dict[str, Any], parent_dir: str | None = None
) -> str:
    """Create source directory and save metadata."""
    if parent_dir is None:
        parent_dir = get_output_directory()
    slug = create_source_slug(source_info["title"])
    source_dir = Path(parent_dir) / slug
    source_dir.mkdir(parents=True, exist_ok=True)

    # Save metadata
    data_file = source_dir / "data.yaml"
    with open(data_file, "w") as f:
        yaml.dump(source_info, f, default_flow_style=False)

    return str(source_dir)


def extract_web_content(url: str) -> str:
    """Extract main content from web page."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Try to find main content
        main_content = soup.find("main") or soup.find("article") or soup.find("body")
        if main_content:
            # Extract text and preserve some structure
            text = main_content.get_text()
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            text = "\n".join(line for line in lines if line)
            return text

        return soup.get_text()
    except Exception as e:
        print(f"Error extracting web content: {e}")
        return f"Error extracting content: {e}"


def _add_single_source(
    url: str,
    verbose: bool = False,
    skip_content: bool = False,
    parent_dir: str | None = None,
) -> bool:
    """Add a single source. Returns True if successful."""
    if parent_dir is None:
        parent_dir = get_output_directory()
    # Ensure parent directory exists
    os.makedirs(parent_dir, exist_ok=True)

    try:
        if verbose:
            print(f"Extracting source info from: {url}")

        # Get source information
        source_info = get_source_info(url)

        if "error" in source_info:
            print(f"⚠️  Failed to extract info from {url}: {source_info['error']}")
            return False

        if verbose:
            print(f"Source title: {source_info['title']}")
            print(f"Source type: {source_info['type']}")

        # Create source directory
        source_dir = create_source_directory(source_info, parent_dir)

        if verbose:
            print(f"Created source directory: {source_dir}")

        # Extract and save content unless skipped
        if not skip_content:
            content_file = Path(source_dir) / "content.md"

            if source_info["type"] == "video":
                if verbose:
                    print("Transcribing video...")
                content = transcribe_from_url(url, verbose)
            else:
                if verbose:
                    print("Extracting web content...")
                content = extract_web_content(url)

            with open(content_file, "w") as f:
                f.write(content)

        print(f"✅ Source added successfully: {source_dir}")
        return True

    except Exception as e:
        print(f"❌ Error processing {url}: {e}")
        return False


@app.command()
def add_source(
    url: str = typer.Argument(..., help="URL to add as a source"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
    skip_content: bool = typer.Option(
        False, "--skip-content", help="Only save metadata, skip content extraction"
    ),
):
    """Add a source URL to the sources directory."""

    success = _add_single_source(url, verbose, skip_content)
    if not success:
        raise typer.Exit(1)


@app.command()
def add_sources_batch(
    urls: str = typer.Argument(
        ..., help="Comma-separated URLs or file path containing URLs"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
    skip_content: bool = typer.Option(
        False, "--skip-content", help="Only save metadata, skip content extraction"
    ),
    delay: float = typer.Option(
        1.0, "--delay", help="Delay between requests in seconds"
    ),
):
    """Add multiple source URLs from a comma-separated list or file."""

    # Parse URLs
    url_list = []
    if os.path.exists(urls):
        # Read from file
        with open(urls, "r") as f:
            url_list = [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]
        print(f"📁 Loaded {len(url_list)} URLs from file: {urls}")
    else:
        # Parse comma-separated
        url_list = [url.strip() for url in urls.split(",") if url.strip()]
        print(f"📝 Processing {len(url_list)} URLs from command line")

    if not url_list:
        print("No URLs found to process")
        return

    # Process each URL
    successful = 0
    failed = 0

    for i, url in enumerate(url_list, 1):
        print(f"\n[{i}/{len(url_list)}] Processing: {url}")

        success = _add_single_source(url, verbose, skip_content)
        if success:
            successful += 1
        else:
            failed += 1

        # Add delay between requests to be respectful
        if i < len(url_list) and delay > 0:
            if verbose:
                print(f"Waiting {delay} seconds...")
            import time

            time.sleep(delay)

    print(
        f"\n📊 Summary: {successful} successful, {failed} failed out of {len(url_list)} total"
    )


@app.command()
def transcribe(
    source: str = typer.Option(
        ..., "--transcribe", "-t", help="YouTube URL or local file path to transcribe"
    ),
    output_file: str = typer.Option(
        None, "--output-file", "-o", help="Output file path (use '-' for stdout)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """Transcribe audio from YouTube URL or local file."""

    # Ensure tmp directory exists
    os.makedirs("tmp", exist_ok=True)

    try:
        if is_url(source):
            if verbose:
                print(f"Detected URL input: {source}")
            transcript = transcribe_from_url(source, verbose)
        else:
            if verbose:
                print(f"Detected file input: {source}")
            transcript = transcribe_from_file(source, verbose)

            # Save transcript
        if output_file == "-":
            print(transcript)
        else:
            if output_file is None:
                output_path = get_output_filename(source, is_url(source))
            else:
                output_path = output_file

            with open(output_path, "w") as f:
                f.write(transcript)

            print(f"Transcript saved to: {output_path}")

    except Exception as e:
        print(f"Error: {e}")
        raise typer.Exit(1)


@app.command()
def summarize(
    source: str = typer.Argument(..., help="Source directory path to summarize"),
    output_file: str = typer.Option(
        None, "--output-file", "-o", help="Output file path (use '-' for stdout)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """Summarize content from a specific source."""

    source_dir = Path(source)

    if not source_dir.exists():
        print(f"Source directory not found: {source_dir}")
        raise typer.Exit(1)

    content_file = source_dir / "content.md"
    if not content_file.exists():
        print(f"Content file not found: {content_file}")
        raise typer.Exit(1)

    if verbose:
        print(f"Reading content from: {content_file}")

    with open(content_file, "r") as f:
        content = f.read()

    if verbose:
        print(f"Content length: {len(content)} characters")
        print(f"Using model: {os.environ.get('LLM_MODEL', 'not set')}")

    summary = summarize_content(content)

    if output_file == "-":
        print(summary)
    else:
        if output_file is None:
            output_path = source_dir / "summary.md"
        else:
            output_path = Path(output_file)

        with open(output_path, "w") as f:
            f.write(summary)

        print(f"Summary saved to: {output_path}")


@app.command()
def summarize_all(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
    delay: float = typer.Option(
        1.0, "--delay", help="Delay between API calls in seconds"
    ),
):
    """Summarize content from all sources."""

    sources = get_sources_list()
    if not sources:
        print(f"No sources found in {get_output_directory()}/ directory")
        return

    print(f"Found {len(sources)} sources to summarize")

    successful = 0
    failed = 0

    for i, source_dir in enumerate(sources, 1):
        print(f"\n[{i}/{len(sources)}] Processing: {source_dir.name}")

        content_file = source_dir / "content.md"
        if not content_file.exists():
            print(f"⚠️  Content file not found: {content_file}")
            failed += 1
            continue

        summary_file = source_dir / "summary.md"
        if summary_file.exists():
            if verbose:
                print("Summary already exists, skipping...")
            continue

        try:
            if verbose:
                print(f"Reading content from: {content_file}")

            with open(content_file, "r") as f:
                content = f.read()

            if verbose:
                print(f"Content length: {len(content)} characters")
                print(f"Using model: {os.environ.get('LLM_MODEL', 'not set')}")

            summary = summarize_content(content)

            with open(summary_file, "w") as f:
                f.write(summary)

            print(f"✅ Summary saved to: {summary_file}")
            successful += 1

        except Exception as e:
            print(f"❌ Error processing {source_dir.name}: {e}")
            failed += 1

        # Add delay between API calls
        if i < len(sources) and delay > 0:
            if verbose:
                print(f"Waiting {delay} seconds...")
            time.sleep(delay)

    print(
        f"\n📊 Summary: {successful} successful, {failed} failed out of {len(sources)} total"
    )


@app.command()
def status(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed information for each source"
    ),
):
    """Show the current state of the sources compendium."""

    sources = get_sources_list()
    if not sources:
        print("📂 No sources found in the compendium.")
        return

    # Collect statistics
    total_sources = len(sources)
    sources_with_content = 0
    sources_with_summaries = 0
    source_details = []

    for source_dir in sources:
        data_file = source_dir / "data.yaml"
        content_file = source_dir / "content.md"
        summary_file = source_dir / "summary.md"

        has_content = content_file.exists()
        has_summary = summary_file.exists()

        if has_content:
            sources_with_content += 1
        if has_summary:
            sources_with_summaries += 1

        # Load metadata
        metadata = {}
        if data_file.exists():
            try:
                with open(data_file, "r") as f:
                    metadata = yaml.safe_load(f)
            except Exception:
                pass

        source_details.append(
            {
                "name": source_dir.name,
                "metadata": metadata,
                "has_content": has_content,
                "has_summary": has_summary,
                "content_size": content_file.stat().st_size if has_content else 0,
            }
        )

    # Sort by date_added (most recent first)
    source_details.sort(key=lambda x: x["metadata"].get("date_added", ""), reverse=True)

    # Print summary statistics
    print("📊 Compendium Status")
    print(f"   Total sources: {total_sources}")
    print(f"   Sources with content: {sources_with_content}")
    print(f"   Sources with summaries: {sources_with_summaries}")
    print(
        f"   Completion rate: {sources_with_summaries}/{sources_with_content} ({100 * sources_with_summaries / max(sources_with_content, 1):.0f}%)"
    )
    print()

    if verbose:
        # Show detailed source information
        print("📋 Source Details:")
        for detail in source_details:
            metadata = detail["metadata"]
            title = metadata.get("title", detail["name"])
            url = metadata.get("url", "No URL")
            date_added = metadata.get("date_added", "Unknown")

            # Status indicators
            content_status = "✅" if detail["has_content"] else "❌"
            summary_status = "✅" if detail["has_summary"] else "❌"

            print(f"  {title}")
            print(f"    📁 {detail['name']}")
            print(f"    🔗 {url}")
            print(f"    📅 Added: {date_added}")
            print(f"    📄 Content: {content_status} Summary: {summary_status}")
            if detail["has_content"]:
                size_kb = detail["content_size"] / 1024
                print(f"    📏 Content size: {size_kb:.1f}KB")
            print()
    else:
        # Show condensed list
        print("📋 Sources (most recent first):")
        for detail in source_details:
            metadata = detail["metadata"]
            title = metadata.get("title", detail["name"])
            content_status = "📄" if detail["has_content"] else "❌"
            summary_status = "📝" if detail["has_summary"] else "❌"
            print(f"  {content_status}{summary_status} {title}")


@app.command()
def models(
    provider: str = typer.Option(
        None,
        "--provider",
        "-p",
        help="Filter by provider (anthropic, openai, google, etc.)",
    ),
):
    """List available LLM models."""
    try:
        import litellm

        # Get model cost map which contains model info
        model_cost_map = litellm.model_cost

        if not model_cost_map:
            print("No model information available")
            return

        # Group models by provider
        providers = {}
        for model_name in model_cost_map.keys():
            if "/" in model_name:
                provider_name = model_name.split("/")[0]
            else:
                # For models without explicit provider prefix
                if model_name.startswith("gpt-") or model_name.startswith("o1-"):
                    provider_name = "openai"
                elif model_name.startswith("claude-"):
                    provider_name = "anthropic"
                elif model_name.startswith("gemini-"):
                    provider_name = "google"
                else:
                    provider_name = "other"

            if provider_name not in providers:
                providers[provider_name] = []
            providers[provider_name].append(model_name)

        # Filter by provider if specified
        if provider:
            providers = {
                k: v for k, v in providers.items() if k.lower() == provider.lower()
            }
            if not providers:
                print(f"No models found for provider: {provider}")
                return

        # Display models grouped by provider
        for provider_name in sorted(providers.keys()):
            print(f"\n{provider_name.upper()} MODELS:")
            for model in sorted(providers[provider_name]):
                print(f"  {model}")

        print(
            f"\nTotal: {sum(len(models) for models in providers.values())} models across {len(providers)} providers"
        )
        print("\nUsage: Set LLM_MODEL=<model_name> and LLM_KEY=<api_key>")
        print(
            "Note: Model names with '/' are prefixed (e.g., 'anthropic/claude-3-sonnet'), others use default provider routing"
        )

    except ImportError:
        print("Error: litellm not available")
        raise typer.Exit(1)
    except Exception as e:
        print(f"Error listing models: {e}")
        raise typer.Exit(1)


@app.command()
def crawl_site(
    url: str = typer.Argument(..., help="Starting URL to crawl"),
    max_depth: int = typer.Option(3, "--max-depth", "-d", help="Maximum crawl depth"),
    max_pages: int = typer.Option(
        50, "--max-pages", "-p", help="Maximum number of pages to crawl"
    ),
    delay: float = typer.Option(
        2.0, "--delay", help="Delay between requests in seconds"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
    skip_content: bool = typer.Option(
        False, "--skip-content", help="Only save metadata, skip content extraction"
    ),
):
    """Crawl a website staying within the same domain."""

    import re
    from urllib.parse import urljoin, urlparse

    # Parse the starting URL to get the domain
    parsed_start = urlparse(url)
    base_domain = parsed_start.netloc

    # Create site-specific directory
    site_slug = slugify(base_domain)
    site_dir = Path(get_output_directory()) / site_slug
    site_dir.mkdir(parents=True, exist_ok=True)

    print(f"🕷️  Starting crawl of {base_domain}")
    print(f"   Target directory: {site_dir}")
    print(f"   Max depth: {max_depth}")
    print(f"   Max pages: {max_pages}")
    print(f"   Delay: {delay}s between requests")

    # Track visited URLs and queue
    visited = set()
    queue = [(url, 0)]  # (url, depth)
    crawled_count = 0

    while queue and crawled_count < max_pages:
        current_url, depth = queue.pop(0)

        # Skip if already visited or depth exceeded
        if current_url in visited or depth > max_depth:
            continue

        visited.add(current_url)
        crawled_count += 1

        print(f"\n[{crawled_count}/{max_pages}] Depth {depth}: {current_url}")

        try:
            # Add the current page as a source
            if verbose:
                print("  Adding source...")

            success = _add_single_source(
                current_url,
                verbose=False,
                skip_content=skip_content,
                parent_dir=str(site_dir),
            )
            if not success:
                print("  ⚠️  Failed to add source")
                continue

            # Only extract links if we haven't reached max depth
            if depth < max_depth:
                if verbose:
                    print("  Extracting links...")

                # Get the page content to extract links
                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                }
                response = requests.get(current_url, timeout=15, headers=headers)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "html.parser")

                # Find all links
                links = soup.find_all("a", href=True)
                new_links = []

                for link in links:
                    try:
                        # Access href attribute directly from BeautifulSoup tag
                        href = getattr(link, "attrs", {}).get("href")
                        if not href or not isinstance(href, str):
                            continue
                    except (AttributeError, KeyError):
                        continue
                    # Convert relative URLs to absolute
                    absolute_url = urljoin(current_url, href)
                    parsed_link = urlparse(absolute_url)

                    # Only follow links within the same domain
                    if (
                        parsed_link.netloc == base_domain
                        and absolute_url not in visited
                        and absolute_url not in [q[0] for q in queue]
                    ):
                        # Skip common non-content links
                        if not any(
                            skip_pattern in absolute_url.lower()
                            for skip_pattern in [
                                "#",
                                "javascript:",
                                "mailto:",
                                "tel:",
                                ".pdf",
                                ".zip",
                                ".png",
                                ".jpg",
                                ".gif",
                            ]
                        ):
                            new_links.append(absolute_url)

                # Add new links to queue
                for new_url in new_links:
                    queue.append((new_url, depth + 1))

                if verbose:
                    print(f"  Found {len(new_links)} new links to crawl")

        except Exception as e:
            print(f"  ❌ Error crawling {current_url}: {e}")

        # Add delay between requests
        if queue and delay > 0:
            if verbose:
                print(f"  Waiting {delay} seconds...")
            time.sleep(delay)

    print("\n✅ Crawl completed!")
    print(f"   Pages crawled: {crawled_count}")
    print(f"   Pages discovered but not crawled: {len(queue)}")
    print("   Use 'reduct status' to see the added sources")


def main() -> None:
    app()
