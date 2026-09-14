import React, { useState, useEffect } from 'react';
import Debugger from './pages/Debugger.jsx';

export default function App() {
  const [theme, setTheme] = useState('dark');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  return <Debugger theme={theme} toggleTheme={toggleTheme} />;
}