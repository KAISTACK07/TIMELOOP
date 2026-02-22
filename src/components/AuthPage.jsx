import { useState } from 'react';
import { motion } from 'framer-motion';
import { Eye, EyeOff, ArrowLeft, Terminal } from 'lucide-react';

export default function AuthPage({ mode, onBack, onSwitchMode, onSuccess }) {
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState('admin@timeloop.com');
  const [password, setPassword] = useState('admin123');
  const [name, setName] = useState('lakshay');

  const isSignup = mode === 'signup';

  const handleSubmit = (e) => {
    e.preventDefault();
    onSuccess();
  };

  return (
    <div className="relative z-10 min-h-screen flex items-center justify-center px-4">
      <motion.button
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5 }}
        onClick={onBack}
        className="absolute top-8 left-8 flex items-center gap-2 text-gray-500 hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span className="text-sm font-['Inter']">Back</span>
      </motion.button>

      <motion.div
        initial={{ opacity: 0, y: 30, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-md"
      >
        <div 
          className="relative p-8 rounded-2xl border border-white/10 backdrop-blur-xl"
          style={{
            background: 'linear-gradient(135deg, rgba(20,20,25,0.9) 0%, rgba(10,10,15,0.95) 100%)',
            boxShadow: '0 0 60px rgba(255,45,85,0.1), inset 0 1px 0 rgba(255,255,255,0.05)',
          }}
        >
          <div className="flex flex-col items-center mb-8">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-red-600/20 to-red-500/10 border border-red-500/30 flex items-center justify-center mb-4">
              <Terminal className="w-7 h-7 text-red-500" />
            </div>
            <h2 className="font-['Orbitron'] text-2xl font-semibold tracking-[0.15em] uppercase text-white">
              {isSignup ? 'Join TimeLoop' : 'Welcome Back'}
            </h2>
            <p className="text-sm text-gray-500 mt-2 font-['Inter']">
              {isSignup ? 'Create your developer account' : 'Access your time-travel sessions'}
            </p>
          </div>

          <form className="space-y-5" onSubmit={handleSubmit}>
            {isSignup && (
              <div>
                <label className="block text-xs tracking-[0.1em] uppercase text-gray-400 mb-2 font-['Inter']">
                  Full Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Enter your name"
                  className="w-full px-4 py-3 rounded-xl bg-gray-900/50 border border-gray-700/50 text-white placeholder-gray-500 focus:border-red-500/50 focus:ring-2 focus:ring-red-500/20 focus:outline-none transition-all duration-200 font-['Inter']"
                />
              </div>
            )}

            <div>
              <label className="block text-xs tracking-[0.1em] uppercase text-gray-400 mb-2 font-['Inter']">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="developer@example.com"
                className="w-full px-4 py-3 rounded-xl bg-gray-900/50 border border-gray-700/50 text-white placeholder-gray-500 focus:border-red-500/50 focus:ring-2 focus:ring-red-500/20 focus:outline-none transition-all duration-200 font-['Inter']"
              />
            </div>

            <div>
              <label className="block text-xs tracking-[0.1em] uppercase text-gray-400 mb-2 font-['Inter']">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full px-4 py-3 rounded-xl bg-gray-900/50 border border-gray-700/50 text-white placeholder-gray-500 focus:border-red-500/50 focus:ring-2 focus:ring-red-500/20 focus:outline-none transition-all duration-200 font-['JetBrains_Mono'] pr-12"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="w-full py-4 rounded-xl bg-gradient-to-r from-red-600 to-red-500 font-['Orbitron'] text-sm uppercase tracking-[0.15em] text-white transition-all duration-200 hover:shadow-[0_0_30px_rgba(255,45,85,0.5)] hover:scale-[1.02] active:scale-[0.98]"
              style={{
                boxShadow: '0 0 20px rgba(255,45,85,0.3), inset 0 1px 0 rgba(255,255,255,0.15)',
              }}
            >
              {isSignup ? 'Create Account' : 'Sign In'}
            </button>
          </form>

          <div className="mt-8 text-center">
            <p className="text-sm text-gray-500 font-['Inter']">
              {isSignup ? 'Already have an account?' : "Don't have an account?"}{' '}
              <button
                onClick={() => onSwitchMode(isSignup ? 'login' : 'signup')}
                className="text-red-400 hover:text-red-300 transition-colors underline underline-offset-4"
              >
                {isSignup ? 'Sign in' : 'Sign up'}
              </button>
            </p>
          </div>
        </div>

        <div className="absolute top-0 left-0 w-16 h-16 border-l-2 border-t-2 border-red-500/20 rounded-tl-2xl -z-10" />
        <div className="absolute bottom-0 right-0 w-16 h-16 border-r-2 border-b-2 border-blue-500/20 rounded-br-2xl -z-10" />
      </motion.div>
    </div>
  );
}
