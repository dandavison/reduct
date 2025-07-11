import os
import tempfile
from dataclasses import dataclass

import whisper
import yt_dlp


@dataclass
class Source:
    url: str
    name: str


sources = [
    Source(
        url="https://www.youtube.com/watch?v=LCEmiRjPEtQ",
        name="Andrej Karpathy: Software Is Changing (Again)",
    ),
]


def create_transcript(source: Source) -> None:
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
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([source.url])

        audio_file = os.path.join(temp_dir, "audio.mp3")
        model = whisper.load_model("base")
        result = model.transcribe(audio_file)

        transcript_filename = f"{source.name.replace(' ', '_').replace(':', '')}.txt"
        with open(transcript_filename, "w") as f:
            f.write(str(result["text"]))

        print(f"Transcript saved to {transcript_filename}")


def main() -> None:
    for source in sources:
        create_transcript(source)
