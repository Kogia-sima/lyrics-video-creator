import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Music, Image, File, X } from 'lucide-react';

interface FileUploadProps {
  type: 'audio' | 'image';
  file: File | null;
  onFileChange: (file: File | null) => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  type,
  file,
  onFileChange
}) => {
  const acceptedFileTypes = {
    audio: {
      'audio/*': ['.mp3', '.wav', '.ogg', '.frac']
    },
    image: {
      'image/*': ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.pbm', '.pgm', '.ppm', '.tif', '.tiff']
    }
  };

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onFileChange(acceptedFiles[0]);
    }
  }, [onFileChange]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: acceptedFileTypes[type],
    maxFiles: 1,
    multiple: false
  });

  const handleClearFile = (e: React.MouseEvent) => {
    e.stopPropagation();
    onFileChange(null);
  };

  const getFilePreview = () => {
    if (!file) return null;

    if (type === 'image') {
      const objectUrl = URL.createObjectURL(file);
      return (
        <div className="relative w-full h-32 overflow-hidden rounded-md">
          <img
            src={objectUrl}
            alt="プレビュー"
            className="w-full h-full object-cover"
            onLoad={() => URL.revokeObjectURL(objectUrl)}
          />
        </div>
      );
    }

    if (type === 'audio') {
      const objectUrl = URL.createObjectURL(file);
      return (
        <div className="w-full">
          <audio
            controls
            className="w-full"
            onLoad={() => URL.revokeObjectURL(objectUrl)}
          >
            <source src={objectUrl} />
            お使いのブラウザは音声再生に対応していません。
          </audio>
        </div>
      );
    }

    return null;
  };

  const getIcon = () => {
    switch (type) {
      case 'audio':
        return <Music className="h-12 w-12 text-slate-400" />;
      case 'image':
        return <Image className="h-12 w-12 text-slate-400" />;
      default:
        return <File className="h-12 w-12 text-slate-400" />;
    }
  };

  const getTitle = () => {
    switch (type) {
      case 'audio':
        return '音楽ファイル';
      case 'image':
        return '背景画像';
      default:
        return 'ファイル';
    }
  };

  return (
    <div className="animate-fade-in">
      <div className="mb-2 text-lg font-medium text-white">{getTitle()}</div>
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-4 transition-colors cursor-pointer
          ${isDragActive
            ? 'border-primary bg-primary-50 bg-opacity-5'
            : 'border-slate-700 hover:border-primary-300 bg-slate-800/50'
          }
          ${file ? 'border-slate-600' : ''}
        `}
      >
        <input {...getInputProps()} />

        {file ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                {type === 'audio' && <Music className="h-5 w-5 text-primary" />}
                {type === 'image' && <Image className="h-5 w-5 text-primary" />}
                <span className="text-sm font-medium truncate max-w-[200px]">
                  {file.name}
                </span>
              </div>
              <button
                onClick={handleClearFile}
                className="p-1 rounded-full hover:bg-slate-700 transition-colors"
              >
                <X className="h-4 w-4 text-slate-400" />
              </button>
            </div>
            {getFilePreview()}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-6 text-center">
            {getIcon()}
            <p className="mt-2 text-xs font-medium text-slate-300">
              {type === 'audio' ? '音声ファイルを' : '画像を'}ドラッグ＆ドロップ、またはクリックして選択
            </p>
            <p className="mt-1 text-xs text-slate-500">
              {type === 'audio' ? 'MP3, WAV, OGG, M4A' : 'JPG, PNG, GIF, WEBP'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};