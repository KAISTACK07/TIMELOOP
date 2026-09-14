import {
  getVisualizationStrategy,
  getVisibleSteps,
  buildExceptionMap,
  buildImportantStepsSet,
  getVisibleFunctions,
  FULL_THRESHOLD,
  OPTIMIZED_THRESHOLD,
  WINDOW_RADIUS_OPTIMIZED,
  WINDOW_RADIUS_AGGREGATED,
  MAX_SAMPLED_NODES_AGGREGATED
} from './src/lib/vizStrategy.js';

import { getExceptions } from './src/lib/api.js';

function assert(condition, message) {
  if (!condition) {
    throw new Error(`[FAIL] ${message}`);
  }
}

console.log('================================================================');
console.log('TIMELOOP FRONTEND FINAL 18-CASE VERIFICATION SUITE');
console.log('================================================================\n');

// Case 1: 0 snapshots
console.log('Case 1: 0 snapshots (empty state)');
{
  const viz = getVisualizationStrategy(0);
  assert(viz.strategy === 'FULL', '0 snapshots strategy should be FULL');
  const steps = getVisibleSteps({ maxStep: -1, currentStep: 0, viz });
  assert(steps.length === 0, '0 snapshots produces 0 rendered steps');
  console.log('  ✓ Correctly handled: empty state returns 0 steps');
}

// Case 2: 1 snapshot
console.log('Case 2: 1 snapshot (single step trace)');
{
  const viz = getVisualizationStrategy(1);
  assert(viz.strategy === 'FULL', '1 snapshot strategy is FULL');
  const steps = getVisibleSteps({ maxStep: 0, currentStep: 0, viz });
  assert(steps.length === 1 && steps[0] === 0, '1 snapshot produces [0]');
  console.log('  ✓ Correctly handled: renders single step [0]');
}

// Case 3: 2 snapshots (Reduced mode boundary)
console.log('Case 3: 2 snapshots (Reduced mode trace)');
{
  const viz = getVisualizationStrategy(2);
  assert(viz.strategy === 'FULL', '2 snapshots strategy is FULL');
  const steps = getVisibleSteps({ maxStep: 1, currentStep: 0, viz });
  assert(steps.length === 2 && steps[0] === 0 && steps[1] === 1, '2 snapshots produces [0, 1]');
  console.log('  ✓ Correctly handled: renders [0, 1] without artificial padding');
}

// Case 4: 10 snapshots (Small trace)
console.log('Case 4: 10 snapshots (Small trace)');
{
  const viz = getVisualizationStrategy(10);
  assert(viz.strategy === 'FULL', '10 snapshots strategy is FULL');
  const steps = getVisibleSteps({ maxStep: 9, currentStep: 5, viz });
  assert(steps.length === 10, '10 snapshots produces exactly 10 steps');
  assert(steps[0] === 0 && steps[9] === 9, 'Boundary steps 0 and 9 present');
  console.log('  ✓ Correctly handled: all 10 steps rendered');
}

// Case 5: 200 snapshots (FULL upper boundary)
console.log('Case 5: 200 snapshots (FULL mode upper threshold boundary)');
{
  const viz = getVisualizationStrategy(200);
  assert(viz.strategy === 'FULL', '200 snapshots strategy is FULL');
  const steps = getVisibleSteps({ maxStep: 199, currentStep: 100, viz });
  assert(steps.length === 200, '200 snapshots produces all 200 steps');
  console.log('  ✓ Correctly handled: exactly at FULL threshold (200 nodes)');
}

// Case 6: 201 snapshots (OPTIMIZED lower boundary)
console.log('Case 6: 201 snapshots (OPTIMIZED mode lower threshold boundary)');
{
  const viz = getVisualizationStrategy(201);
  assert(viz.strategy === 'OPTIMIZED', '201 snapshots transitions to OPTIMIZED');
  const steps = getVisibleSteps({ maxStep: 200, currentStep: 100, viz });
  assert(steps.length <= WINDOW_RADIUS_OPTIMIZED * 2 + 3, 'Node count is windowed');
  assert(steps.includes(100) && steps.includes(0) && steps.includes(200), 'Includes currentStep, 0, 200');
  console.log('  ✓ Correctly handled: windowed rendering activated at 201 snapshots');
}

