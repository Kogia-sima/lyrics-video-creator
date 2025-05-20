import argparse
import json
from pathlib import Path

from dotenv import load_dotenv
from moviepy import AudioFileClip, CompositeVideoClip, ImageClip, TextClip, vfx


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
):
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


def main():
    # Load environment variables
    load_dotenv()

    # Set up command line arguments
    parser = argparse.ArgumentParser(
        description="Translate a JSON file containing Japanese lyrics into English and output the result to another JSON file.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "music_file",
        help="Path to the music file",
    )
    parser.add_argument(
        "lyrics_file", help="Path to lyric data (translated, JSON) file."
    )
    parser.add_argument(
        "image_file",
        help="Path to the background image file. Used as the video background.",
    )
    parser.add_argument(
        "--output_file", help="Path to the output video file.", default=None
    )
    parser.add_argument(
        "--font_name_ja",
        default="C:/Windows/Fonts/HGRKK.TTC",
        help="File path or font name for Japanese font.",
    )
    parser.add_argument(
        "--font_name_en",
        default="C:/Windows/Fonts/msmincho.ttc",
        help="File path or font name for English font.",
    )
    parser.add_argument(
        "--font_size",
        type=int,
        default=56,
        help="Font size for subtitles. Default is 56.",
    )
    parser.add_argument(
        "--font_color",
        default="white",
        help="Font color for subtitles. Default is 'white'.",
    )
    parser.add_argument(
        "--stroke_color",
        default="black",
        help="Stroke color for subtitles. Default is 'black'.",
    )
    parser.add_argument(
        "--stroke_width",
        type=int,
        default=0,
        help="Stroke width for subtitles. Default is 0.",
    )
    parser.add_argument(
        "--margin_bottom",
        type=int,
        default=70,
        help="Bottom margin for subtitles. Default is 70.",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=24,
        help="Frame rate for output video. Default is 24.",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=8,
        help="Number of threads for encoding. Default is 8.",
    )

    args = parser.parse_args()

    if args.output_file is None:
        args.output_file = Path(args.music_file).with_suffix(".mp4")

    create_lyric_video(**vars(args))


if __name__ == "__main__":
    main()
