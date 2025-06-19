import copy
import json
import logging  # ...new import...
import os
import uuid
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

# Import LangChain and OpenAI related libraries
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from moviepy import AudioFileClip, CompositeVideoClip, ImageClip, TextClip, vfx
from musicai_sdk import MusicAiClient

from lyrics_video_creator.font import get_font_path

logger = logging.getLogger(__name__)


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
        logger.info("File Uploaded: %s", file_url)
        return file_url

    def run_job(self, workflow_slug: str, workflow_params: dict[str, Any]) -> dict:
        """
        Runs a job using the MusicAI API.
        """
        # Create a job for the workflow
        create_job_info = self.client.add_job(
            job_name=str(uuid.uuid4()),
            workflow_slug=workflow_slug,
            params=workflow_params,
        )
        job_id = create_job_info["id"]
        logger.info("Job Created: %s", job_id)

        # Wait for the job to complete
        job_info = self.client.wait_for_job_completion(job_id)

        # Get job info
        job_info = self.client.get_job(job_id=job_id)
        logger.info("Job Result: %s", job_info["result"])
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
    # test
    lyrics_json = convert_lyrics_to_json(lyrics)
    for i, lyric in enumerate(lyrics_json):
        lyric["start"] = i * 4
        lyric["end"] = i * 4 + 1

    return lyrics_json

    # Initialize the MusicAI client
    musicai = MusicAiJobRunner(api_key=os.environ["MUSICAI_API_KEY"])

    # Get application info
    app_info = musicai.get_application_info()
    logger.info("MusicAI Application Info: %s", app_info)

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


def translate_lyrics(lyrics: list[dict]) -> list[dict]:
    """
    Reads a Japanese lyrics JSON file, translates it into English, and saves it to a new JSON file.

    Args:
        input_file_path (str): Path to the input JSON file.
        output_file_path (str): Path to the output JSON file.
    """
    # Check OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key is None:
        raise RuntimeError(
            "Error: Environment variable OPENAI_API_KEY is not set. "
            "Please set OPENAI_API_KEY before running the script."
            "Example: export OPENAI_API_KEY='your_api_key_here'"
        )

    # Check input data format
    if not isinstance(lyrics, list):
        logger.error(
            "Error: The content of input file '%s' must be a list.", input_file_path
        )
        return
    if not all(
        isinstance(item, dict) and "text" in item and "start" in item and "end" in item
        for item in lyrics
    ):
        raise RuntimeError(
            "Error: Each element in the input file must be a dictionary with 'text', 'start', and 'end' keys."
        )

    japanese_texts = [item["text"] for item in lyrics]
    num_original_lines = len(japanese_texts)
    japanese_lyrics_block = "\n".join(japanese_texts)

    # Create prompt
    # Hint: Include the entire lyrics in the prompt and specify the output format in the prompt
    #       to make it easier to extract the English lyrics accurately.
    prompt_template_str = """\
以下の日本語の歌詞を英語に翻訳してください。
各行の翻訳は改行で区切って、元の歌詞の行数と全く同じ数の翻訳行を生成してください。
翻訳は自然で、歌詞としての流れを意識してください。

# 歌詞

<lyrics>
{lyrics}
</lyrics>

# 条件

* もとの歌詞の意味合いと雰囲気を可能な限り維持してください
* 翻訳された各行は、元の日本語の歌詞の各行に厳密に対応する必要があります。
* 空の行や不必要な空白行を生成しないでください。元の行数と完全に一致させてください。
* もとの歌詞と翻訳結果以外は一切出力しないでください。
* 前置き、後書き、元の日本語歌詞、追加のコメントや説明は一切含めないでください。
* 下記の出力形式に厳密に従ってください。

# 出力形式

```
[日本語歌詞の1行目],[1行目の翻訳結果]
[日本語歌詞の2行目],[2行目の翻訳結果]
(以降同様に続く)
```
"""

    current_temperature = 0.0
    # Hint: If the output does not follow the instructions, increase the value of temperature by 0.2
    #       and retry translation until the correct result is obtained.
    #       Here, try up to a maximum of 1.0.
    max_temperature = 1.0
    temperature_step = 0.2
    translated_lines_list: list[str] = []

    logger.info("Starting translation. Number of input lines: %d", len(japanese_texts))

    # Translation using ChatOpenAI (including retry logic)
    while current_temperature <= max_temperature:
        logger.debug(
            "  Trying translation with temperature %.1f...", current_temperature
        )

        # Initialize ChatOpenAI
        # Condition: Set temperature parameter of ChatOpenAI to 0 and seed to 42.
        # (First try with temperature=0, increase temperature on retry)
        chat_model = ChatOpenAI(
            temperature=current_temperature,
            name="gpt-4.1-mini",
            timeout=120,  # Set a longer timeout
            seed=42,  # Seed value to improve reproducibility of model output
        )

        prompt = ChatPromptTemplate.from_template(prompt_template_str)
        chain = prompt | chat_model | StrOutputParser()

        # To maintain consistency of lyrics, call ChatOpenAI once for the whole lyrics, not line by line
        response_text = chain.invoke({"lyrics": japanese_lyrics_block})
        response_text = response_text.replace("```", "")

        # Parse and validate translation result
        # Remove leading/trailing whitespace/newlines with strip(), then split by newline
        potential_translations = response_text.strip().split("\n")
        # Further strip each line
        potential_translations = [line.strip() for line in potential_translations]
        # Skip empty lines
        potential_translations = [line for line in potential_translations if line]
        # Split each line by comma and extract the translation part
        potential_translations = [
            ",".join(line.split(",")[1:]).strip() for line in potential_translations
        ]

        # If the number of lines matches, break the loop
        if len(potential_translations) == num_original_lines:
            translated_lines_list = potential_translations
            break

        # If the number of lines does not match, increase temperature and retry
        logger.debug(
            "  The number of translation lines (%.1f) did not match. Expected: %d, Actual: %d",
            current_temperature,
            num_original_lines,
            len(potential_translations),
        )
        current_temperature += temperature_step
        # Small value for floating point comparison
        if (
            current_temperature > max_temperature + 1e-9
            and translated_lines_list is None
        ):
            logger.info("  Reached maximum temperature (%.1f).", max_temperature)
            break

    if not translated_lines_list:
        raise RuntimeError(
            "Warning: Translation failed for all temperature settings or the result was not in the expected format."
        )

    # Create output data
    lyrics = copy.copy(lyrics)
    for i, item in enumerate(lyrics):
        # Condition: For each dictionary, add a new key "translations",
        #            and create a nested key "en" inside it
        if "translations" not in item:
            item["translations"] = {}
        item["translations"]["en"] = translated_lines_list[i]
    logger.info("Incorporated translation results into output data.")

    return lyrics


