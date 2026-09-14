import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

/* ─────────────────── Filtering ─────────────────── */

/**
 * Values that represent class definitions, modules, or non-runtime
 * globals rather than actual execution state.
 */
const NON_RUNTIME_PATTERNS = [
  /^<class\s/,
  /^<module\s/,
  /^<function\s/,
];

function isClassDef(value) {
  if (typeof value === 'string') {
    return NON_RUNTIME_PATTERNS.some((rx) => rx.test(value));
  }
  // A structured object with zero attributes and its __type__ matches common
  // class-only patterns is also treated as a class definition (not an instance).
  return false;
}

function isStructuredObject(value) {
  return (
    value !== null &&
    typeof value === 'object' &&
    !Array.isArray(value) &&
    typeof value.__type__ === 'string'
  );
}

function isCircularRef(value) {
  return isStructuredObject(value) && value.__circular__ === true;
}

function isSetObject(value) {
  return isStructuredObject(value) && value.__type__ === 'set' && Array.isArray(value.values);
}

function isGeneratorObject(value) {
  return isStructuredObject(value) && value.__type__ === 'generator';
}

function isDebuggerMeta(key) {
  return key === 'return_value' || key === 'error';
}

function isImplementationArtifact(key) {
  return key.startsWith('.') || (key.startsWith('<') && key.endsWith('>'));
}

/* ─────────────── Compact preview ─────────────── */

function objectPreview(value) {
  if (isCircularRef(value)) return `${value.__type__}(...)`;
  if (!isStructuredObject(value)) return String(value);

  const type = value.__type__;
  const attrs = value.attributes;

  if (!attrs || Object.keys(attrs).length === 0) return `${type}()`;

  const parts = [];
  const entries = Object.entries(attrs);
  for (let i = 0; i < Math.min(entries.length, 3); i++) {
    const [k, v] = entries[i];
    parts.push(`${k}=${primitivePreview(v)}`);
  }
  if (entries.length > 3) parts.push('...');
  return `${type}(${parts.join(', ')})`;
}

function primitivePreview(value) {
  if (value === null || value === undefined) return 'None';
  if (typeof value === 'boolean') return value ? 'True' : 'False';
  if (typeof value === 'number') return String(value);
  if (typeof value === 'string') {
    if (value === '...') return '...';
    if (value.startsWith('<') && value.endsWith('>')) return value;
    if (value.length > 30) return `"${value.slice(0, 27)}..."`;
    return `"${value}"`;
  }
  if (Array.isArray(value)) {
    if (value.length === 0) return '[]';
    if (value.length <= 3) return `[${value.map(primitivePreview).join(', ')}]`;
    return `[${primitivePreview(value[0])}, ... (${value.length})]`;
  }
  if (isCircularRef(value)) return `${value.__type__}(...)`;
  if (isGeneratorObject(value)) {
    return `<generator ${value.name || 'object'} (${value.supported || 'partial'})>`;
  }
  if (isSetObject(value)) {
    const items = value.values;
    if (items.length === 0) return 'set()';
    if (items.length <= 3) return `{${items.map(primitivePreview).join(', ')}}`;
    return `{${primitivePreview(items[0])}, ... (${items.length})}`;
  }
  if (isStructuredObject(value)) return objectPreview(value);
  if (typeof value === 'object') {
    const keys = Object.keys(value);
    if (keys.length === 0) return '{}';
    if (keys.length <= 2) {
      return `{${keys.map((k) => `${k}: ${primitivePreview(value[k])}`).join(', ')}}`;
    }
    return `{${keys[0]}: ${primitivePreview(value[keys[0]])}, ... (${keys.length})}`;
  }
  return String(value);
}

/* ─────────────── Value Renderer ─────────────── */

