from pathlib import Path
import os
import json

from dotenv import load_dotenv
from openai import OpenAI
from pydub import AudioSegment


# Project paths
PROJECT_DIR = Path(__file__).resolve().parent
AUDIO_DIR = PROJECT_DIR / "audio"
OUTPUT_DIR = PROJECT_DIR / "outputs"
CHUNK_DIR = AUDIO_DIR / "chunks"


def setup_environment():
    """Load API credentials and prepare output folders."""

    load_dotenv(PROJECT_DIR / ".env")

    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY not found in .env")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHUNK_DIR.mkdir(parents=True, exist_ok=True)

    return OpenAI()


#basic transcription function:

def transcribe_audio(client, audio_path, prompt=None):
    """Transcribe an audio file using OpenAI Whisper."""

    with open(audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            prompt=prompt
        )

    return transcription.text


#audio chunking function:

def split_audio(audio_path, chunk_length_ms=60000):
    """Split audio into chunks and retain their original positions."""

    audio = AudioSegment.from_file(audio_path)
    chunks = []

    for start_ms in range(0, len(audio), chunk_length_ms):
        end_ms = min(start_ms + chunk_length_ms, len(audio))

        chunks.append({
            "audio": audio[start_ms:end_ms],
            "start_ms": start_ms,
            "end_ms": end_ms
        })

    return chunks

#Save audio chunks as MP3 files:

def export_chunks(chunks, chunk_dir):
    """Save audio chunks as MP3 files."""

    chunk_dir.mkdir(parents=True, exist_ok=True)

    for i, chunk in enumerate(chunks, start=1):
        chunk_path = chunk_dir / f"chunk_{i:02d}.mp3"

        chunk["audio"].export(
            chunk_path,
            format="mp3"
        )

        chunk["path"] = chunk_path

    return chunks

#Timestamped chunk transcription

def transcribe_chunks_with_timestamps(chunks, client):
    """Transcribe chunks and convert timestamps to the original audio timeline."""

    all_segments = []

    for i, chunk in enumerate(chunks, start=1):
        with open(chunk["path"], "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )

        if result.segments is None:
            raise ValueError(f"No timestamps returned for chunk {i}")

        offset_seconds = chunk["start_ms"] / 1000

        for segment in result.segments:
            all_segments.append({
                "chunk": i,
                "start": round(segment.start + offset_seconds, 2),
                "end": round(segment.end + offset_seconds, 2),
                "text": segment.text.strip()
            })

        print(f"Chunk {i}: timestamps extracted.")

    return all_segments

#export functions

#This function takes the timestamped segments, combines their text, and saves it to a file:
def export_txt(segments, output_path):
    """Export transcription as plain text."""

    text = " ".join(segment["text"] for segment in segments)

    output_path.write_text(text, encoding="utf-8")

#Export SRT:

def format_srt_time(seconds):
    """Convert seconds to SRT timestamp format."""

    total_ms = round(seconds * 1000)

    hours, remainder = divmod(total_ms, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    secs, milliseconds = divmod(remainder, 1000)

    return (
        f"{hours:02d}:{minutes:02d}:"
        f"{secs:02d},{milliseconds:03d}"
    )

def export_srt(segments, output_path):
    """Export timestamped segments as SRT subtitles."""

    blocks = []

    for i, segment in enumerate(segments, start=1):
        start = format_srt_time(segment["start"])
        end = format_srt_time(segment["end"])

        blocks.append(
            f"{i}\n"
            f"{start} --> {end}\n"
            f"{segment['text']}"
        )

    output_path.write_text(
        "\n\n".join(blocks) + "\n",
        encoding="utf-8"
    )

#Export JSON:

def export_json(segments, output_path, source_file):
    """Export structured transcription data."""

    data = {
        "source_file": source_file,
        "model": "whisper-1",
        "segment_count": len(segments),
        "segments": segments
    }

    output_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


#Connect everything with main()

def main():
    """Run the complete Whisper transcription workflow."""

    # 1. Initialize the environment
    client = setup_environment()
    audio_path = AUDIO_DIR / "project_nimbus_meeting.mp3"

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # 2. Transcribe without contextual prompting
    unguided_text = transcribe_audio(client, audio_path)

    (OUTPUT_DIR / "unguided_transcription.txt").write_text(
        unguided_text,
        encoding="utf-8"
    )

    # 3. Transcribe with contextual prompting
    context_prompt = (
        "Technical vocabulary: Project Nimbus, Kubernetes, "
        "Amazon EKS, PostgreSQL, Redis, Q3 OKRs."
    )

    guided_text = transcribe_audio(
        client,
        audio_path,
        prompt=context_prompt
    )

    (OUTPUT_DIR / "guided_transcription.txt").write_text(
        guided_text,
        encoding="utf-8"
    )

    # 4. Split the audio and save the chunks
    chunks = split_audio(audio_path)
    chunks = export_chunks(chunks, CHUNK_DIR)

    print(f"Created {len(chunks)} audio chunks.")

    # 5. Transcribe chunks with timestamps
    segments = transcribe_chunks_with_timestamps(chunks, client)

    # 6. Export the results
    export_txt(
        segments,
        OUTPUT_DIR / "meeting_transcription.txt"
    )

    export_srt(
        segments,
        OUTPUT_DIR / "meeting_subtitles.srt"
    )

    export_json(
        segments,
        OUTPUT_DIR / "meeting_transcription.json",
        audio_path.name
    )

    print("All transcription files exported successfully.")


if __name__ == "__main__":
    main()