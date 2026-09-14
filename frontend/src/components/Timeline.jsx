import React, { useRef, useState, useMemo, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  getVisualizationStrategy,
  getVisibleSteps,
  buildExceptionMap,
  buildImportantStepsSet,
  getVisibleFunctions,
} from '../lib/vizStrategy.js';

/* ═══════════════════════════════════════════════════════════
   SpiderKnob — the animated draggable execution marker
   ═══════════════════════════════════════════════════════════ */
const SpiderKnob = ({ isDragging }) => (
  <div className="relative w-16 h-16 flex items-center justify-center -top-2">
    {/* Symbiote aura/glow behind the spider */}
    <div 
      className={`absolute inset-0 bg-theme-text/40 blur-xl rounded-full transition-all duration-200 ${
        isDragging ? 'opacity-100 scale-150' : 'opacity-0 scale-100'
      }`} 
    />
    
    <motion.div 
      className="w-full h-full relative z-10 drop-shadow-[0_4px_6px_rgba(0,0,0,0.8)]"
      animate={{ scale: isDragging ? 1.15 : 1, rotate: isDragging ? -8 : 0 }}
      transition={{ type: "spring", stiffness: 400, damping: 20 }}
    >
      <img 
        src="/venom__logo___png_by_jt525pro_df7i4wt-375w-2x.png" 
        alt="Spider Knob"
        className="w-full h-full object-contain drop-shadow-md pointer-events-none select-none filter invert dark:invert-0"
      />
    </motion.div>
  </div>
);

/* ═══════════════════════════════════════════════════════════
   WebTrackSVG — the animated web-fluid timeline track
   ═══════════════════════════════════════════════════════════ */
const WebTrackSVG = React.memo(({ active }) => (
  <svg 
    viewBox="0 0 1000 40" 
    preserveAspectRatio="none" 
    className="w-full h-12"
  >
    <defs>
      <filter id="webGlow" x="-20%" y="-20%" width="140%" height="140%">
        <feGaussianBlur stdDeviation={active ? "5" : "0"} result="blur" />
        <feComponentTransfer in="blur" result="glow">
          <feFuncA type="linear" slope="2" />
        </feComponentTransfer>
        <feMerge>
          <feMergeNode in="glow" />
          <feMergeNode in="SourceGraphic" />
        </feMerge>
      </filter>
    </defs>
    
    <g filter={active ? "url(#webGlow)" : ""}>
      <motion.path 
        fill="none" 
        stroke={active ? "var(--color-accent)" : "var(--color-border)"} 
        strokeWidth={active ? 5 : 2} 
        strokeLinecap="round"
        animate={{
          d: [
            "M0,20 Q 250,15 500,20 T 1000,20",
            "M0,20 Q 250,25 500,20 T 1000,20",
            "M0,20 Q 250,15 500,20 T 1000,20"
          ]
        }}
        transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
      />
      
      <motion.path 
        fill="none" 
        stroke={active ? "var(--color-accent)" : "var(--color-border)"} 
        strokeWidth={active ? 3 : 1}
        animate={{
          d: [
            "M0,20 Q 150,25 300,18 T 600,22 T 1000,20",
            "M0,20 Q 150,15 300,22 T 600,18 T 1000,20",
            "M0,20 Q 150,25 300,18 T 600,22 T 1000,20"
          ]
        }}
        transition={{ repeat: Infinity, duration: 5, ease: "easeInOut" }}
      />
      
      <motion.path 
        fill="none" 
        stroke={active ? "var(--color-accent)" : "var(--color-border)"} 
        strokeWidth={active ? 2 : 0.5} 
        animate={{
          d: [
            "M0,18 Q 200,10 400,22 T 800,15 T 1000,20",
            "M0,22 Q 200,26 400,18 T 800,25 T 1000,20",
            "M0,18 Q 200,10 400,22 T 800,15 T 1000,20"
          ]
        }}
        transition={{ repeat: Infinity, duration: 6, ease: "easeInOut" }}
      />
      
      {/* Web straggles */}
      <motion.path 
        fill="none" stroke={active ? "var(--color-accent)" : "var(--color-border)"} strokeWidth={active ? 1.5 : 0.5}
        animate={{ d: ["M 100,20 Q 110,30 120,20", "M 100,20 Q 115,35 120,20", "M 100,20 Q 110,30 120,20"] }}
        transition={{ repeat: Infinity, duration: 2.5, ease: "easeInOut" }}
      />
      <motion.path 
        fill="none" stroke={active ? "var(--color-accent)" : "var(--color-border)"} strokeWidth={active ? 1.5 : 0.5}
        animate={{ d: ["M 350,18 Q 360,8 380,21", "M 350,18 Q 365,5 380,21", "M 350,18 Q 360,8 380,21"] }}
        transition={{ repeat: Infinity, duration: 3.2, ease: "easeInOut" }}
      />
      <motion.path 
        fill="none" stroke={active ? "var(--color-accent)" : "var(--color-border)"} strokeWidth={active ? 1.5 : 0.5}
        animate={{ d: ["M 650,22 Q 670,35 690,19", "M 650,22 Q 675,40 690,19", "M 650,22 Q 670,35 690,19"] }}
        transition={{ repeat: Infinity, duration: 2.8, ease: "easeInOut" }}
      />
    </g>
  </svg>
));

