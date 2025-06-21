import logging
import logging.config
import os
import shutil
import uuid
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from lyrics_video_creator.lib import (
    align_lyrics,
    correct_lyrics_timing,
    create_lyric_video,
    translate_lyrics,
)

# ログ設定を辞書形式で定義
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(asctime)s - %(name)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "file": {
            "formatter": "default",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "app.log",  # 出力ファイル名
            "maxBytes": 1024 * 1024 * 5,  # 5MB
            "backupCount": 3,
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "": {"handlers": ["default", "file"], "level": "INFO"},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {
            "handlers": ["default", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# ログ設定を適用
logging.config.dictConfig(LOGGING_CONFIG)

# ロガーのインスタンスを取得
logger = logging.getLogger(__name__)

# FastAPIアプリケーションのインスタンスを作成
app = FastAPI(
    title="Lyrics Video Creator API",
    description="API for creating lyric videos with music and images.",
    version="0.1.0",
)

# ここからCORS設定
origins = [
    "http://localhost:5173",  # Next.jsアプリケーションのオリジン
    # 必要に応じて他のオリジンも追加できます
    # 例: "http://localhost:3000" (Create React Appの場合など)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 許可するオリジンのリスト
    allow_credentials=True,  # Cookieなどの認証情報を含むリクエストを許可するか
    allow_methods=["*"],  # すべてのHTTPメソッドを許可 (GET, POST, PUT, DELETEなど)
    allow_headers=["*"],  # すべてのHTTPヘッダーを許可
)
# ここまでCORS設定


@app.post("/create_video")
async def create_video(
    music_file: UploadFile = File(),
    image_file: UploadFile = File(),
    lyrics: str = Form(),
    font_name_ja: str = Form(default="Noto Sans JP"),
    font_name_en: str = Form(default="Arial"),
    font_color: str = Form(default="#FFFFFF"),
    font_size: int = Form(default=32),
    outline_color: str = Form(default="#000000"),
    outline_size: int = Form(default=0),
    bottom_margin: int = Form(default=50),
    enable_fade: bool = Form(default=False),
) -> FileResponse:
    # 各リクエストにユニークなIDを割り当て、ログ追跡を容易にする
    request_id = str(uuid.uuid4())
    logger.info(f"[Request ID: {request_id}] ビデオ作成リクエストを受理しました。")
    logger.info(
        f"[Request ID: {request_id}] パラメータ: font_name_ja={font_name_ja}, font_color={font_color}, etc."
    )

    # 一時的なアップロードディレクトリをリクエストごとに作成
    temp_dir_path = f"uploads/{request_id}"

    try:
        logger.info(
            f"[Request ID: {request_id}] 一時ディレクトリを作成します: {temp_dir_path}"
        )
        os.makedirs(temp_dir_path, exist_ok=True)

        logger.info(
            f"[Request ID: {request_id}] バックグラウンドでのディレクトリ削除タスクを追加しました。"
        )

        # ファイルを保存
        music_filename = os.path.join(temp_dir_path, f"music_{music_file.filename}")
        image_filename = os.path.join(temp_dir_path, f"image_{image_file.filename}")
        lyrics_filename = os.path.join(temp_dir_path, "lyrics.txt")
        video_filename = os.path.join(temp_dir_path, "output_video.mp4")

        logger.info(
            f"[Request ID: {request_id}] 音楽ファイルを保存します: {music_filename}"
        )
        with open(music_filename, "wb") as f:
            f.write(await music_file.read())

        logger.info(
            f"[Request ID: {request_id}] 画像ファイルを保存します: {image_filename}"
        )
        with open(image_filename, "wb") as f:
            f.write(await image_file.read())

        logger.info(
            f"[Request ID: {request_id}] 歌詞ファイルを保存します: {lyrics_filename}"
        )
        with open(lyrics_filename, "w", encoding="utf-8") as f:
            f.write(lyrics)

        # 歌詞のアラインメント
        logger.info(f"[Request ID: {request_id}] 歌詞をアラインメントしています...")
        aligned_lyrics = align_lyrics(
            workflow_slug="subtitle-transcription-and-alignment",
            music_file=Path(music_filename),
            lyrics=lyrics,
        )
        aligned_lyrics = correct_lyrics_timing(
            original_lyrics=lyrics, aligned_lyrics=aligned_lyrics
        )

        # 歌詞の翻訳
        logger.info(f"[Request ID: {request_id}] 歌詞を翻訳しています...")
        translated_lyrics = translate_lyrics(lyrics=aligned_lyrics)

        # 歌詞動画の生成処理を呼び出す
        logger.info(f"[Request ID: {request_id}] 歌詞動画を生成しています...")
        create_lyric_video(
            music_file=music_filename,
            image_file=image_filename,
            lyrics=translated_lyrics,
            output_file=video_filename,
            font_name_ja=font_name_ja,
            font_name_en=font_name_en,
            font_color=font_color,
            stroke_color=outline_color,
            font_size=font_size,
            stroke_width=outline_size,
            margin_bottom=bottom_margin,
            enable_fade=enable_fade,
        )
        logger.info(
            f"[Request ID: {request_id}] 歌詞動画の生成が完了しました: {video_filename}"
        )

        # 動画ファイルをレスポンスとして返す
        return FileResponse(
            video_filename,
            media_type="video/mp4",
            filename=os.path.basename(video_filename),
        )

    except Exception as e:
        logger.error(
            f"[Request ID: {request_id}] ビデオ作成中にエラーが発生しました。",
            exc_info=True,
        )
        # エラーが発生した場合も、作成された一時ディレクトリをクリーンアップ
        if os.path.exists(temp_dir_path):
            shutil.rmtree(temp_dir_path)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


def main():
    logger.info("FastAPIアプリケーションを起動します。")
    logger.info("APIドキュメント: http://127.0.0.1:8000/docs")
    # uvicorn.run に log_config を渡してロギング設定を適用
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        log_config=LOGGING_CONFIG,
        reload=True,  # 開発中はリロードを有効にすると便利
    )


if __name__ == "__main__":
    main()
