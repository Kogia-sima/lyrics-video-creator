# main.py
import json
import os
import uuid

import uvicorn
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse

from lyrics_video_creator.lib import create_lyric_video

# FastAPIアプリケーションのインスタンスを作成
app = FastAPI(
    title="FastAPIサンプルアプリケーション",
    description="FastAPIの様々な機能を紹介するためのサンプルです。",
    version="0.1.0",
)


@app.post("/create_video")
async def create_video(
    music_file: UploadFile = File(),
    image_file: UploadFile = File(),
    lyrics: str = Form(),
    font_name_ja: str = Form(default="Noto Sans JP"),
    font_name_en: str = Form(default="Arial"),
    font_color: str = Form(default="#FFFFFF"),
    outline_color: str = Form(default="#000000"),
    font_size: int = Form(default=32),
    outline_size: int = Form(default=0),
    bottom_margin: int = Form(default=50),
    enable_fade: bool = Form(default=False),
):
    # Create uploads directory if not exists
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    # Save audio file
    music_filename = os.path.join(upload_dir, f"{uuid.uuid4()}_{music_file.filename}")
    with open(music_filename, "wb") as f:
        f.write(await music_file.read())

    # Save image file
    image_filename = os.path.join(upload_dir, f"{uuid.uuid4()}_{image_file.filename}")
    with open(image_filename, "wb") as f:
        f.write(await image_file.read())

    # Save lyrics to a text file
    lyrics_filename = os.path.join(upload_dir, f"{uuid.uuid4()}_lyrics.txt")
    with open(lyrics_filename, "w", encoding="utf-8") as f:
        f.write(lyrics)

    # Create a dummy video file (simulate combining audio and image)
    video_filename = os.path.join(upload_dir, f"{uuid.uuid4()}_video.mp4")

    # Call the create_lyric_video function to generate the video
    create_lyric_video(
        music_file=music_filename,
        image_file=image_filename,
        lyrics_file=lyrics_filename,
        output_file=video_filename,
        font_name_ja=font_name_ja,
        font_name_en=font_name_en,
        font_color=font_color,
        stroke_color=outline_color,
        font_size=font_size,
        stroke_width=outline_size,
        margin_bottom=bottom_margin,
        # enable_fade=enable_fade,
    )

    # Return video file as response
    return FileResponse(
        video_filename,
        media_type="video/mp4",
        filename=os.path.basename(video_filename),
    )


def main():
    print(
        f"FastAPIアプリケーションを起動します。 http://127.0.0.1:8000/docs でAPIドキュメントを確認できます。"
    )
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()  # アプリケーションを起動するためのメイン関数を呼び出す