/* ═══════════════════════════════════════════════════════════
   StepNode — a single memoized timeline dot
   ═══════════════════════════════════════════════════════════ */
const StepNode = React.memo(({ step, percent, isActive, exception, isYield, snap }) => (
  <div 
    className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 flex justify-center items-center group/node pointer-events-auto"
    style={{ left: `${percent}%` }}
  >
    <div className="absolute -inset-2" /> {/* Hover target expansion */}
    <div className={`rounded-full transition-colors duration-300 ${
      exception 
        ? (exception.type === 'exception_handled' 
            ? 'bg-orange-500 shadow-[0_0_12px_rgba(249,115,22,0.8)] z-10 w-2 h-2' 
            : 'bg-red-500 shadow-[0_0_12px_rgba(239,68,68,0.8)] z-10 w-3 h-3 border-2 border-[var(--color-bg)]')
        : isYield
          ? 'bg-purple-500 shadow-[0_0_8px_rgba(168,85,247,0.8)] z-10 w-2 h-2'
          : isActive 
            ? 'bg-theme-text shadow-[0_0_8px_var(--color-text-glow)] w-1.5 h-1.5' 
            : 'bg-theme-muted w-1.5 h-1.5 opacity-40'
    }`} />
    
    {/* Exception Tooltip */}
    {exception && (
      <div className={`absolute bottom-full mb-3 whitespace-nowrap border text-[10px] font-mono px-3 py-1.5 rounded backdrop-blur-md opacity-0 group-hover/node:opacity-100 transition-opacity z-50 pointer-events-none ${
        exception.type === 'exception_handled' 
          ? 'bg-orange-500/10 border-orange-500/50 text-orange-600 dark:text-orange-200 shadow-[0_0_15px_rgba(249,115,22,0.2)]' 
          : 'bg-red-500/10 border-red-500/50 text-red-600 dark:text-red-200 shadow-[0_0_15px_rgba(239,68,68,0.2)]'
      }`}>
        <div className={`absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 rotate-45 border-r border-b ${
          exception.type === 'exception_handled' ? 'bg-orange-500/50 border-orange-500/50' : 'bg-red-500/50 border-red-500/50'
        }`}></div>
        {exception.message}
      </div>
    )}
    
    {/* Yield Tooltip */}
    {isYield && !exception && (
      <div className="absolute bottom-full mb-3 whitespace-nowrap bg-purple-500/10 border border-purple-500/50 text-purple-600 dark:text-purple-200 text-[10px] font-mono px-3 py-1.5 rounded backdrop-blur-md shadow-[0_0_15px_rgba(168,85,247,0.2)] opacity-0 group-hover/node:opacity-100 transition-opacity z-50 pointer-events-none">
        <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-purple-500/50 rotate-45 border-r border-b border-purple-500/50"></div>
        Yield: {snap?.value !== undefined ? String(snap.value) : 'None'}
      </div>
    )}
  </div>
));

/* ═══════════════════════════════════════════════════════════
   FunctionBracket — a single function call overlay
   ═══════════════════════════════════════════════════════════ */
