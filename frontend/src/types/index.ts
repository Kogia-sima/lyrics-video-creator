export interface SubtitleSettings {
  fontFamilyJa: string;
  fontFamilyEn: string;
  fontSize: number;
  color: string;
  outlineColor: string;
  outlineSize: number;
  bottomMargin: number;
  enableFade: boolean;
}

export interface VideoGeneratorState {
  audioFile: File | null;
  backgroundImage: File | null;
  lyrics: string;
  settings: SubtitleSettings;
}

export type ActionType =
  | { type: 'SET_AUDIO_FILE'; payload: File | null }
  | { type: 'SET_BACKGROUND_IMAGE'; payload: File | null }
  | { type: 'SET_LYRICS'; payload: string }
  | { type: 'UPDATE_SETTINGS'; payload: Partial<SubtitleSettings> };