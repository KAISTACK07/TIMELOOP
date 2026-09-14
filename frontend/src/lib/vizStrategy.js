/**
 * vizStrategy.js — Centralized Adaptive Visualization Strategy
 *
 * Determines rendering strategy based on execution complexity.
 * This is the SINGLE source of truth for visualization thresholds.
 *
 * Strategies:
 *   FULL       — small executions: every step rendered, full animation
 *   OPTIMIZED  — medium executions: windowed rendering, animate visible region
 *   AGGREGATED — large executions: sampled representative nodes, phase-aware
 */

// ── Thresholds ──────────────────────────────────────────────
export const FULL_THRESHOLD = 200;
export const OPTIMIZED_THRESHOLD = 2000;

// ── Window sizes per strategy ───────────────────────────────
export const WINDOW_RADIUS_OPTIMIZED = 60;
export const WINDOW_RADIUS_AGGREGATED = 30;
export const MAX_SAMPLED_NODES_AGGREGATED = 200;

/**
 * Determine visualization strategy from snapshot count.
 * @param {number} snapshotCount
 * @returns {{ strategy: string, windowRadius: number, maxRenderedNodes: number }}
 */
export function getVisualizationStrategy(snapshotCount) {
  if (snapshotCount <= FULL_THRESHOLD) {
    return {
      strategy: 'FULL',
      windowRadius: Infinity,   // render all
      maxRenderedNodes: snapshotCount,
    };
  }
  if (snapshotCount <= OPTIMIZED_THRESHOLD) {
    return {
      strategy: 'OPTIMIZED',
      windowRadius: WINDOW_RADIUS_OPTIMIZED,
      maxRenderedNodes: WINDOW_RADIUS_OPTIMIZED * 2 + 1,
    };
  }
  return {
    strategy: 'AGGREGATED',
    windowRadius: WINDOW_RADIUS_AGGREGATED,
    maxRenderedNodes: MAX_SAMPLED_NODES_AGGREGATED,
  };
}

/**
 * Build a pre-computed Map of step → exception for O(1) lookups.
 * @param {object[]} exceptions
 * @returns {Map<number, object>}
 */
export function buildExceptionMap(exceptions) {
  const map = new Map();
  if (!exceptions || !Array.isArray(exceptions)) return map;
  for (const exc of exceptions) {
    if (typeof exc.step === 'number') {
      map.set(exc.step, exc);
    }
  }
  return map;
}

/**
 * Pre-computes a Set of important step indices (exceptions, yields)
 * once per execution dataset change to prevent O(N) scans on every scrub event.
 * @param {object[]} snapshots
 * @param {Map<number, object>|object[]} exceptions
 * @returns {Set<number>}
 */
export function buildImportantStepsSet(snapshots, exceptions) {
  const set = new Set();

  if (exceptions instanceof Map) {
    for (const step of exceptions.keys()) {
      set.add(step);
    }
  } else if (Array.isArray(exceptions)) {
    for (const exc of exceptions) {
      if (typeof exc.step === 'number') set.add(exc.step);
    }
  }

  if (Array.isArray(snapshots)) {
    for (let i = 0; i < snapshots.length; i++) {
      const snap = snapshots[i];
      if (snap && (snap.event === 'yield' || snap.event === 'exception' || snap.event === 'exception_handled')) {
        set.add(i);
      }
    }
  }

  return set;
}

/**
 * Build the set of step indices that should be rendered as DOM nodes.
 *
 * For FULL: every step.
 * For OPTIMIZED: window around currentStep + pinned important events.
 * For AGGREGATED: evenly-sampled subset + window + pinned events.
 *
 * @param {object} params
 * @param {number} params.maxStep
 * @param {number} params.currentStep
 * @param {object} params.viz - strategy from getVisualizationStrategy
 * @param {Set<number>} [params.importantSteps] - pre-indexed important step numbers
 * @param {Map<number,object>} [params.exceptionMap] - fallback step→exception
 * @param {object[]} [params.snapshots] - full snapshot array
 * @returns {number[]} sorted array of integer step indices to render
 */
export function getVisibleSteps({
  maxStep,
  currentStep,
  viz,
  importantSteps,
  exceptionMap,
  snapshots,
}) {
  if (maxStep < 0) return [];
  
  if (viz.strategy === 'FULL') {
    const steps = [];
    for (let i = 0; i <= maxStep; i++) steps.push(i);
    return steps;
  }

  const visible = new Set();

  // 1. Sliding window around current step
  const radius = typeof viz.windowRadius === 'number' && Number.isFinite(viz.windowRadius) 
    ? viz.windowRadius 
    : WINDOW_RADIUS_OPTIMIZED;
  const lo = Math.max(0, currentStep - radius);
  const hi = Math.min(maxStep, currentStep + radius);
  for (let i = lo; i <= hi; i++) visible.add(i);

  // 2. Always pin boundaries (first and last step)
  visible.add(0);
  visible.add(maxStep);

  // 3. Always include currentStep explicitly
  if (currentStep >= 0 && currentStep <= maxStep) {
    visible.add(currentStep);
  }

  // 4. Pin important steps (O(1) iteration over pre-computed Set)
  if (importantSteps instanceof Set) {
    for (const step of importantSteps) {
      if (step >= 0 && step <= maxStep) {
        visible.add(step);
      }
    }
  } else {
    // Fallback if importantSteps is not supplied
    if (exceptionMap) {
      for (const step of exceptionMap.keys()) {
        if (step >= 0 && step <= maxStep) visible.add(step);
      }
    }
    if (snapshots && snapshots.length <= 500) {
      for (let i = 0; i <= maxStep && i < snapshots.length; i++) {
        const snap = snapshots[i];
        if (snap && (snap.event === 'yield' || snap.event === 'exception' || snap.event === 'exception_handled')) {
          visible.add(i);
        }
      }
    }
  }

  // 5. For AGGREGATED, add evenly-spaced sample points
  if (viz.strategy === 'AGGREGATED' && maxStep > 0) {
    const sampleCount = Math.min(MAX_SAMPLED_NODES_AGGREGATED, maxStep + 1);
    const interval = maxStep / Math.max(1, sampleCount - 1);
    for (let i = 0; i < sampleCount; i++) {
      const idx = Math.min(maxStep, Math.max(0, Math.round(i * interval)));
      visible.add(idx);
    }
  }

  return Array.from(visible).sort((a, b) => a - b);
}

/**
 * Filter function calls to only those overlapping the visible window.
 * @param {object[]} layeredFunctions - with start, end, layer
 * @param {number[]} visibleSteps - sorted visible step indices
 * @param {number} currentStep
 * @param {string} strategy
 * @returns {object[]}
 */
export function getVisibleFunctions(layeredFunctions, visibleSteps, currentStep, strategy) {
  if (!layeredFunctions || layeredFunctions.length === 0) return [];
  if (strategy === 'FULL') return layeredFunctions;

  // For AGGREGATED: show active functions at currentStep and functions overlapping current window
  if (strategy === 'AGGREGATED') {
    return layeredFunctions.filter(
      f => f.start <= currentStep && currentStep <= f.end
    );
  }

  // For OPTIMIZED: show functions overlapping the visible range
  if (visibleSteps.length === 0) return [];
  const visMin = visibleSteps[0];
  const visMax = visibleSteps[visibleSteps.length - 1];

  return layeredFunctions.filter(
    f => f.end >= visMin && f.start <= visMax
  );
}

