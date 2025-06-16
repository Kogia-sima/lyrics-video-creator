import React from 'react';
import { Settings, Type, Palette, Square } from 'lucide-react';
import { HexColorPicker } from 'react-colorful';
import { SubtitleSettings } from '../types';
import { Slider } from './ui/Slider';
import { Switch } from './ui/Switch';

interface SubtitleSettingsPanelProps {
  settings: SubtitleSettings;
  onChange: (settings: Partial<SubtitleSettings>) => void;
}

export const SubtitleSettingsPanel: React.FC<SubtitleSettingsPanelProps> = ({
  settings,
  onChange
}) => {
  const japaneseFonts = [
    'HG教科書体',
    'HGP教科書体',
    'Meiryo',
    'Meiryo UI',
    'MS Gothic',
    'MS PGothic',
    'MS Mincho',
    'MS PMincho',
    'Noto Sans JP',
    'Noto Serif JP',
    'Yu Gothic',
    'Yu Gothic UI',
  ];

  const englishFonts = [
    'Roboto',
    'Arial',
    'Times New Roman',
  ];

  return (
    <div className="bg-slate-900 rounded-lg border border-slate-800 animate-fade-in">
      <div className="p-6 border-b border-slate-800">
        <div className="flex items-center mb-4">
          <Settings className="h-5 w-5 text-primary mr-2" />
          <h2 className="text-xl font-semibold text-white">字幕設定</h2>
        </div>
      </div>

      <div className="p-6 space-y-8">
        {/* Font Settings */}
        <div className="space-y-4">
          <h3 className="text-md font-medium text-white flex items-center">
            <Type className="h-4 w-4 mr-2 text-primary" />
            フォント設定
          </h3>

          <div className="space-y-3">
            <div>
              <label className="text-sm text-slate-400">日本語フォント</label>
              <select
                value={settings.fontFamilyJa}
                onChange={(e) => onChange({ fontFamilyJa: e.target.value })}
                className="w-full mt-1 bg-slate-800 border border-slate-700 text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
              >
                {japaneseFonts.map((font) => (
                  <option key={font} value={font}>{font}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-sm text-slate-400">英語フォント</label>
              <select
                value={settings.fontFamilyEn}
                onChange={(e) => onChange({ fontFamilyEn: e.target.value })}
                className="w-full mt-1 bg-slate-800 border border-slate-700 text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
              >
                {englishFonts.map((font) => (
                  <option key={font} value={font}>{font}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-sm text-slate-400">フォントサイズ: {settings.fontSize}px</label>
              <Slider
                value={[settings.fontSize]}
                min={16}
                max={72}
                step={1}
                onValueChange={(values) => onChange({ fontSize: values[0] })}
              />
            </div>

            <div>
              <label className="text-sm text-slate-400">縁取りの大きさ: {settings.outlineSize}px</label>
              <Slider
                value={[settings.outlineSize]}
                min={0}
                max={4}
                step={0.25}
                onValueChange={(values) => onChange({ outlineSize: values[0] })}
              />
            </div>
          </div>
        </div>

        {/* Color Settings */}
        <div className="space-y-4">
          <h3 className="text-md font-medium text-white flex items-center">
            <Palette className="h-4 w-4 mr-2 text-primary" />
            色設定
          </h3>

          <div className="space-y-4">
            <div>
              <label className="text-sm text-slate-400 block mb-2">文字色</label>
              <div className="flex items-center space-x-3">
                <div
                  className="w-10 h-10 rounded-md border border-slate-600"
                  style={{ backgroundColor: settings.color }}
                />
                <HexColorPicker
                  color={settings.color}
                  onChange={(color) => onChange({ color })}
                  className="w-full max-w-[200px]"
                />
              </div>
            </div>

            <div>
              <label className="text-sm text-slate-400 block mb-2">縁取り色</label>
              <div className="flex items-center space-x-3">
                <div
                  className="w-10 h-10 rounded-md border border-slate-600"
                  style={{ backgroundColor: settings.outlineColor }}
                />
                <HexColorPicker
                  color={settings.outlineColor}
                  onChange={(color) => onChange({ outlineColor: color })}
                  className="w-full max-w-[200px]"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Layout Settings */}
        <div className="space-y-4">
          <h3 className="text-md font-medium text-white flex items-center">
            <Square className="h-4 w-4 mr-2 text-primary" />
            レイアウトと効果
          </h3>

          <div className="space-y-3">
            <div>
              <label className="text-sm text-slate-400">下余白: {settings.bottomMargin}px</label>
              <Slider
                value={[settings.bottomMargin]}
                min={0}
                max={150}
                step={5}
                onValueChange={(values) => onChange({ bottomMargin: values[0] })}
              />
            </div>

            <div className="flex items-center justify-between">
              <label className="text-sm text-slate-400">フェードイン・アウトを有効にする</label>
              <Switch
                checked={settings.enableFade}
                onCheckedChange={(checked) => onChange({ enableFade: checked })}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};