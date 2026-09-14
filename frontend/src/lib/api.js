// Configurable for deployment (Phase 12/13). Falls back to local dev backend.
const API_URL = import.meta.env?.VITE_API_URL || 'http://127.0.0.1:8000';

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

  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(`Explain failed (${response.status}): ${text}`);
  }

  // The backend always returns a complete analysis object:
  // either LLM-backed (source: "llm") or the deterministic AST static
  // analyzer (source: "static-analysis"). No analysis logic lives in the
  // client anymore — and no API key ever reaches the browser.
  return await response.json();
};