const FunctionBracket = React.memo(({ func, getPercent, isActive, isDeepestActive }) => {
  const startPercent = getPercent(func.start);
  const endPercent = getPercent(func.end);
  const widthPercent = Math.max(0.5, endPercent - startPercent);
  
  return (
    <div 
      className={`absolute flex items-end transition-all duration-300 ${
        isDeepestActive 
          ? 'text-theme-accent z-20 opacity-100' 
          : isActive 
            ? 'text-theme-accent opacity-40 z-10' 
            : 'text-theme-muted opacity-10 z-0'
      }`}
      style={{ 
        left: `${startPercent}%`, 
        width: `${widthPercent}%`,
        bottom: `${func.layer * 22}px`,
        height: '20px'
      }}
    >
      <div className="w-px h-full bg-current relative opacity-60">
        <div className="absolute top-0 -left-1 w-2 h-px bg-current"></div>
      </div>
      <div className="flex-1 h-px bg-current self-start opacity-60"></div>
      <span className={`px-2 text-[10px] font-mono bg-theme-timeline transition-colors self-start -mt-2 whitespace-nowrap ${
        isDeepestActive 
          ? 'text-theme-text font-bold drop-shadow-[0_0_8px_var(--color-accent)] border border-theme-accent/50 rounded px-2 py-0.5 bg-theme-accent-dim shadow-[0_0_10px_var(--color-accent-glow)]' 
          : 'text-current'
      }`}>
        {func.name}()
      </span>
      <div className="flex-1 h-px bg-current self-start opacity-60"></div>
      <div className="w-px h-full bg-current relative opacity-60">
        <div className="absolute top-0 -right-1 w-2 h-px bg-current"></div>
      </div>
    </div>
  );
});

/* ═══════════════════════════════════════════════════════════
   Timeline — Main Component (Adaptive Rendering)
   ═══════════════════════════════════════════════════════════ */
