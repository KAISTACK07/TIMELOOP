const API_URL = 'http://127.0.0.1:8000';

export const executeCode = async (code, mode = 'smart') => {
  try {
    const response = await fetch(`${API_URL}/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ code, mode }),
    });
    
    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Execution failed (${response.status}): ${text}`);
    }
    
    const data = await response.json();
    
    const snapshots = data.snapshots || [];
    
    // Max step is the length of the snapshots array minus 1 (used as index)
    const maxStep = snapshots.length > 0 
      ? snapshots.length - 1
      : 0;
      
    return {
      session_id: data.session_id,
      maxStep: maxStep,
      snapshots: snapshots,
      error: data.error || null,
      truncated: data.truncated || false,
      stdout: data.stdout || ''
    };
  } catch (error) {
    console.error("Error executing code:", error);
    throw error;
  }
};

export const getState = async (sessionId, step) => {
  try {
    const response = await fetch(
      `${API_URL}/state?session_id=${encodeURIComponent(sessionId)}&step=${step}`
    );
    if (!response.ok) {
      console.warn("getState failed:", response.status);
      return {};
    }
    const data = await response.json();
    if (data.error) {
      console.warn("getState error:", data.error);
      return {};
    }
    return data.state || {};
  } catch (error) {
    console.error("Error fetching state:", error);
    return {};
  }
};

export const getFunctionCalls = async (sessionId, snapshots) => {
  // Derive function call ranges directly from snapshot events
  if (!snapshots || snapshots.length === 0) return [];
  
  const calls = [];
  const callStack = []; // stack of {name, startIndex}
  
  snapshots.forEach((snap, index) => {
    if (snap.event === 'call') {
      callStack.push({ name: snap.function || 'unknown', startIndex: index });
    } else if (snap.event === 'return' || snap.event === 'exception_unwind') {
      const call = callStack.pop();
      if (call) {
        calls.push({ 
          name: call.name, 
          start: call.startIndex, 
          end: index 
        });
      }
    }
  });
  
  // Close any unclosed calls (functions that didn't return)
  const maxIndex = snapshots.length - 1;
  while (callStack.length > 0) {
    const call = callStack.pop();
    calls.push({ 
      name: call.name, 
      start: call.startIndex, 
      end: maxIndex 
    });
  }
  
  return calls;
};

export const getExceptions = (snapshots = []) => {
  if (!Array.isArray(snapshots)) return [];
  const exceptions = [];
  snapshots.forEach((snap, index) => {
    if (snap.event === 'exception' || snap.event === 'exception_handled') {
      const isHandled = snap.event === 'exception_handled';
      let message = isHandled ? 'Handled Exception' : 'Exception occurred';
      
      if (snap.value && typeof snap.value === 'object') {
        if (isHandled) {
          message = `Handled: ${snap.value.exception_type || 'Exception'}`;
        } else if (snap.value.message) {
          message = snap.value.exception_type 
            ? `${snap.value.exception_type}: ${snap.value.message}`
            : snap.value.message;
        } else if (snap.value.exception_type) {
          message = snap.value.exception_type;
        }
      } else if (typeof snap.value === 'string' && snap.value.trim().length > 0) {
        message = snap.value;
      }

      exceptions.push({
        step: index, // map directly to timeline index
        line_no: snap.line_no,
        message: message,
        type: snap.event
      });
    }
  });
  return exceptions;
};

/**
 * Send structured debugger context to the AI explanation endpoint.
 * Note: API keys are securely managed server-side. No client secrets are stored here.
 * @param {object} context
 * @param {string} context.code
 * @param {number} context.currentLine
 * @param {object} [context.snapshot]
 * @param {object} [context.variables]
 * @param {string[]} [context.stack]
 * @param {string} [context.mode]
 * @returns {Promise<object>}
 */
export const explainCode = async (context) => {
  try {
    const response = await fetch(`${API_URL}/explain`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        code: context.code || '',
        current_line: context.currentLine || 0,
        snapshot: context.snapshot || null,
        variables: context.variables || {},
        stack: context.stack || [],
        mode: context.mode || 'smart'
      }),
    });

    if (response.ok) {
      return await response.json();
    }
  } catch {
    // If backend endpoint is not yet available, provide local structured heuristic analysis
  }

  // Graceful client fallback analyzer when backend AI endpoint is in standby
  return generateClientAnalysis(context);
};

/**
 * Heuristic code analysis fallback when external backend LLM is unreachable.
 */
function generateClientAnalysis({ code, currentLine, snapshot, variables }) {
  const codeLines = (code || '').split('\n');
  const hasNestedLoops = /for\s+.*:\s*\n\s+for\s+.*:/m.test(code) || /for\s+.*in.*:\s*.*for\s+.*in/m.test(code);
  const hasRecursion = (snapshot?.stack && snapshot.stack.length > 2) || /def\s+(\w+)\(.*\):[\s\S]*?\1\(/.test(code);
  const hasBacktracking = /board\.pop\(\)|\.remove\(|undo/i.test(code);

  let timeComplexity = 'O(n)';
  let spaceComplexity = 'O(1)';
  let issue = 'Linear execution path observed.';
  let optimization = 'Algorithm is operating within standard complexity bounds.';
  let expectedComplexity = 'O(n)';
  let optimizedCode = code;

  if (hasNestedLoops) {
    timeComplexity = 'O(n²)';
    spaceComplexity = 'O(1)';
    issue = 'Nested iteration detected. Inner loop repeatedly scans or iterates over the collection for every outer loop element.';
    optimization = 'Utilize a hash set, dictionary lookup, or two-pointer approach to eliminate redundant inner loop scans.';
    expectedComplexity = 'O(n) Time, O(n) Space';
  } else if (hasBacktracking || (hasRecursion && hasNestedLoops)) {
    timeComplexity = 'O(2ⁿ) / O(N!)';
    spaceComplexity = 'O(n) Call Stack';
    issue = 'Exhaustive recursive search with state backtracking explore large permutation state-trees.';
    optimization = 'Apply memoization/dynamic programming or constraint propagation to prune branches early.';
    expectedComplexity = 'Pruned sub-exponential branch space';
  } else if (hasRecursion) {
    timeComplexity = 'O(n)';
    spaceComplexity = 'O(n) Recursion Stack';
    issue = 'Recursive call stack overhead for linear operations.';
    optimization = 'Consider tail recursion or iterative formulation with an explicit accumulator if stack depth is large.';
    expectedComplexity = 'O(n) Time, O(1) Space';
  }

  return {
    timeComplexity,
    spaceComplexity,
    issue,
    optimization,
    expectedComplexity,
    optimizedCode,
    activeLineInfo: currentLine > 0 ? `Line ${currentLine}: ${codeLines[currentLine - 1] || ''}` : '',
    contextSummary: `Step ${snapshot?.step ?? 0} in ${snapshot?.function || 'global'} with ${Object.keys(variables || {}).length} active variables.`
  };
}

