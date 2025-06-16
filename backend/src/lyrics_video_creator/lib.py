import json
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
        create_job_info = self.client.add_job(
            job_name=str(uuid.uuid4()),
            workflow_slug=workflow_slug,
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


def translate_lyrics(input_file_path: str, output_file_path: str | None):
    """
    Reads a Japanese lyrics JSON file, translates it into English, and saves it to a new JSON file.

    Args:
        input_file_path (str): Path to the input JSON file.
        output_file_path (str): Path to the output JSON file.
    """
    # 1. Check OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key is None:
        print("Error: Environment variable OPENAI_API_KEY is not set.")
        print("Please set OPENAI_API_KEY before running the script.")
        print("Example: export OPENAI_API_KEY='your_api_key_here'")
        return

    # 2. Read input file
    try:
        with open(input_file_path, "r", encoding="utf-8") as f:
            lyrics_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file_path}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Input file '{input_file_path}' is not a valid JSON format.")
        return
    except Exception as e:
        print(
            f"An unexpected error occurred while reading input file '{input_file_path}': {e}"
        )
        return

    # Check input data format
    if not isinstance(lyrics_data, list):
        print(f"Error: The content of input file '{input_file_path}' must be a list.")
        return
    if not all(
        isinstance(item, dict) and "text" in item and "start" in item and "end" in item
        for item in lyrics_data
    ):
        print(
            f"Error: Each element in the input file must be a dictionary with 'text', 'start', and 'end' keys."
        )
        return

    # If output file path is not specified, save in the same directory as the input file
    if output_file_path is None:
        output_file_path = os.path.splitext(input_file_path)[0] + "_translated.json"

    japanese_texts = [item["text"] for item in lyrics_data]
    num_original_lines = len(japanese_texts)
    japanese_lyrics_block = "\n".join(japanese_texts)

    # 3. Create prompt
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

    print(f"Starting translation. Number of input lines: {num_original_lines}")

    # 4. Translation using ChatOpenAI (including retry logic)
    while current_temperature <= max_temperature:
        print(f"  Trying translation with temperature {current_temperature:.1f}...")

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
        print(
            f"  The number of lines in the translation result with temperature {current_temperature:.1f} did not match."
        )
        print(
            f"    Expected lines: {num_original_lines}, Actual lines: {len(potential_translations)}"
        )

        current_temperature += temperature_step
        # Small value for floating point comparison
        if (
            current_temperature > max_temperature + 1e-9
            and translated_lines_list is None
        ):
            print(f"  Reached maximum temperature ({max_temperature:.1f}).")
            break

    if not translated_lines_list:
        raise RuntimeError(
            "Warning: Translation failed for all temperature settings or the result was not in the expected format."
        )

    # 5. Create output data
    for i, item in enumerate(lyrics_data):
        # Condition: For each dictionary, add a new key "translations",
        #            and create a nested key "en" inside it
        if "translations" not in item:
            item["translations"] = {}
        item["translations"]["en"] = translated_lines_list[i]
    print("Incorporated translation results into output data.")

    # 6. Save output file
    # Condition: Save the output result in JSON format to a path different from the input file
    try:
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(lyrics_data, f, ensure_ascii=False, indent=4)
        print(f"Saved translation result to '{output_file_path}'.")
    except Exception as e:
        print(
            f"An error occurred while saving to output file '{output_file_path}': {e}"
        )


