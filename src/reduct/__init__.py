import os
import tempfile
import urllib.parse
from pathlib import Path

import typer
import whisper
import yt_dlp

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
