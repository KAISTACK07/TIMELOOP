import React, { useRef, useEffect, useState } from 'react';

export default function CodePanel({ code, currentLine, onChange }) {
  const containerRef = useRef(null);
  const textareaRef = useRef(null);
  const [isEditing, setIsEditing] = useState(false);
  const lines = code.split('\n');

  useEffect(() => {
    if (containerRef.current && currentLine > 0 && !isEditing) {
      const activeEl = containerRef.current.querySelector(`[data-line="${currentLine}"]`);
      if (activeEl) {
        activeEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [currentLine, isEditing]);

  // Auto-resize textarea to match content
  useEffect(() => {
    if (textareaRef.current && isEditing) {
      textareaRef.current.focus();
    }
  }, [isEditing]);

  if (isEditing) {
    return (
      <div className="flex flex-col h-full bg-theme-panel">
        <div className="h-10 border-b border-theme-border flex items-center px-4 shrink-0 bg-theme-header justify-between">
          <span className="text-xs font-mono text-theme-accent font-bold uppercase tracking-widest drop-shadow-[0_0_8px_var(--color-accent-glow)]">Source Code</span>
          <button 
            onClick={() => setIsEditing(false)}
            className="text-[10px] font-mono text-theme-muted hover:text-theme-accent border border-theme-border hover:border-theme-accent px-3 py-1 rounded transition-all uppercase tracking-wider"
          >
            Done
          </button>
        </div>
        <div className="flex-1 overflow-auto relative">
          <textarea
            ref={textareaRef}
            value={code}
            onChange={(e) => onChange(e.target.value)}
            spellCheck={false}
            className="w-full h-full resize-none bg-transparent text-theme-text font-mono text-[13px] leading-relaxed p-4 pl-14 outline-none border-none"
            style={{ 
              tabSize: 4, 
              minHeight: '100%',
              caretColor: 'var(--color-accent)'
            }}
          />
          {/* Line numbers overlay */}
          <div className="absolute top-0 left-0 pointer-events-none py-4">
            {code.split('\n').map((_, idx) => (
              <div key={idx} className="text-theme-muted text-[13px] leading-relaxed text-right pr-4 select-none" style={{ width: '3rem' }}>
                {idx + 1}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-theme-panel">
      <div className="h-10 border-b border-theme-border flex items-center px-4 shrink-0 bg-theme-header justify-between">
        <span className="text-xs font-mono text-theme-accent font-bold uppercase tracking-widest drop-shadow-[0_0_8px_var(--color-accent-glow)]">Source Code</span>
        <button 
          onClick={() => setIsEditing(true)}
          className="text-[10px] font-mono text-theme-muted hover:text-theme-accent border border-theme-border hover:border-theme-accent px-3 py-1 rounded transition-all uppercase tracking-wider"
        >
          Edit
        </button>
      </div>
      <div 
        ref={containerRef}
        className="flex-1 overflow-auto font-mono text-[13px] leading-relaxed py-4 relative scroll-smooth cursor-pointer"
        onDoubleClick={() => setIsEditing(true)}
      >
        {lines.map((line, idx) => {
          const lineNum = idx + 1;
          const isActive = lineNum === currentLine;
          
          return (
            <div 
              key={idx} 
              data-line={lineNum}
              className={`flex items-start px-4 py-0.5 transition-all duration-300 ${
                isActive 
                  ? 'bg-theme-accent-dim shadow-[inset_4px_0_0_var(--color-accent),inset_0_0_20px_var(--color-accent-glow)] relative z-10' 
                  : 'hover:bg-theme-hover'
              }`}
            >
              <div className={`w-8 shrink-0 text-right pr-4 select-none transition-colors duration-300 ${isActive ? 'text-theme-accent font-bold drop-shadow-[0_0_8px_var(--color-accent)]' : 'text-theme-muted'}`}>
                {lineNum}
              </div>
              <div className={`whitespace-pre transition-colors duration-300 ${isActive ? 'text-theme-text font-medium' : 'text-theme-text opacity-70'}`}>
                {line || ' '}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}