import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import TopBar from '../components/TopBar.jsx';
import CodePanel from '../components/CodePanel.jsx';
import VariablesPanel from '../components/VariablesPanel.jsx';
import Timeline from '../components/Timeline.jsx';
import AIExplainerModal from '../components/AIExplainerModal.jsx';
import * as api from '../lib/api.js';

const DEFAULT_CODE = `def main():
    x = 0
    for i in range(5):
        x += i
        calculate(x)

def calculate(val):
    return val * 2

main()`;

// Debounce delay for state fetches during scrubbing (ms)
const STATE_FETCH_DEBOUNCE = 150;

export default function Debugger({ theme, toggleTheme }) {
  const [code, setCode] = useState(DEFAULT_CODE);
  const [mode, setMode] = useState('smart');
  const [sessionId, setSessionId] = useState(null);
  const [step, setStep] = useState(0);
  const [maxStep, setMaxStep] = useState(0);
  const [snapshots, setSnapshots] = useState([]);
  const [currentState, setCurrentState] = useState({});
  const [prevState, setPrevState] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [stdout, setStdout] = useState('');
  const [truncated, setTruncated] = useState(false);
  
  const [functionCalls, setFunctionCalls] = useState([]);
  const [exceptions, setExceptions] = useState([]);
  const [aiModalOpen, setAiModalOpen] = useState(false);

  // Ref to hold the debounce timer for state fetches
  const stateFetchTimer = useRef(null);
  // Ref to track the latest currentState for prevState calculation
  const currentStateRef = useRef({});
  currentStateRef.current = currentState;

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setCurrentState({});
    setPrevState({});
    setStep(0);
    setMaxStep(0);
    setSnapshots([]);
    setFunctionCalls([]);
    setExceptions([]);
    setStdout('');
    setTruncated(false);
    
    try {
      const res = await api.executeCode(code, mode);
      
      if (res.error) {
        setError(res.error);
      }
      
      setSessionId(res.session_id);
      setMaxStep(res.maxStep);
      setSnapshots(res.snapshots);
      setStdout(res.stdout || '');
      setTruncated(res.truncated || false);
      
      const funcs = await api.getFunctionCalls(res.session_id, res.snapshots);
      setFunctionCalls(funcs);
      
      const excs = api.getExceptions(res.snapshots);
      setExceptions(excs);
      
      setStep(0);
      
      // Fetch initial state at step 0
      if (res.session_id && res.snapshots.length > 0) {
        const firstStep = res.snapshots[0]?.step ?? 0;
        const state = await api.getState(res.session_id, firstStep);
        setCurrentState(state);
      }
    } catch (err) {
      console.error(err);
      setError(err.message || 'Execution failed');
    } finally {
      setLoading(false);
    }
  };

  // Debounced state fetch with cancellation protection: prevents stale in-flight responses
  useEffect(() => {
    if (sessionId && snapshots.length > 0) {
      let isCancelled = false;

      // Clear any pending fetch timer
      if (stateFetchTimer.current) {
        clearTimeout(stateFetchTimer.current);
      }

      stateFetchTimer.current = setTimeout(async () => {
        const snapshotAtStep = snapshots[step];
        const actualStep = snapshotAtStep?.step ?? step;
        
        const state = await api.getState(sessionId, actualStep);
        if (!isCancelled) {
          setPrevState(currentStateRef.current);
          setCurrentState(state);
        }
      }, STATE_FETCH_DEBOUNCE);

      return () => {
        isCancelled = true;
        if (stateFetchTimer.current) {
          clearTimeout(stateFetchTimer.current);
        }
      };
    }
  }, [step, sessionId, snapshots]);

  // Stable step change callback
  const handleStepChange = useCallback((newStep) => {
    setStep(newStep);
  }, []);

  // Get the current line number from the snapshot at the current step index
  const currentLine = snapshots[step]?.line_no || 0;

  // Memoize stable maxStep for timeline
  const timelineMaxStep = useMemo(
    () => snapshots.length > 0 ? snapshots.length - 1 : 0,
    [snapshots.length]
  );

  return (
    <div className="flex flex-col h-screen w-full bg-theme-bg font-sans overflow-hidden transition-colors duration-300">
      <TopBar 
        onRun={handleRun} 
        loading={loading} 
        theme={theme} 
        toggleTheme={toggleTheme} 
        sessionId={sessionId}
        error={error}
        mode={mode}
        setMode={setMode}
        onOpenAI={() => setAiModalOpen(true)}
      />
      
      <div className="flex-1 flex overflow-hidden p-4 gap-4">
        <div className="w-1/2 flex flex-col rounded-xl overflow-hidden border border-theme-border bg-theme-panel backdrop-blur-sm shadow-2xl transition-colors duration-300">
          <CodePanel code={code} currentLine={currentLine} onChange={setCode} />
        </div>
        <div className="w-1/2 flex flex-col rounded-xl overflow-hidden border border-theme-border bg-theme-panel backdrop-blur-sm shadow-2xl transition-colors duration-300">
          <VariablesPanel
            currentState={currentState}
            prevState={prevState}
            error={error}
            stdout={stdout}
            currentSnapshot={snapshots[step]}
            truncated={truncated}
            totalSnapshots={snapshots.length}
            mode={mode}
          />
        </div>
      </div>

      <div className="h-64 shrink-0 border-t border-theme-border bg-theme-timeline backdrop-blur-md p-4 z-10 relative transition-colors duration-300">
        <Timeline 
          currentStep={step} 
          maxStep={timelineMaxStep} 
          snapshots={snapshots}
          functionCalls={functionCalls}
          exceptions={exceptions}
          onStepChange={handleStepChange}
        />
      </div>

      <AIExplainerModal 
        isOpen={aiModalOpen}
        onClose={() => setAiModalOpen(false)}
        code={code}
        currentLine={currentLine}
        currentSnapshot={snapshots[step]}
        currentState={currentState}
        mode={mode}
        onApplyCode={setCode}
      />
    </div>
  );
}

