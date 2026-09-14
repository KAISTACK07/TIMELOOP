import React, { useState, useEffect } from 'react';
import { Sparkles, X, Check, Copy, Zap, ArrowRight, Code, Activity, ShieldCheck, Loader2 } from 'lucide-react';
import * as api from '../lib/api.js';

export default function AIExplainerModal({ 
  isOpen, 
  onClose, 
  code, 
  currentLine, 
  currentSnapshot, 
  currentState, 
  mode,
  onApplyCode 
}) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState('explanation'); // 'explanation' | 'code'

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      setCopied(false);
      setError(null);
      setAnalysis(null);

      const context = {
        code,
        currentLine,
        snapshot: currentSnapshot,
        variables: currentState,
        stack: currentSnapshot?.stack || [],
        mode
      };

      api.explainCode(context)
        .then((res) => {
          setAnalysis(res);
        })
        .catch((err) => {
          console.error("AI analysis error:", err);
          setError("Could not reach the analysis backend. Is the server running?");
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [isOpen, code, currentLine, currentSnapshot, currentState, mode]);

  const isLLM = analysis?.source === 'llm';

  if (!isOpen) return null;

  const handleCopy = () => {
    if (analysis?.optimizedCode) {
      navigator.clipboard.writeText(analysis.optimizedCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleApply = () => {
    if (analysis?.optimizedCode && onApplyCode) {
      onApplyCode(analysis.optimizedCode);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-theme-panel border border-theme-border w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh] transition-colors">
        
        {/* Header */}
        <div className="h-14 border-b border-theme-border px-6 flex items-center justify-between bg-theme-header shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-theme-accent-dim flex items-center justify-center text-theme-accent shadow-[0_0_12px_var(--color-accent-glow)]">
              <Sparkles size={18} />
            </div>
            <div>
              <h2 className="text-sm font-mono font-bold text-theme-text flex items-center gap-2">
                AI Code Explainer & Optimizer
              </h2>
              <span className="text-[10px] font-mono text-theme-muted flex items-center gap-1.5">
                <ShieldCheck size={11} className="text-emerald-400" />
                {analysis
                  ? isLLM
                    ? `Claude${analysis.model ? ` · ${analysis.model}` : ''} · secure backend`
                    : 'Deterministic AST static analysis'
                  : 'Secure server-side analysis'}
              </span>
            </div>
          </div>
          
          <button 
            onClick={onClose}
            className="p-1.5 rounded-lg text-theme-muted hover:text-theme-text hover:bg-theme-hover transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-auto p-6 space-y-5">
          {loading ? (
            <div className="py-16 flex flex-col items-center justify-center text-center space-y-4">
              <Loader2 size={32} className="text-theme-accent animate-spin" />
              <div className="text-xs font-mono text-theme-muted">
                Analyzing AST execution profile, call graphs, and algorithmic complexity...
              </div>
            </div>
          ) : error ? (
            <div className="py-12 text-center text-xs font-mono text-red-300/90 space-y-2">
              <div className="text-red-400 font-bold uppercase tracking-wider">Analysis unavailable</div>
              <p>{error}</p>
            </div>
          ) : analysis ? (
            <>
              {analysis.error && (
                <div className="text-[11px] font-mono p-2.5 rounded-lg border border-amber-500/25 bg-amber-500/5 text-amber-300/90">
                  {analysis.error}
                </div>
              )}
              {/* Complexity Badges */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3.5 rounded-xl border border-theme-border bg-theme-panel-inner flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <Activity size={16} className="text-sky-400" />
                    <span className="text-xs font-mono text-theme-muted">Current Complexity</span>
                  </div>
                  <span className="text-xs font-mono font-bold text-amber-400 px-2.5 py-1 rounded bg-amber-400/10 border border-amber-400/20">
                    {analysis.timeComplexity}
                  </span>
                </div>

                <div className="p-3.5 rounded-xl border border-theme-border bg-theme-panel-inner flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <Zap size={16} className="text-emerald-400" />
                    <span className="text-xs font-mono text-theme-muted">Expected Optimized</span>
                  </div>
                  <span className="text-xs font-mono font-bold text-emerald-400 px-2.5 py-1 rounded bg-emerald-400/10 border border-emerald-400/20">
                    {analysis.expectedComplexity}
                  </span>
                </div>
              </div>

              {/* Context bar */}
              {analysis.activeLineInfo && (
                <div className="text-[11px] font-mono p-2.5 rounded-lg border border-theme-border/60 bg-theme-header text-theme-muted flex items-center gap-2">
                  <span className="text-theme-accent font-bold">Focus:</span>
                  <span className="text-theme-text truncate">{analysis.activeLineInfo}</span>
                </div>
              )}

              {/* Tabs */}
              <div className="flex border-b border-theme-border gap-4 text-xs font-mono">
                <button
                  onClick={() => setActiveTab('explanation')}
                  className={`pb-2 transition-colors border-b-2 ${
                    activeTab === 'explanation' 
                      ? 'border-theme-accent text-theme-accent font-bold' 
                      : 'border-transparent text-theme-muted hover:text-theme-text'
                  }`}
                >
                  Analysis & Optimization
                </button>
                <button
                  onClick={() => setActiveTab('code')}
                  className={`pb-2 transition-colors border-b-2 flex items-center gap-1.5 ${
                    activeTab === 'code' 
                      ? 'border-theme-accent text-theme-accent font-bold' 
                      : 'border-transparent text-theme-muted hover:text-theme-text'
                  }`}
                >
                  <Code size={13} />
                  Optimized Implementation
                </button>
              </div>

              {activeTab === 'explanation' ? (
                <div className="space-y-4 text-xs font-mono leading-relaxed">
                  {/* Issue section */}
                  <div className="p-4 rounded-xl border border-red-500/25 bg-red-500/5 space-y-1.5">
                    <div className="text-[11px] font-bold text-red-400 uppercase tracking-wider flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-red-400"></span>
                      Performance Bottleneck Detected
                    </div>
                    <p className="text-red-300/90">{analysis.issue}</p>
                  </div>

                  {/* Proposal section */}
                  <div className="p-4 rounded-xl border border-emerald-500/25 bg-emerald-500/5 space-y-1.5">
                    <div className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                      Recommended Optimization Strategy
                    </div>
                    <p className="text-emerald-300/90">{analysis.optimization}</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="relative rounded-xl border border-theme-border bg-black/60 p-4 font-mono text-xs overflow-x-auto">
                    <pre className="text-gray-200">{analysis.optimizedCode}</pre>
                  </div>
                  <div className="flex justify-end gap-2 pt-1">
                    <button
                      onClick={handleCopy}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-theme-border text-xs font-mono text-theme-muted hover:text-theme-text hover:bg-theme-hover transition-colors"
                    >
                      {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
                      <span>{copied ? 'Copied' : 'Copy Code'}</span>
                    </button>
                    {onApplyCode && (
                      <button
                        onClick={handleApply}
                        className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-theme-accent text-[var(--color-bg)] text-xs font-mono font-bold hover:opacity-90 transition-opacity"
                      >
                        <span>Apply to Editor</span>
                        <ArrowRight size={14} />
                      </button>
                    )}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="py-12 text-center text-xs font-mono text-theme-muted">
              No analysis available. Run the code to generate execution traces.
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="h-12 border-t border-theme-border px-6 flex items-center justify-between bg-theme-header shrink-0 text-[11px] font-mono text-theme-muted">
          <span>Mode: <strong className="text-theme-text uppercase">{mode}</strong></span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg border border-theme-border hover:bg-theme-hover text-theme-text transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