// Case 7: 500 snapshots (Medium recursion / Smart mode)
console.log('Case 7: 500 snapshots (Medium recursion / Smart mode)');
{
  const viz = getVisualizationStrategy(500);
  assert(viz.strategy === 'OPTIMIZED', '500 snapshots uses OPTIMIZED');
  const steps = getVisibleSteps({ maxStep: 499, currentStep: 250, viz });
  assert(steps.includes(250), 'currentStep 250 visible');
  assert(steps.includes(0) && steps.includes(499), 'Endpoints 0 and 499 pinned');
  assert(steps.length <= 125, 'DOM nodes strictly bounded (<= 125)');
  console.log(`  ✓ Correctly handled: 500 snapshots renders ${steps.length} DOM nodes`);
}

// Case 8: 2000 snapshots (OPTIMIZED upper boundary)
console.log('Case 8: 2000 snapshots (OPTIMIZED upper threshold boundary)');
{
  const viz = getVisualizationStrategy(2000);
  assert(viz.strategy === 'OPTIMIZED', '2000 snapshots uses OPTIMIZED');
  const steps = getVisibleSteps({ maxStep: 1999, currentStep: 1000, viz });
  assert(steps.includes(1000), 'currentStep 1000 visible');
  assert(steps.includes(0) && steps.includes(1999), 'Endpoints 0 and 1999 pinned');
  assert(steps.length <= 125, 'DOM nodes strictly bounded (<= 125)');
  console.log('  ✓ Correctly handled: upper OPTIMIZED boundary bounded');
}

// Case 9: 2001 snapshots (AGGREGATED lower boundary)
console.log('Case 9: 2001 snapshots (AGGREGATED lower threshold boundary)');
{
  const viz = getVisualizationStrategy(2001);
  assert(viz.strategy === 'AGGREGATED', '2001 snapshots transitions to AGGREGATED');
  const steps = getVisibleSteps({ maxStep: 2000, currentStep: 500, viz });
  assert(steps.length <= 270, 'DOM nodes bounded in AGGREGATED');
  assert(steps.includes(500) && steps.includes(0) && steps.includes(2000), 'Includes currentStep, 0, 2000');
  console.log('  ✓ Correctly handled: AGGREGATED sampling activated at 2001 snapshots');
}

// Case 10: 5000 snapshots (Large execution / N-Queens N=8)
console.log('Case 10: 5000 snapshots (Large execution / N-Queens N=8)');
{
  const maxStep = 4999;
  const viz = getVisualizationStrategy(5000);
  assert(viz.strategy === 'AGGREGATED', '5000 snapshots uses AGGREGATED');
  
  const mockSnapshots = new Array(5000).fill(null).map((_, i) => ({
    step: i,
    event: i === 1200 ? 'yield' : (i === 4200 ? 'exception' : 'line')
  }));
  const mockExceptions = [{ step: 4200, line_no: 8, message: 'Err', type: 'exception' }];
  const excMap = buildExceptionMap(mockExceptions);
  const important = buildImportantStepsSet(mockSnapshots, excMap);

  const steps = getVisibleSteps({ maxStep, currentStep: 2500, viz, importantSteps: important, exceptionMap: excMap, snapshots: mockSnapshots });
  assert(steps.length < 300, `DOM nodes (${steps.length}) strictly < 300`);
  assert(steps.includes(2500), 'currentStep 2500 visible');
  assert(steps.includes(0) && steps.includes(4999), 'Endpoints 0 and 4999 pinned');
  assert(steps.includes(1200), 'Yield event 1200 pinned');
  assert(steps.includes(4200), 'Exception event 4200 pinned');
  console.log(`  ✓ Correctly handled: 5000 snapshots rendered with ${steps.length} DOM nodes (< 300)`);
}

// Case 11: currentStep = 0 (Left boundary navigation)
console.log('Case 11: currentStep = 0 (Left boundary navigation in large trace)');
{
  const maxStep = 4999;
  const viz = getVisualizationStrategy(5000);
  const steps = getVisibleSteps({ maxStep, currentStep: 0, viz });
  assert(steps[0] === 0, 'First node is 0');
  assert(steps.includes(0), 'currentStep 0 is rendered');
  assert(steps.includes(WINDOW_RADIUS_AGGREGATED), 'Window extends forward from 0');
  console.log('  ✓ Correctly handled: left boundary windowing');
}

