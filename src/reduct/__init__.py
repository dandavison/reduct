import os
import tempfile
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import requests
import typer
import whisper
import yaml
import yt_dlp
from bs4 import BeautifulSoup
from slugify import slugify

app = typer.Typer()


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


def create_source_directory(source_info: Dict[str, Any]) -> str:
    """Create source directory and save metadata."""
    slug = create_source_slug(source_info["title"])
    source_dir = Path("sources") / slug
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
    url: str, verbose: bool = False, skip_content: bool = False
) -> bool:
    """Add a single source. Returns True if successful."""
    # Ensure sources directory exists
    os.makedirs("sources", exist_ok=True)

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
        source_dir = create_source_directory(source_info)

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


def main() -> None:
    app()
