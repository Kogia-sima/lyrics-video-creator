import React from 'react';
import { Music, Settings, Film, GithubIcon } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      <header className="border-b border-slate-800 py-4 px-6 bg-slate-900">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Film className="h-6 w-6 text-primary" />
            <span className="text-xl font-semibold text-white">Lyrics Video Creator</span>
          </div>

          <div className="flex items-center space-x-4">
            <a
              href="https://github.com/Kogia-sima/lyrics-video-creator"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-slate-400 hover:text-white transition-colors"
              title="GitHub"
            >
              <GithubIcon className="h-5 w-5" />
            </a>
          </div>
        </div>
      </header>

      <main className="flex-1 w-full max-w-7xl mx-auto px-4 py-6 md:px-6">
        {children}
      </main>

      <footer className="border-t border-slate-800 py-4 px-6 bg-slate-900">
        <div className="max-w-7xl mx-auto text-center text-sm text-slate-500">
          <p>Lyrics Video Creator &copy; 2025</p>
        </div>
      </footer>
    </div>
  );
};