function ValueRenderer({ value, depth = 0 }) {
  const [expanded, setExpanded] = useState(depth < 1);

  /* ── Null / undefined ── */
  if (value === null || value === undefined) {
    return <span className="text-yellow-500/80 italic">None</span>;
  }

  /* ── Boolean ── */
  if (typeof value === 'boolean') {
    return <span className="text-purple-400">{value ? 'True' : 'False'}</span>;
  }

  /* ── Number ── */
  if (typeof value === 'number') {
    return <span className="text-emerald-400">{value}</span>;
  }

  /* ── String ── */
  if (typeof value === 'string') {
    if (value === '...') return <span className="text-theme-muted italic">...</span>;
    if (value.startsWith('<') && value.endsWith('>')) {
      return <span className="text-theme-muted italic">{value}</span>;
    }
    const display = value.length > 60 ? value.slice(0, 57) + '...' : value;
    return <span className="text-amber-400">"{display}"</span>;
  }

  /* ── Array (Python list/tuple) ── */
  if (Array.isArray(value)) {
    if (value.length === 0) return <span className="text-theme-muted">[]</span>;

    return (
      <span className="inline">
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-theme-muted hover:text-theme-text transition-colors cursor-pointer mr-1"
        >
          <span className="inline-block w-3 text-[10px] text-center">{expanded ? '▼' : '▶'}</span>
          <span className="text-sky-400/70 text-[10px] ml-0.5">list[{value.length}]</span>
        </button>
        {!expanded && (
          <span className="text-theme-muted text-xs">{primitivePreview(value)}</span>
        )}
        {expanded && (
          <div className="ml-3 pl-3 border-l border-theme-border/50 mt-1 space-y-1">
            {value.map((item, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className="text-theme-muted text-[10px] shrink-0 w-5 text-right">{i}</span>
                <ValueRenderer value={item} depth={depth + 1} />
              </div>
            ))}
          </div>
        )}
      </span>
    );
  }

  /* ── Circular reference ── */
  if (isCircularRef(value)) {
    return (
      <span className="inline-flex items-center gap-1.5">
        <span className="text-orange-400/90 font-semibold">{value.__type__}</span>
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-orange-500/15 text-orange-400/80 border border-orange-500/20">
          circular
        </span>
      </span>
    );
  }

  /* ── Set ── */
  if (isSetObject(value)) {
    const items = value.values;
    if (items.length === 0) return <span className="text-theme-muted">set()</span>;

    return (
      <span className="inline">
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-theme-muted hover:text-theme-text transition-colors cursor-pointer mr-1"
        >
          <span className="inline-block w-3 text-[10px] text-center">{expanded ? '▼' : '▶'}</span>
          <span className="text-sky-400/70 text-[10px] ml-0.5">set({items.length})</span>
        </button>
        {!expanded && (
          <span className="text-theme-muted text-xs">{primitivePreview(value)}</span>
        )}
        {expanded && (
          <div className="ml-3 pl-3 border-l border-theme-border/50 mt-1 space-y-1">
            {items.map((item, i) => (
              <div key={i}>
                <ValueRenderer value={item} depth={depth + 1} />
              </div>
            ))}
          </div>
        )}
      </span>
    );
  }

  /* Generator */
  if (isGeneratorObject(value)) {
    return (
      <span className="inline-flex items-center gap-1.5">
        <span className="text-theme-muted italic">
          &lt;generator {value.name || 'object'}&gt;
        </span>
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-yellow-500/10 text-yellow-500/90 border border-yellow-500/20">
          partial
        </span>
      </span>
    );
  }

  /* ── Structured user-defined object ── */
  if (isStructuredObject(value) && value.attributes) {
    const attrs = value.attributes;
    const attrEntries = Object.entries(attrs).filter(([k]) => k !== '__truncated__');
    const truncated = attrs.__truncated__;
    const isEmpty = attrEntries.length === 0;

    if (isEmpty) {
      return (
        <span className="text-cyan-400 font-semibold">
          {value.__type__}<span className="text-theme-muted font-normal">()</span>
        </span>
      );
    }

    return (
      <span className="inline">
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-theme-muted hover:text-theme-text transition-colors cursor-pointer mr-1"
        >
          <span className="inline-block w-3 text-[10px] text-center">{expanded ? '▼' : '▶'}</span>
          <span className="text-cyan-400 font-semibold ml-0.5">{value.__type__}</span>
        </button>
        {!expanded && (
          <span className="text-theme-muted text-xs ml-1">
            {objectPreview(value).replace(value.__type__, '').trim()}
          </span>
        )}
        {expanded && (
          <div className="ml-3 pl-3 border-l border-cyan-500/20 mt-1 space-y-1">
            {attrEntries.map(([attrKey, attrVal]) => (
              <div key={attrKey} className="flex items-start gap-2">
                <span className="text-violet-400/90 shrink-0">{attrKey}</span>
                <span className="text-theme-muted">=</span>
                <ValueRenderer value={attrVal} depth={depth + 1} />
              </div>
            ))}
            {truncated && (
              <div className="text-theme-muted text-[10px] italic">{truncated}</div>
            )}
          </div>
        )}
      </span>
    );
  }

  /* ── Plain dict ── */
  if (typeof value === 'object' && value !== null) {
    const entries = Object.entries(value).filter(([k]) => k !== '__truncated__');
    const truncated = value.__truncated__;
    if (entries.length === 0) return <span className="text-theme-muted">{'{}'}</span>;

    return (
      <span className="inline">
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-theme-muted hover:text-theme-text transition-colors cursor-pointer mr-1"
        >
          <span className="inline-block w-3 text-[10px] text-center">{expanded ? '▼' : '▶'}</span>
          <span className="text-sky-400/70 text-[10px] ml-0.5">dict({entries.length})</span>
        </button>
        {!expanded && (
          <span className="text-theme-muted text-xs">{primitivePreview(value)}</span>
        )}
        {expanded && (
          <div className="ml-3 pl-3 border-l border-theme-border/50 mt-1 space-y-1">
            {entries.map(([k, v]) => (
              <div key={k} className="flex items-start gap-2">
                <span className="text-amber-400/80 shrink-0">"{k}"</span>
                <span className="text-theme-muted">:</span>
                <ValueRenderer value={v} depth={depth + 1} />
              </div>
            ))}
            {truncated && (
              <div className="text-theme-muted text-[10px] italic">{truncated}</div>
            )}
          </div>
        )}
      </span>
    );
  }

  /* ── Fallback ── */
  return <span className="text-theme-text">{String(value)}</span>;
}