def create_lyric_video(
    music_file: str,
    image_file: str,
    lyrics: list[dict],
    output_file: str = "output.mp4",
    font_name_ja: str = "MS Gothic",
    font_name_en: str = "MS Gothic",
    font_size: int = 48,
    font_color: str = "white",
    stroke_color: str = "black",
    stroke_width: int = 2,
    margin_bottom: int = 50,
    fps: int = 24,
    enable_fade: bool = True,
    threads: int = 4,
) -> None:
    """
    Creates a lyric video with subtitles from the provided music, lyrics, and background image.

    Args:
        music_file (str): Path to the music file.
        lyrics_file (str): Path to the lyrics JSON file.
        image_file (str): Path to the background image file.
        output_file (str): Path to save the output video file (default is "output.mp4").
        font_name_ja (str): Font name for Japanese text (default is "SourceHanSansJP-Regular").
        font_name_en (str): Font name for English text (default is "C:/Windows/Fonts/msmincho.ttc").
        font_size (int): Font size for subtitles (default is 48).
        font_color (str): Color of the font for subtitles (default is "white").
        stroke_color (str): Color of the stroke for subtitles (default is "black").
        stroke_width (int): Width of the stroke for subtitles (default is 2).
        margin_bottom (int): Bottom margin for subtitles (default is 50).
        fps (int): Frames per second for the output video (default is 24).
        enable_fade (bool): Whether to enable fade-in and fade-out effects for subtitles (default is True).
        threads (int): Number of threads to use for video processing (default is 4).
    """
    logger.info("--- Start generating video ---")
    logger.debug(
        "Settings: Font=%s, Size=%d, Margin=%d", font_name_ja, font_size, margin_bottom
    )

    font_path_ja = get_font_path(font_name_ja)
    if font_path_ja is None:
        raise RuntimeError(f"Font '{font_name_ja}' not found.")

    font_path_en = get_font_path(font_name_en)
    if font_path_en is None:
        raise RuntimeError(f"Font '{font_name_en}' not found.")

    audio_clip = None
    background_clip = None
    subtitle_clips = []
    video: CompositeVideoClip | None = None

    try:
        # --- Load Input Files ---
        logger.info("Loading music file: %s", music_file)
        audio_clip = AudioFileClip(music_file)
        video_duration = audio_clip.duration
        logger.debug("Music file duration: %.2f seconds", video_duration)

        logger.info("Loading background image: %s", image_file)
        background_clip = ImageClip(image_file).with_duration(video_duration)
        video_width, video_height = background_clip.size
        logger.debug("Video size: %dx%d", video_width, video_height)

        # --- Generate Subtitle Clips ---
        logger.info("Generating subtitle clips...")
        for i, lyric in enumerate(lyrics):
            start_time = lyric.get("start")
            end_time = lyric.get("end")
            text = lyric.get("text", "").strip()

            # Data validation
            if start_time is None or end_time is None or not text:
                logger.warning(
                    "Skipping invalid lyric data (line %d): %s", i + 1, lyric
                )
                continue
            if (
                not isinstance(start_time, (int, float))
                or not isinstance(end_time, (int, float))
                or start_time < 0
                or end_time <= start_time
            ):
                logger.warning(
                    "Skipping lyric data with invalid time (line %d): start=%s, end=%s",
                    i + 1,
                    start_time,
                    end_time,
                )
                continue

            end_time = min(end_time, video_duration)
            duration = end_time - start_time

            # Create TextClip
            try:
                txt_clip = TextClip(
                    text=text,
                    font_size=font_size,
                    color=font_color,
                    font=font_path_ja,
                    stroke_color=stroke_color,
                    stroke_width=stroke_width,
                    method="caption",
                    text_align="center",
                    size=(int(video_width * 0.9), None),
                )
                # Set position and timing
                txt_clip = (
                    txt_clip.with_position(
                        ("center", video_height - txt_clip.h - margin_bottom)
                    )
                    .with_start(start_time)
                    .with_duration(duration)
                )
                if enable_fade:
                    txt_clip = txt_clip.with_effects(
                        [vfx.FadeIn(0.5), vfx.FadeOut(0.5)]
                    )

                subtitle_clips.append(txt_clip)

                txt_clip = TextClip(
                    text=lyric["translations"]["en"],
                    font_size=font_size // 2,
                    color=font_color,
                    font=font_path_en,
                    stroke_color=stroke_color,
                    stroke_width=stroke_width,
                    method="caption",
                    text_align="center",
                    size=(int(video_width * 0.9), None),
                )
                # Set position and timing
                txt_clip = (
                    txt_clip.with_position(
                        ("center", video_height - margin_bottom + 10)
                    )
                    .with_start(start_time)
                    .with_duration(duration)
                )
                if enable_fade:
                    txt_clip = txt_clip.with_effects(
                        [vfx.FadeIn(0.5), vfx.FadeOut(0.5)]
                    )

                subtitle_clips.append(txt_clip)

            except Exception as e:
                logger.error(
                    "Error: Failed to create text clip (line %d): '%s' - %s",
                    i + 1,
                    text,
                    e,
                )
                logger.error(
                    "Please check if the '%s' font is installed on your system or if the path is correct.",
                    font_name_ja,
                )
                raise  # Re-raise the error to abort processing

        logger.info("Generated %d subtitle clips.", len(subtitle_clips))

        # --- Combine Clips ---
        logger.info("Combining video and subtitle clips...")
        final_clips = [background_clip] + subtitle_clips
        video = CompositeVideoClip(final_clips, size=(video_width, video_height))
        assert video is not None

        # --- Set Audio ---
        logger.info("Setting audio to video...")
        video = video.with_audio(audio_clip)
        assert video is not None

        # logger.info("Video preview")
        # video.show(34.0)
        # video = video.subclipped(0, 10)
        # video.preview(3, audio=False)
        # return

        # --- Write Output Video File ---
        logger.info("Writing video file '%s'...", output_file)
        video.write_videofile(
            output_file,
            codec="libx264",
            audio_codec="aac",
            fps=fps,
            threads=threads,
            logger="bar",
            preset="ultrafast",
        )
        logger.info("Video file created successfully: %s", output_file)

    except FileNotFoundError as e:
        logger.error("Error: Input file not found - %s", e)
    except Exception as e:
        logger.error(
            "Error: Unexpected problem occurred during video generation - %s", e
        )
        raise e
    finally:
        logger.info("Releasing resources...")
        # --- Clean up resources ---
        try:
            if audio_clip:
                audio_clip.close()
            if background_clip:
                background_clip.close()
            for clip in subtitle_clips:
                if clip:
                    clip.close()
            if video:
                video.close()
            logger.info("Cleanup complete.")
        except Exception as e:
            logger.warning(f"Warning: Error occurred during resource cleanup - {e}")

    logger.info("--- Video generation finished ---")
