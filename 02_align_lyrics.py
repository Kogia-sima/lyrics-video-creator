import argparse
import json
import os
import uuid
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from musicai_sdk import MusicAiClient


class MusicAiJobRunner:
    """A class to run a job using the MusicAI API."""

    def __init__(self, api_key: str, job_monitor_interval: int = 2):
        self.client = MusicAiClient(
            api_key=api_key, job_monitor_interval=job_monitor_interval
        )

    def get_application_info(self) -> dict:
        """
        Gets application info from the MusicAI API.
        """
        app_info = self.client.get_application_info()
        return app_info

    def upload_file(self, file_path: str | Path) -> str:
        """
        Uploads a file to the MusicAI API.
        """
        file_url = self.client.upload_file(file_path)
        print("File Uploaded:", file_url)
        return file_url

    def run_job(self, workflow_slug: str, workflow_params: dict[str, Any]) -> dict:
        """
        Runs a job using the MusicAI API.
        """
        # Create a job for the workflow
        create_job_info = self.client.create_job(
            job_name=str(uuid.uuid4()),
            workflow_id=workflow_slug,
            params=workflow_params,
        )
        job_id = create_job_info["id"]
        print("Job Created:", job_id)

        # Wait for the job to complete
        job_info = self.client.wait_for_job_completion(job_id)

        # Get job info
        job_info = self.client.get_job(job_id=job_id)
        print("Job Result:", job_info["result"])

        return job_info["result"]


def convert_lyrics_to_json(lyrics: str) -> list[dict]:
    """
    Converts lyrics to JSON format.
    """
    lyrics_lines = [line.strip() for line in lyrics.splitlines()]
    lyrics_lines = [line for line in lyrics_lines if line]
    return [{"text": line, "language": "japanese"} for line in lyrics_lines]


def align_lyrics(workflow_slug: str, music_file: Path, lyrics: str) -> list[dict]:
    """
    Aligns lyrics to music using the MusicAI API.
    """
    # Initialize the MusicAI client
    musicai = MusicAiJobRunner(api_key=os.environ["MUSICAI_API_KEY"])

    # Get application info
    app_info = musicai.get_application_info()
    print("MusicAI Application Info:", app_info)

    with NamedTemporaryFile(suffix=".json") as temp_lyrics_file:
        # convert the lyrics to json
        lyrics_json = convert_lyrics_to_json(lyrics)
        temp_lyrics_file.write(
            json.dumps(lyrics_json, ensure_ascii=False).encode("utf-8")
        )
        temp_lyrics_file.flush()

        # Upload the files
        music_url = musicai.upload_file(music_file)
        lyrics_url = musicai.upload_file(temp_lyrics_file.name)

    # Define workflow parameters
    workflow_params = {
        "musicUrl": music_url,
        "lyricsUrl": lyrics_url,
    }

    # Create a job for the workflow
    job_result = musicai.run_job(workflow_slug, workflow_params)

    aligned_lyrics = json.loads(job_result["aligned_lyrics"])
    return aligned_lyrics


def correct_lyrics_timing(
    original_lyrics: str, aligned_lyrics: list[dict]
) -> list[dict]:
    """
    Corrects the timing of the aligned lyrics based on the original lyrics.
    """
    # Format the original lyrics as JSON
    original_lyrics_json = convert_lyrics_to_json(original_lyrics)

    for i in range(len(aligned_lyrics) - 1):
        # Replace the text in the aligned lyrics with the original lyrics
        aligned_lyrics[i]["text"] = original_lyrics_json[i]["text"]
        # Fix the start and end times of the aligned lyrics
        aligned_lyrics[i]["end"] = min(
            aligned_lyrics[i]["end"] + 1.0, aligned_lyrics[i + 1]["start"]
        )
    return aligned_lyrics


def main():
    parser = argparse.ArgumentParser(description="Align lyrics to music using MusicAI.")
    parser.add_argument("music_file", type=Path, help="Path to the music file.")
    parser.add_argument("lyrics_file", type=Path, help="Path to the lyrics file.")
    parser.add_argument(
        "--workflow_slug",
        type=str,
        default="subtitle-transcription-and-alignment",
        help="Workflow slug for the MusicAI API.",
    )
    args = parser.parse_args()

    # Read the lyrics from the file
    with args.lyrics_file.open(encoding="utf-8") as f:
        lyrics = f.read()

    # Align the lyrics
    aligned_lyrics = align_lyrics(args.workflow_slug, args.music_file, lyrics)

    # Save the aligned lyrics to a new JSON file
    output_file = Path(args.lyrics_file).parent / (
        Path(args.lyrics_file).stem + "_aligned.json"
    )
    output_file.write_text(
        json.dumps(aligned_lyrics, indent=2, ensure_ascii=False), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
