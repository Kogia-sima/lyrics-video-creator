# main.py
import json
import os
import uuid

import uvicorn
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse

# FastAPIアプリケーションのインスタンスを作成
app = FastAPI(
    title="FastAPIサンプルアプリケーション",
    description="FastAPIの様々な機能を紹介するためのサンプルです。",
    version="0.1.0",
)


@app.post("/create_video")
async def create_video(
    audio_file: UploadFile = File(...),
    image_file: UploadFile = File(...),
    lyrics: str = Form(...),
    speed: str = Form(...),
    font_size: str = Form(...),
    bg_color: str = Form(...),
):
    # Create uploads directory if not exists
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    # Save audio file
    audio_filename = os.path.join(upload_dir, f"{uuid.uuid4()}_{audio_file.filename}")
    with open(audio_filename, "wb") as f:
        f.write(await audio_file.read())

    # Save image file
    image_filename = os.path.join(upload_dir, f"{uuid.uuid4()}_{image_file.filename}")
    with open(image_filename, "wb") as f:
        f.write(await image_file.read())

    # Save lyrics to a text file
    lyrics_filename = os.path.join(upload_dir, f"{uuid.uuid4()}_lyrics.txt")
    with open(lyrics_filename, "w", encoding="utf-8") as f:
        f.write(lyrics)

    # Create settings dictionary from individual parameters
    settings_data = {"speed": speed, "font_size": font_size, "bg_color": bg_color}

    # Create a dummy video file (simulate combining audio and image)
    video_filename = os.path.join(upload_dir, f"{uuid.uuid4()}_video.mp4")
    with open(video_filename, "wb") as f:
        # ...simulate video creation by writing dummy content...
        f.write(
            b"Dummy video content combining: "
            + f"Audio: {audio_filename}, Image: {image_filename}, Lyrics: {lyrics}, Settings: {settings_data}".encode(
                "utf-8"
            )
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