export default function Timeline({ 
  currentStep, 
  maxStep, 
  snapshots, 
  functionCalls, 
  exceptions, 
  onStepChange 
}) {
  const trackRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  
  // ── Adaptive Strategy ──────────────────────────────────
  const viz = useMemo(
    () => getVisualizationStrategy(maxStep + 1),
    [maxStep]
  );

  // ── Pre-compute exception map (O(1) lookup) ───────────
  const exceptionMap = useMemo(
    () => buildExceptionMap(exceptions),
    [exceptions]
  );

  // ── Pre-compute important step indices (O(1) iteration) ─
  const importantSteps = useMemo(
    () => buildImportantStepsSet(snapshots, exceptionMap),
    [snapshots, exceptionMap]
  );

  // ── Deterministic function layering ────────────────────
  const layeredFunctions = useMemo(() => {
    if (!functionCalls || functionCalls.length === 0) return [];
    
    const sorted = [...functionCalls].sort((a, b) => a.start - b.start);
    const layered = [];
    
    sorted.forEach(func => {
      let assignedLayer = 0;
      while (layered.some(lFunc => lFunc.layer === assignedLayer && 
                          Math.max(func.start, lFunc.start) <= Math.min(func.end, lFunc.end))) {
        assignedLayer++;
      }
      layered.push({ ...func, layer: assignedLayer });
    });
    return layered;
  }, [functionCalls]);

  const maxLayer = layeredFunctions.reduce((max, f) => Math.max(max, f.layer), -1);
  const functionAreaHeight = (maxLayer + 1) * 24;

  // ── Active function detection ──────────────────────────
  const { activeFunction, deepestActiveLayer } = useMemo(() => {
    const actives = layeredFunctions.filter(f => f.start <= currentStep && currentStep <= f.end);
    const deepest = actives.length > 0 
      ? actives.sort((a, b) => b.layer - a.layer)[0] 
      : null;
    return {
      activeFunction: deepest,
      deepestActiveLayer: deepest ? deepest.layer : -1,
    };
  }, [layeredFunctions, currentStep]);

  // ── Visible steps (windowed) ───────────────────────────
  const visibleSteps = useMemo(
    () => getVisibleSteps({ maxStep, currentStep, viz, importantSteps, exceptionMap, snapshots }),
    [maxStep, currentStep, viz, importantSteps, exceptionMap, snapshots]
  );

  // ── Visible function brackets ──────────────────────────
  const visibleFunctions = useMemo(
    () => getVisibleFunctions(layeredFunctions, visibleSteps, currentStep, viz.strategy),
    [layeredFunctions, visibleSteps, currentStep, viz.strategy]
  );

  // ── Position calculation (stable) ─────────────────────
  const getPercent = useCallback(
    (step) => (step / Math.max(1, maxStep)) * 100,
    [maxStep]
  );

  const progressPercent = getPercent(currentStep);

  // ── Pointer interaction ────────────────────────────────
  const updateStepFromEvent = useCallback((e) => {
    if (!trackRef.current) return;
    const rect = trackRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = rect.width > 0 ? Math.max(0, Math.min(1, x / rect.width)) : 0;
    const newStep = Math.round(percentage * maxStep);
    if (Number.isFinite(newStep) && newStep !== currentStep) {
      onStepChange(newStep);
    }
  }, [maxStep, currentStep, onStepChange]);

  const handlePointerDown = useCallback((e) => {
    setIsDragging(true);
    updateStepFromEvent(e);
    if (e.currentTarget.setPointerCapture) {
      e.currentTarget.setPointerCapture(e.pointerId);
    }
  }, [updateStepFromEvent]);

  const handlePointerMove = useCallback((e) => {
    if (isDragging) {
      updateStepFromEvent(e);
    }
  }, [isDragging, updateStepFromEvent]);

  const handlePointerUp = useCallback((e) => {
    setIsDragging(false);
    if (e.currentTarget.hasPointerCapture && e.currentTarget.hasPointerCapture(e.pointerId)) {
      e.currentTarget.releasePointerCapture(e.pointerId);
    }
  }, []);


  // ── Empty state ────────────────────────────────────────
  if (maxStep === 0 && (!snapshots || snapshots.length === 0)) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-theme-muted font-mono text-sm bg-theme-timeline">
        <div className="w-12 h-12 border-2 border-theme-border rounded-full flex items-center justify-center mb-4 relative">
          <div className="absolute inset-0 rounded-full bg-theme-accent opacity-20 animate-ping"></div>
          <div className="w-2 h-2 bg-theme-accent rounded-full"></div>
        </div>
        Timeline inactive. Run execution to generate trace.
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col select-none">
      <div className="flex justify-between items-center mb-4 shrink-0">
        <h3 className="text-xs font-mono text-theme-muted uppercase tracking-widest flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-theme-accent animate-pulse shadow-[0_0_8px_var(--color-accent)]"></div>
          Execution Controller
          {viz.strategy !== 'FULL' && (
            <span className="ml-2 text-[9px] px-2 py-0.5 rounded border border-theme-border text-theme-muted bg-theme-panel">
              {viz.strategy === 'OPTIMIZED' ? '⚡ Windowed' : '⚡ Adaptive'} — {visibleSteps.length} / {maxStep + 1} nodes
            </span>
          )}
        </h3>
        <div className="font-mono text-theme-accent text-xs bg-theme-accent-dim px-3 py-1.5 rounded border border-theme-accent shadow-[0_0_10px_var(--color-accent-glow)]">
          STEP <span className="text-theme-text font-bold">{currentStep}</span> / {maxStep}
        </div>
      </div>

      <div className="flex-1 relative flex flex-col justify-center px-8 pb-4">
        
        {/* Layer 4: Function Overlays */}
        <div 
          className="relative w-full mb-0 pointer-events-none"
          style={{ height: `${functionAreaHeight}px` }}
        >
          {visibleFunctions.map((func, idx) => {
            const isActive = func.start <= currentStep && currentStep <= func.end;
            const isDeepestActive = isActive && func.layer === deepestActiveLayer;
            
            return (
              <FunctionBracket
                key={`${func.name}-${func.start}-${func.end}`}
                func={func}
                getPercent={getPercent}
                isActive={isActive}
                isDeepestActive={isDeepestActive}
              />
            );
          })}
        </div>

        {/* The Scrubbable Track Area */}
        <div 
          className="relative w-full h-16 flex items-center cursor-pointer group"
          ref={trackRef}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerCancel={handlePointerUp}
        >
          {/* Background track */}
          <div className="absolute inset-0 flex items-center pointer-events-none opacity-80">
            <WebTrackSVG active={false} />
          </div>

          {/* Active track */}
          <div 
            className="absolute inset-0 flex items-center pointer-events-none will-change-[clip-path]"
            style={{ clipPath: `inset(0 ${100 - progressPercent}% 0 0)` }}
          >
            <WebTrackSVG active={true} />
          </div>

          {/* Step Nodes — only visible window rendered */}
          <div className="absolute inset-0 pointer-events-none z-10">
            {visibleSteps.map((step) => {
              const snap = snapshots[step];
              const exception = exceptionMap.get(step);
              const isYield = snap?.event === 'yield';
              const isActive = step <= currentStep;
              const percent = getPercent(step);
              
              return (
                <StepNode
                  key={step}
                  step={step}
                  percent={percent}
                  isActive={isActive}
                  exception={exception}
                  isYield={isYield}
                  snap={snap}
                />
              );
            })}
          </div>

          {/* SpiderKnob */}
          <div 
            className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 z-20 pointer-events-none will-change-[left]"
            style={{ left: `${progressPercent}%` }}
          >
            <SpiderKnob isDragging={isDragging} />
          </div>
        </div>
      </div>
    </div>
  );
}