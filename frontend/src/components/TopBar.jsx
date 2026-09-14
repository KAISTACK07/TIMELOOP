import React from 'react';
import { Play, History, User, Sparkles, ChevronDown, Loader2, Moon, Sun, AlertTriangle, Settings2 } from 'lucide-react';

export default function TopBar({ onRun, loading, theme, toggleTheme, sessionId, error, mode, setMode, onOpenAI }) {
  const [modeMenuOpen, setModeMenuOpen] = React.useState(false);

  const MODES = {
    detailed: { label: 'DETAILED', desc: 'Captures fine-grained execution activity and produces the largest timeline.' },
    smart: { label: 'SMART', desc: 'Prioritizes meaningful events (calls, returns, exceptions, yields, mutations).' },
    reduced: { label: 'REDUCED', desc: 'Suppresses generic noise and focuses on semantic operations.' }
  };
  return (
    <header className="h-14 border-b border-theme-border bg-theme-header flex items-center px-6 shrink-0 relative z-20 transition-colors duration-300">
      
      {/* Left: Logo & Session */}
      <div className="flex items-center gap-6 flex-1">
        <div className="flex items-center gap-2 group cursor-pointer">
          <div className="relative w-14 h-14 flex items-center justify-center">
            {loading ? (
              <img 
                src="/topbar%20logo.png" 
                alt="Logo" 
                className="w-12 h-12 object-contain animate-pulse drop-shadow-[0_0_15px_var(--color-accent)] scale-90 transition-all duration-300"
              />
            ) : (
              <img 
                src="/1.png" 
                alt="Logo" 
                className="w-12 h-12 object-contain group-hover:scale-110 transition-all duration-300 drop-shadow-[0_0_8px_var(--color-accent)] group-hover:drop-shadow-[0_0_20px_var(--color-accent)]"
              />
            )}
            <div className="absolute inset-0 bg-theme-accent blur-2xl opacity-30 group-hover:opacity-60 transition-opacity rounded-full"></div>
          </div>
          <span className="font-accent text-theme-accent text-3xl tracking-widest mt-2 ml-1 drop-shadow-[0_0_10px_var(--color-accent-glow)] font-bold">TimeLoop</span>
        </div>

        <div className="h-5 w-px bg-theme-border hidden md:block"></div>

        <button className="hidden md:flex items-center gap-2 text-xs font-mono text-theme-muted hover:text-theme-text transition-colors">
          <span>Session: <span className="text-theme-text font-bold">{sessionId ? sessionId.substring(0, 16) : 'none'}</span></span>
          <ChevronDown size={14} />
        </button>

        {/* Mode Selector */}
        <div className="relative">
          <button 
            onClick={() => setModeMenuOpen(!modeMenuOpen)}
            className="flex items-center gap-2 text-xs font-mono text-theme-muted hover:text-theme-text transition-colors bg-theme-panel border border-theme-border px-3 py-1.5 rounded"
          >
            <Settings2 size={14} />
            <span>Mode: <span className="text-theme-text font-bold">{MODES[mode]?.label}</span></span>
            <ChevronDown size={14} />
          </button>
          
          {modeMenuOpen && (
            <div className="absolute top-full mt-2 left-0 w-64 bg-theme-panel border border-theme-border rounded shadow-xl z-50 overflow-hidden">
              {Object.entries(MODES).map(([k, v]) => (
                <div 
                  key={k}
                  onClick={() => {
                    setMode(k);
                    setModeMenuOpen(false);
                  }}
                  className={`p-3 cursor-pointer transition-colors ${mode === k ? 'bg-theme-accent-dim border-l-2 border-theme-accent' : 'hover:bg-theme-hover border-l-2 border-transparent'}`}
                >
                  <div className={`font-mono text-xs font-bold ${mode === k ? 'text-theme-accent' : 'text-theme-text'}`}>
                    {v.label}
                  </div>
                  <div className="text-[10px] text-theme-muted mt-1 leading-tight">
                    {v.desc}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Error indicator */}
        {error && (
          <div className="hidden md:flex items-center gap-2 text-xs font-mono text-yellow-500 bg-yellow-500/10 border border-yellow-500/30 px-3 py-1 rounded">
            <AlertTriangle size={12} />
            <span className="truncate max-w-48">{error}</span>
          </div>
        )}
      </div>

      {/* Center: Run Button */}
      <div className="flex-1 flex justify-center">
        <button 
          onClick={onRun}
          disabled={loading}
          className="relative overflow-hidden group flex items-center gap-3 bg-theme-accent-dim text-theme-accent hover:bg-theme-accent hover:text-[var(--color-bg)] border border-theme-accent px-8 py-2 rounded-md text-sm font-accent tracking-widest transition-all uppercase shadow-[0_0_15px_var(--color-accent-glow)] hover:shadow-[0_0_25px_var(--color-accent)] disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? <Loader2 size={18} className="animate-spin relative z-10" /> : <Play size={18} fill="currentColor" className="relative z-10" />}
          <span className="relative z-10 mt-1">{loading ? 'Executing...' : 'Run'}</span>
          
          {/* Energy charging effect on hover */}
          {!loading && (
            <div className="absolute inset-0 bg-theme-text/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out z-0"></div>
          )}
        </button>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center justify-end gap-4 flex-1">
        <button onClick={toggleTheme} className="p-2 text-theme-muted hover:text-theme-accent hover:bg-theme-hover hover:scale-110 rounded-full transition-all duration-300" title="Toggle Theme">
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
        
        <div className="w-px h-5 bg-theme-border mx-1"></div>

        <button 
          onClick={onOpenAI}
          className="p-2 text-theme-muted hover:text-theme-accent hover:bg-theme-hover hover:scale-110 rounded-full transition-all duration-300" 
          title="AI Assistant"
        >
          <Sparkles size={18} />
        </button>
        <button className="p-2 text-theme-muted hover:text-theme-text hover:bg-theme-hover hover:scale-110 rounded-full transition-all duration-300" title="History">
          <History size={18} />
        </button>
        <button className="p-2 text-theme-muted hover:text-theme-text hover:bg-theme-hover hover:scale-110 rounded-full transition-all duration-300" title="Account">
          <User size={18} />
        </button>
      </div>
    </header>
  );
}