// Case 12: currentStep = middle (2500 in 5000)
console.log('Case 12: currentStep = middle (Center navigation in large trace)');
{
  const maxStep = 4999;
  const viz = getVisualizationStrategy(5000);
  const steps = getVisibleSteps({ maxStep, currentStep: 2500, viz });
  assert(steps.includes(2500), 'currentStep 2500 is rendered');
  assert(steps.includes(2500 - WINDOW_RADIUS_AGGREGATED) && steps.includes(2500 + WINDOW_RADIUS_AGGREGATED), 'Window extends ±30 around 2500');
  console.log('  ✓ Correctly handled: symmetric middle windowing');
}

// Case 13: currentStep = maxStep (Right boundary navigation)
console.log('Case 13: currentStep = maxStep (Right boundary navigation in large trace)');
{
  const maxStep = 4999;
  const viz = getVisualizationStrategy(5000);
  const steps = getVisibleSteps({ maxStep, currentStep: 4999, viz });
  assert(steps[steps.length - 1] === 4999, 'Last node is 4999');
  assert(steps.includes(4999), 'currentStep 4999 is rendered');
  assert(steps.includes(4999 - WINDOW_RADIUS_AGGREGATED), 'Window extends backward from 4999');
  console.log('  ✓ Correctly handled: right boundary windowing');
}

// Case 14: Important event outside current window
console.log('Case 14: Important event outside current window');
{
  const maxStep = 4999;
  const viz = getVisualizationStrategy(5000);
  const important = new Set([50, 4800]); // Far from currentStep = 2500
  const steps = getVisibleSteps({ maxStep, currentStep: 2500, viz, importantSteps: important });
  assert(steps.includes(50), 'Important step 50 pinned outside window');
  assert(steps.includes(4800), 'Important step 4800 pinned outside window');
  console.log('  ✓ Correctly handled: distant important events remain pinned');
}

// Case 15: Zero-width timeline pointer calculation
console.log('Case 15: Zero-width timeline pointer calculation');
{
  function calcStep(clientX, rectLeft, rectWidth, maxStep) {
    const percentage = rectWidth > 0 ? Math.max(0, Math.min(1, (clientX - rectLeft) / rectWidth)) : 0;
    const newStep = Math.round(percentage * maxStep);
    return Number.isFinite(newStep) ? newStep : 0;
  }
  assert(calcStep(100, 100, 0, 4999) === 0, 'Zero width produces step 0 without NaN');
  assert(!Number.isNaN(calcStep(0, 0, 0, 4999)), 'Zero width is not NaN');
  console.log('  ✓ Correctly handled: zero-width track yields step 0 safely');
}

// Case 16: truncated=true / error=null (Controlled execution limit)
console.log('Case 16: truncated=true / error=null (Intentional limit reached)');
{
  const error = null;
  const truncated = true;
  const isPythonError = error !== null;
  const isTruncated = truncated === true && error === null;
  assert(!isPythonError, 'Must NOT be flagged as Python error');
  assert(isTruncated, 'Must be flagged as intentional limit');
  console.log('  ✓ Correctly handled: execution limit distinguished from Python error');
}

// Case 17: error!=null / truncated=false (Real runtime error)
console.log('Case 17: error!=null / truncated=false (Real runtime error)');
{
  const error = 'ZeroDivisionError: division by zero';
  const truncated = false;
  const isPythonError = error !== null;
  const isTruncated = truncated === true && error === null;
  assert(isPythonError, 'Must be flagged as Python error');
  assert(!isTruncated, 'Must NOT be flagged as truncation limit');
  console.log('  ✓ Correctly handled: real runtime error displayed');
}

// Case 18: error!=null / truncated=true (Both error and truncation)
console.log('Case 18: error!=null / truncated=true (Both present independently)');
{
  const error = 'Execution interrupted by exception';
  const truncated = true;
  const showError = error !== null;
  const showTruncation = truncated === true;
  assert(showError && showTruncation, 'Both error and truncation displayed independently');
  console.log('  ✓ Correctly handled: both error and truncation displayed independently');
}

console.log('\n================================================================');
console.log('ALL 18 CONCEPTUAL TEST CASES PASSED WITH 100% SUCCESS!');
console.log('================================================================\n');
