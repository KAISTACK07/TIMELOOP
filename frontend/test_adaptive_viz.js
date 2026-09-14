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

function assert(condition, message) {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

console.log('=== RUNNING ADAPTIVE VISUALIZATION VALIDATION SUITE ===\n');

// Test 1: Strategy Classification
console.log('Test 1: Strategy classification thresholds');
assert(getVisualizationStrategy(0).strategy === 'FULL', '0 snapshots should be FULL');
assert(getVisualizationStrategy(1).strategy === 'FULL', '1 snapshot should be FULL');
assert(getVisualizationStrategy(2).strategy === 'FULL', '2 snapshots should be FULL');
assert(getVisualizationStrategy(200).strategy === 'FULL', '200 snapshots should be FULL');
assert(getVisualizationStrategy(201).strategy === 'OPTIMIZED', '201 snapshots should be OPTIMIZED');
assert(getVisualizationStrategy(2000).strategy === 'OPTIMIZED', '2000 snapshots should be OPTIMIZED');
assert(getVisualizationStrategy(2001).strategy === 'AGGREGATED', '2001 snapshots should be AGGREGATED');
assert(getVisualizationStrategy(5000).strategy === 'AGGREGATED', '5000 snapshots should be AGGREGATED');
console.log('  ✓ Strategy thresholds correct');

// Test 2: Reduced Mode (0, 1, 2 snapshots)
console.log('Test 2: Reduced mode visible steps (0, 1, 2 snapshots)');
{
  // 1 snapshot: step 0
  const viz = getVisualizationStrategy(1);
  const steps1 = getVisibleSteps({ maxStep: 0, currentStep: 0, viz });
  assert(steps1.length === 1 && steps1[0] === 0, '1 snapshot should return [0]');

  // 2 snapshots: step 0 and step 1
  const viz2 = getVisualizationStrategy(2);
  const steps2 = getVisibleSteps({ maxStep: 1, currentStep: 0, viz: viz2 });
  assert(steps2.length === 2 && steps2[0] === 0 && steps2[1] === 1, '2 snapshots at step 0 should return [0, 1]');
  const steps2b = getVisibleSteps({ maxStep: 1, currentStep: 1, viz: viz2 });
  assert(steps2b.length === 2 && steps2b[0] === 0 && steps2b[1] === 1, '2 snapshots at step 1 should return [0, 1]');
}
console.log('  ✓ Reduced mode visible steps correct');

// Test 3: Optimized Mode (e.g. 500 snapshots)
console.log('Test 3: Optimized mode windowing (500 snapshots)');
{
  const maxStep = 499;
  const viz = getVisualizationStrategy(500);
  
  // At step 0
  const stepsAt0 = getVisibleSteps({ maxStep, currentStep: 0, viz });
  assert(stepsAt0.includes(0), 'Must include step 0');
  assert(stepsAt0.includes(maxStep), 'Must pin last step (499)');
  assert(stepsAt0.length <= WINDOW_RADIUS_OPTIMIZED * 2 + 2, 'Rendered node count must stay bounded');
  assert(stepsAt0.every(s => Number.isInteger(s) && s >= 0 && s <= maxStep), 'All steps must be valid bounded integers');

  // At step 250
  const stepsAt250 = getVisibleSteps({ maxStep, currentStep: 250, viz });
  assert(stepsAt250.includes(250), 'Must include currentStep 250');
  assert(stepsAt250.includes(0) && stepsAt250.includes(maxStep), 'Must pin boundaries');
  assert(stepsAt250.includes(250 - WINDOW_RADIUS_OPTIMIZED) && stepsAt250.includes(250 + WINDOW_RADIUS_OPTIMIZED), 'Must cover window radius');

  // At step 499 (last step)
  const stepsAtLast = getVisibleSteps({ maxStep, currentStep: maxStep, viz });
  assert(stepsAtLast.includes(maxStep), 'Must include last step');
  assert(stepsAtLast.includes(0), 'Must pin step 0');
}
console.log('  ✓ Optimized mode windowing verified');

// Test 4: Aggregated Mode (5000 snapshots, N-Queens N=8)
console.log('Test 4: Aggregated mode (5000 snapshots, N-Queens N=8 simulation)');
{
  const maxStep = 4999;
  const viz = getVisualizationStrategy(5000);
  assert(viz.strategy === 'AGGREGATED', 'Must use AGGREGATED strategy');

  // Simulate mock snapshots with yield events and exceptions
  const mockSnapshots = new Array(5000).fill(null).map((_, i) => ({
    step: i,
    event: i === 1234 ? 'yield' : (i === 4500 ? 'exception' : 'line'),
    value: i === 1234 ? 42 : (i === 4500 ? { message: 'Custom error' } : undefined)
  }));
  const mockExceptions = [{ step: 4500, line_no: 10, message: 'Custom error', type: 'exception' }];
  const exceptionMap = buildExceptionMap(mockExceptions);
  const importantSteps = buildImportantStepsSet(mockSnapshots, exceptionMap);

  assert(importantSteps.has(1234), 'Yield step 1234 must be in importantSteps');
  assert(importantSteps.has(4500), 'Exception step 4500 must be in importantSteps');

  // Test across scrubbing points: 0, 100, 500, 2500, 4998, 4999
  const scrubPoints = [0, 100, 500, 1234, 2500, 4500, 4998, 4999];
  for (const pt of scrubPoints) {
    const visible = getVisibleSteps({ maxStep, currentStep: pt, viz, importantSteps, exceptionMap, snapshots: mockSnapshots });
    assert(visible.includes(pt), `currentStep ${pt} must be in visible steps`);
    assert(visible.includes(0), 'Step 0 must always be pinned');
    assert(visible.includes(maxStep), `Last step ${maxStep} must always be pinned`);
    assert(visible.includes(1234), 'Yield step 1234 must remain pinned even outside window');
    assert(visible.includes(4500), 'Exception step 4500 must remain pinned even outside window');
    assert(visible.length < 300, `DOM node count (${visible.length}) must be strictly < 300 for DOM safety`);
    assert(visible.every(s => Number.isInteger(s) && s >= 0 && s <= maxStep), 'Every step must be integer in [0, 4999]');
  }
}
console.log('  ✓ Aggregated mode for 5000 snapshots strictly limits DOM to < 300 nodes while keeping all steps navigable');

// Test 5: Function Brackets windowing
console.log('Test 5: Function brackets filtering');
{
  const funcs = [
    { name: 'main', start: 0, end: 4999, layer: 0 },
    { name: 'solve', start: 10, end: 4980, layer: 1 },
    { name: 'is_safe', start: 200, end: 250, layer: 2 },
    { name: 'is_safe', start: 2400, end: 2450, layer: 2 },
  ];
  const visSteps = [0, 10, 2400, 2410, 2450, 4999];
  const visFuncs = getVisibleFunctions(funcs, visSteps, 2420, 'AGGREGATED');
  assert(visFuncs.some(f => f.name === 'main'), 'Active main() function must be visible');
  assert(visFuncs.some(f => f.name === 'solve'), 'Active solve() function must be visible');
  assert(visFuncs.some(f => f.name === 'is_safe' && f.start === 2400), 'Active is_safe() at 2420 must be visible');
  assert(!visFuncs.some(f => f.name === 'is_safe' && f.start === 200), 'Inactive is_safe() at 200 must be culled in AGGREGATED');
}
console.log('  ✓ Function brackets filtering verified');

console.log('\n=== ALL VISUALIZATION AND STRATEGY TESTS PASSED! ===');