def create_lyric_video(
    music_file: str,
    lyrics_file: str,
    image_file: str,
    output_file: str = "output.mp4",
    font_name_ja: str = "SourceHanSansJP-Regular",
    font_name_en: str = "C:/Windows/Fonts/msmincho.ttc",
    font_size: int = 48,
    font_color: str = "white",
    stroke_color: str = "black",
    stroke_width: int = 2,
    margin_bottom: int = 50,
    fps: int = 24,
    threads: int = 4,
) -> None:
    """
    Create a lyric video with subtitles from an image, lyric data, and music.

    Args:
        music_file (str): Path to the music file.
        lyrics_file (str): Path to the lyric data (JSON) file.
        image_file (str): Path to the background image file.
        output_file (str, optional): Path to the output video file. Default is "output.mp4".
        font_name (str, optional): Font name or font file path for subtitles.
                                    Default is "SourceHanSansJP-Regular".
        font_size (int, optional): Font size for subtitles. Default is 48.
        font_color (str, optional): Font color for subtitles. Default is "white".
        stroke_color (str, optional): Stroke color for subtitles. Default is "black".
        stroke_width (int, optional): Stroke width for subtitles. Default is 2.
        margin_bottom (int, optional): Bottom margin for subtitles. Default is 50.
        fps (int, optional): Frame rate for output video. Default is 24.
        threads (int, optional): Number of threads for encoding. Default is 4.
    """
    print("--- Start generating video ---")
    print(f"Settings: Font={font_name_ja}, Size={font_size}, Margin={margin_bottom}")

    audio_clip = None
    background_clip = None
    subtitle_clips = []
    video: CompositeVideoClip | None = None

    try:
        # --- Load Input Files ---
        print(f"Loading music file: {music_file}")
        audio_clip = AudioFileClip(music_file)
        video_duration = audio_clip.duration
        print(f"Music file duration: {video_duration:.2f} seconds")

        print(f"Loading background image: {image_file}")
        background_clip = ImageClip(image_file).with_duration(video_duration)
        video_width, video_height = background_clip.size
        print(f"Video size: {video_width}x{video_height}")

        print(f"Loading lyric data: {lyrics_file}")
        with open(lyrics_file, "r", encoding="utf-8") as f:
            lyrics_data = json.load(f)
        print(f"Loaded {len(lyrics_data)} lyric data entries.")

        # --- Generate Subtitle Clips ---
        print("Generating subtitle clips...")
        for i, lyric in enumerate(lyrics_data):
            start_time = lyric.get("start")
            end_time = lyric.get("end")
            text = lyric.get("text", "").strip()

            # Data validation
            if start_time is None or end_time is None or not text:
                print(f"Warning: Skipping invalid lyric data (line {i+1}): {lyric}")
                continue
            if (
                not isinstance(start_time, (int, float))
                or not isinstance(end_time, (int, float))
                or start_time < 0
                or end_time <= start_time
            ):
                print(
                    f"Warning: Skipping lyric data with invalid time (line {i+1}): start={start_time}, end={end_time}"
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
                    font=font_name_ja,
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
                    .with_effects([vfx.FadeIn(0.5), vfx.FadeOut(0.5)])
                )

                subtitle_clips.append(txt_clip)

                txt_clip = TextClip(
                    text=lyric["translations"]["en"],
                    font_size=font_size // 2,
                    color=font_color,
                    font=font_name_en,
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
                    .with_effects([vfx.FadeIn(0.5), vfx.FadeOut(0.5)])
                )
                subtitle_clips.append(txt_clip)

            except Exception as e:
                print(f"Error: Failed to create text clip (line {i+1}): '{text}' - {e}")
                print(
                    f"Please check if the '{font_name_ja}' font is installed on your system or if the path is correct."
                )
                raise  # Re-raise the error to abort processing

        print(f"Generated {len(subtitle_clips)} subtitle clips.")

        # --- Combine Clips ---
        print("Combining video and subtitle clips...")
        final_clips = [background_clip] + subtitle_clips
        video = CompositeVideoClip(final_clips, size=(video_width, video_height))
        assert video is not None

        # --- Set Audio ---
        print("Setting audio to video...")
        video = video.with_audio(audio_clip)
        assert video is not None

        print("Video preview")
        # video.show(34.0)
        # video = video.subclipped(0, 10)
        # video.preview(3, audio=False)
        # return

        # --- Write Output Video File ---
        print(f"Writing video file '{output_file}'...")
        print("This may take some time...")
        video.write_videofile(
            output_file,
            codec="libx264",
            audio_codec="aac",
            fps=fps,
            threads=threads,
            logger="bar",
            preset="ultrafast",
        )
        print(f"\nVideo file created successfully: {output_file}")

    except FileNotFoundError as e:
        print(f"Error: Input file not found - {e}")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in lyric file ({lyrics_file}) - {e}")
    except Exception as e:
        print(f"Error: Unexpected problem occurred during video generation - {e}")
        raise e  # Re-raise the error to abort processing
    finally:
        # --- Clean up resources ---
        print("Releasing resources...")
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
            print("Cleanup complete.")
        except Exception as e:
            print(f"Warning: Error occurred during resource cleanup - {e}")

    print("--- Video generation finished ---")
