import { useState } from 'react';
import LandingPage from "./components/LandingPage";
import AuthPage from "./components/AuthPage";
import Dashboard from "./components/Dashboard";

export default function App() {
  const [currentPage, setCurrentPage] = useState('landing');
  const [authMode, setAuthMode] = useState('signup');

  const handleGetStarted = () => {
    setAuthMode('signup');
    setCurrentPage('auth');
  };

  const handleBack = () => {
    setCurrentPage('landing');
  };

  const handleSwitchMode = (mode) => {
    setAuthMode(mode);
  };

  const handleLogin = () => {
    setCurrentPage('dashboard');
  };

  const handleLogout = () => {
    setCurrentPage('landing');
  };

  return (
    <div className="min-h-screen bg-[#050505] relative overflow-hidden">
      <BackgroundEffects />
      {currentPage === 'landing' && (
        <LandingPage onGetStarted={handleGetStarted} />
      )}
      {currentPage === 'auth' && (
        <AuthPage 
          mode={authMode} 
          onBack={handleBack} 
          onSwitchMode={handleSwitchMode}
          onSuccess={handleLogin}
        />
      )}
      {currentPage === 'dashboard' && (
        <Dashboard onLogout={handleLogout} />
      )}
    </div>
  );
}

function BackgroundEffects() {
  return (
    <>
      <div 
        className="fixed inset-0 pointer-events-none z-50 opacity-[0.03]"
        style={{
          backgroundImage: `repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(255,255,255,0.03) 2px,
            rgba(255,255,255,0.03) 4px
          )`,
        }}
      />
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div 
          className="absolute w-[200%] h-[800px] top-[-50%] left-[-50%] opacity-20 animate-streak-red"
          style={{
            background: 'linear-gradient(135deg, transparent 0%, #ff2d55 30%, #ff2d55 50%, #ff2d55 70%, transparent 100%)',
            transform: 'rotate(-25deg)',
            filter: 'blur(60px)',
          }}
        />
        <div 
          className="absolute w-[200%] h-[600px] top-[-20%] left-[20%] opacity-15 animate-streak-blue"
          style={{
            background: 'linear-gradient(160deg, transparent 0%, #00d4ff 30%, #00d4ff 50%, #00d4ff 70%, transparent 100%)',
            transform: 'rotate(-20deg)',
            filter: 'blur(80px)',
          }}
        />
        <div 
          className="absolute w-[300px] h-full top-0 left-[15%] opacity-10 animate-vertical-beam"
          style={{
            background: 'linear-gradient(180deg, transparent 0%, #ff2d55 40%, #ff2d55 60%, transparent 100%)',
            filter: 'blur(40px)',
          }}
        />
        <div 
          className="absolute w-[200px] h-full top-0 right-[20%] opacity-08 animate-vertical-beam-alt"
          style={{
            background: 'linear-gradient(180deg, transparent 0%, #00d4ff 40%, #00d4ff 60%, transparent 100%)',
            filter: 'blur(50px)',
          }}
        />
      </div>
      <div 
        className="fixed inset-0 pointer-events-none z-40"
        style={{
          background: 'radial-gradient(ellipse at center, transparent 0%, rgba(5,5,5,0.4) 70%, rgba(5,5,5,0.9) 100%)',
        }}
      />
      <style>{`
        @keyframes streak-red {
          0%, 100% { transform: translateX(-10%) rotate(-25deg); }
          50% { transform: translateX(10%) rotate(-25deg); }
        }
        @keyframes streak-blue {
          0%, 100% { transform: translateX(10%) rotate(-20deg); }
          50% { transform: translateX(-10%) rotate(-20deg); }
        }
        @keyframes vertical-beam {
          0%, 100% { opacity: 0.1; }
          50% { opacity: 0.15; }
        }
        @keyframes vertical-beam-alt {
          0%, 100% { opacity: 0.08; }
          50% { opacity: 0.12; }
        }
        .animate-streak-red {
          animation: streak-red 12s ease-in-out infinite;
        }
        .animate-streak-blue {
          animation: streak-blue 15s ease-in-out infinite;
        }
        .animate-vertical-beam {
          animation: vertical-beam 8s ease-in-out infinite;
        }
        .animate-vertical-beam-alt {
          animation: vertical-beam-alt 10s ease-in-out infinite;
        }
      `}</style>
    </>
  );
}
