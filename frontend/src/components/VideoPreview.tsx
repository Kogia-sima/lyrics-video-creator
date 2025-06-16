import React from 'react';
import { SubtitleSettings } from '../types';

interface VideoPreviewProps {
  backgroundImage: File | null;
  lyrics: string;
  settings: SubtitleSettings;
}

export const VideoPreview: React.FC<VideoPreviewProps> = ({
  backgroundImage,
  lyrics,
  settings,
}) => {
  const [backgroundUrl, setBackgroundUrl] = React.useState<string | null>(null);
  const [aspectRatio, setAspectRatio] = React.useState(16 / 9);
  const containerRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (backgroundImage) {
      const newUrl = URL.createObjectURL(backgroundImage);
      setBackgroundUrl(newUrl);

      // Load image to get its dimensions
      const img = new Image();
      img.onload = () => {
        setAspectRatio(img.width / img.height);
        URL.revokeObjectURL(img.src);
      };
      img.src = newUrl;

      return () => URL.revokeObjectURL(newUrl);
    } else {
      setBackgroundUrl(null);
      setAspectRatio(16 / 9);
    }
  }, [backgroundImage]);

  const subtitleStyle: React.CSSProperties = {
    fontFamily: settings.fontFamilyJa,
    fontSize: `${settings.fontSize}px`,
    color: settings.color,
    textShadow: `0 0 ${settings.outlineSize}px ${settings.outlineColor}`,
    WebkitTextStroke: `${settings.outlineSize}px ${settings.outlineColor}`,
    marginBottom: 0,
    padding: 0,
  };

  // 英語字幕用スタイル
  const englishSubtitleStyle: React.CSSProperties = {
    ...subtitleStyle,
    fontFamily: settings.fontFamilyEn,
    fontSize: `${settings.fontSize / 2}px`,
    marginTop: 0,
    marginBottom: `${settings.bottomMargin}px`,
  };

  return (
    <div className="relative bg-slate-950 rounded-lg overflow-hidden border border-slate-800" ref={containerRef}>
      <div
        className="relative w-full overflow-hidden"
        style={{
          paddingBottom: `${(1 / aspectRatio) * 100}%`
        }}
      >
        {backgroundUrl ? (
          <img
            src={backgroundUrl}
            alt="背景"
            className="absolute inset-0 w-full h-full object-cover"
          />
        ) : (
          <div className="absolute inset-0 w-full h-full bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center">
            <p className="text-slate-500 text-lg">背景画像がありません</p>
          </div>
        )}

        <div className="absolute inset-x-0 bottom-0 flex flex-col items-center justify-end p-4 h-full">
          <div
            className="text-center px-4 py-2 max-w-[90%]"
            style={subtitleStyle}
          >
            字幕がここに表示されます
          </div>
          <div
            className="mt-1"
            style={englishSubtitleStyle}
          >
            English subtitle appears here
          </div>
        </div>
      </div>
    </div>
  );
};