/* ─────────────── Main Panel ─────────────── */

export default function VariablesPanel({ currentState, prevState, error, stdout, currentSnapshot, truncated, totalSnapshots, mode }) {
  const returnValue = currentState?.return_value;
  const traceError = currentState?.error;

  // Filter out debugger metadata, implementation artifacts, and definitions.
  const entries = Object.entries(currentState).filter(
    ([key, value]) => !isDebuggerMeta(key) && !isImplementationArtifact(key) && !isClassDef(value)
  );

  // Call stack for the active frame (last entry = currently executing).
  const stack = Array.isArray(currentSnapshot?.stack) ? currentSnapshot.stack : [];

  return (
    <div className="flex flex-col h-full bg-theme-panel">
      <div className="h-10 border-b border-theme-border flex items-center px-4 shrink-0 bg-theme-header">
        <span className="text-xs font-mono text-theme-accent font-bold uppercase tracking-widest drop-shadow-[0_0_8px_var(--color-accent-glow)]">Variables / Context</span>
        {entries.length !== Object.keys(currentState).length && (
          <span className="ml-auto text-[10px] text-theme-muted font-mono">
            {Object.keys(currentState).length - entries.length} hidden
          </span>
        )}
      </div>

      {/* Call-stack breadcrumb — the deepest frame is the active one. */}
      {stack.length > 0 && (
        <div className="shrink-0 border-b border-theme-border/60 bg-theme-panel-inner px-4 py-2 flex items-center gap-1.5 overflow-x-auto">
          <span className="text-[9px] font-mono text-theme-muted uppercase tracking-widest shrink-0 mr-1">Stack</span>
          {stack.map((frame, i) => {
            const isActive = i === stack.length - 1;
            return (
              <React.Fragment key={`${frame}-${i}`}>
                {i > 0 && <span className="text-theme-muted/50 text-[10px] shrink-0">›</span>}
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded shrink-0 transition-colors ${
                    isActive
                      ? 'text-theme-accent font-bold bg-theme-accent-dim border border-theme-accent/40 drop-shadow-[0_0_6px_var(--color-accent-glow)]'
                      : 'text-theme-muted border border-transparent'
                  }`}
                >
                  {frame}{frame === 'global' ? '' : '()'}
                </span>
              </React.Fragment>
            );
          })}
        </div>
      )}
      <div className="flex-1 overflow-auto p-4 space-y-3">
        {/* Show real runtime error if present */}
        {error && (
          <div className="font-mono text-sm p-3 rounded-lg border border-red-500/30 bg-red-500/10 text-red-400">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-red-500 font-bold text-xs uppercase tracking-wider">Error</span>
            </div>
            <span className="text-red-300 break-all">{error}</span>
          </div>
        )}

        {/* Show intentional truncation warning if execution reached limits */}
        {truncated && (
          <div className="font-mono text-sm p-3 rounded-lg border border-orange-500/30 bg-orange-500/10 text-orange-400">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-orange-500 font-bold text-[10px] uppercase tracking-widest">Execution Limit Reached</span>
            </div>
            <span className="text-orange-300">Debugger step ceiling reached. Partial execution history preserved ({totalSnapshots} snapshots).</span>
          </div>
        )}


        {returnValue !== undefined && (
          <div className="font-mono text-sm p-3 rounded-lg border border-emerald-500/25 bg-emerald-500/10 text-theme-text">
            <div className="text-[10px] text-emerald-400 font-bold uppercase tracking-widest mb-1">
              Return from {currentSnapshot?.function || 'function'}()
            </div>
            <ValueRenderer value={returnValue} depth={0} />
          </div>
        )}

        {traceError && (!error || truncated) && (
          <div className="font-mono text-sm p-3 rounded-lg border border-yellow-500/30 bg-yellow-500/10 text-yellow-400">
            <div className="text-[10px] text-yellow-500 font-bold uppercase tracking-widest mb-1">
              Exception Event
            </div>
            <span className="text-yellow-300 break-all">{traceError}</span>
          </div>
        )}
        
        <AnimatePresence>
          {entries.map(([key, value]) => {
            const prevValue = prevState?.[key];
            const isChanged = prevValue !== undefined && JSON.stringify(prevValue) !== JSON.stringify(value);
            const isNew = prevValue === undefined && Object.keys(prevState).length > 0;
            
            return (
              <motion.div 
                key={key}
                layout
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className={`font-mono text-sm p-3 rounded-lg border transition-all duration-500 ${
                  isNew
                    ? 'border-green-500/50 bg-green-500/10 shadow-[0_0_10px_rgba(34,197,94,0.2)] scale-[1.02]'
                    : isChanged 
                      ? 'border-theme-accent bg-theme-accent-dim shadow-[0_0_15px_var(--color-accent-glow)] scale-[1.02]' 
                      : 'border-theme-border bg-theme-panel-inner shadow-none scale-100'
                }`}
              >
                <div className="flex items-start gap-3">
                  <span className={`shrink-0 ${
                    isNew ? 'text-green-500 font-bold' :
                    isChanged ? 'text-blue-500 font-bold drop-shadow-[0_0_5px_rgba(59,130,246,0.5)]' : 'text-blue-600/70'
                  }`}>{key}</span>
                  <span className="text-theme-muted">=</span>
                  <div className="flex-1 min-w-0">
                    <ValueRenderer value={value} depth={0} />
                    {isChanged && prevValue !== undefined && (
                      <div className="mt-1.5 text-[10px] text-theme-muted line-through opacity-60">
                        {primitivePreview(prevValue)}
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
        
        {/* Reduced mode guidance */}
        {mode === 'reduced' && totalSnapshots <= 2 && totalSnapshots > 0 && !error && (
          <div className="font-mono text-sm p-3 rounded-lg border border-sky-500/30 bg-sky-500/10 text-sky-400">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-sky-500 font-bold text-[10px] uppercase tracking-widest">Reduced Mode</span>
            </div>
            <span className="text-sky-300 text-xs leading-relaxed">
              This program produced {totalSnapshots} semantic event{totalSnapshots !== 1 ? 's' : ''}. 
              Reduced mode only captures explicit <code className="text-sky-200 bg-sky-500/20 px-1 rounded">__semantic_event__()</code> calls. 
              Switch to <strong>SMART</strong> mode for automatic tracing, or add semantic events to track algorithm state.
            </span>
          </div>
        )}

        {entries.length === 0 && !error && !stdout && !(mode === 'reduced' && totalSnapshots <= 2 && totalSnapshots > 0) && (
          <div className="h-full flex items-center justify-center text-theme-muted font-mono text-sm italic">
            Awaiting execution context...
          </div>
        )}

        {/* Stdout display */}
        {stdout && (
          <div className="font-mono text-sm p-3 rounded-lg border border-theme-border/50 bg-black/40 text-theme-text mt-4">
            <div className="flex items-center gap-2 mb-2 pb-1 border-b border-theme-border/30">
              <span className="text-theme-muted font-bold text-[10px] uppercase tracking-widest">Standard Output</span>
            </div>
            <pre className="whitespace-pre-wrap font-mono text-xs text-gray-300 leading-relaxed">{stdout}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
