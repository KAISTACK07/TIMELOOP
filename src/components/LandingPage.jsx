import { motion } from 'framer-motion';
import { ArrowRight, Terminal, Zap, Clock } from 'lucide-react';

export default function LandingPage({ onGetStarted }) {
  return (
    <div className="relative z-10 min-h-screen flex flex-col items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.2 }}
        className="mb-16"
      >
        <div className="px-4 py-1.5 rounded-full border border-red-500/30 bg-red-500/5 backdrop-blur-sm">
          <span className="text-xs font-medium tracking-[0.2em] uppercase text-red-400/80">
            Early Access
          </span>
        </div>
      </motion.div>

      <motion.h1
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1, delay: 0.4 }}
        className="font-['Orbitron'] text-5xl md:text-7xl lg:text-8xl font-semibold tracking-[0.15em] uppercase text-white text-center mb-6"
        style={{ textShadow: '0 0 60px rgba(255,45,85,0.3)' }}
      >
        TimeLoop
        <span className="block text-2xl md:text-3xl lg:text-4xl font-['Orbitron'] tracking-[0.3em] text-red-500/90 mt-2">
          Labs
        </span>
      </motion.h1>

      <motion.p
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1, delay: 0.6 }}
        className="text-lg md:text-xl text-gray-400 text-center mb-12 font-['Inter'] max-w-lg"
      >
        Where elite developers master execution timelines.
      </motion.p>

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1, delay: 0.8 }}
      >
        <button
          onClick={onGetStarted}
          className="group relative px-10 py-4 rounded-full bg-gradient-to-r from-red-600 to-red-500 font-['Orbitron'] text-sm uppercase tracking-[0.2em] text-white transition-all duration-300 hover:shadow-[0_0_40px_rgba(255,45,85,0.6),0_0_80px_rgba(255,45,85,0.3)] hover:scale-105"
          style={{
            boxShadow: '0 0 20px rgba(255,45,85,0.4), inset 0 1px 0 rgba(255,255,255,0.2)',
          }}
        >
          <span className="flex items-center gap-3">
            Get Early Access
            <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
          </span>
        </button>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1, delay: 1 }}
        className="flex flex-wrap justify-center gap-4 mt-12"
      >
        <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10">
          <Terminal className="w-4 h-4 text-red-400" />
          <span className="text-xs tracking-[0.1em] uppercase text-gray-400">Python 3.8+</span>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10">
          <Zap className="w-4 h-4 text-blue-400" />
          <span className="text-xs tracking-[0.1em] uppercase text-gray-400">Time Travel</span>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10">
          <Clock className="w-4 h-4 text-red-400" />
          <span className="text-xs tracking-[0.1em] uppercase text-gray-400">Production Ready</span>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1, delay: 1.2 }}
        className="absolute bottom-8"
      >
        <p className="text-sm text-gray-600 font-['JetBrains_Mono']">
          Python 3.8+ • Time Travel Debugging • Production Ready
        </p>
      </motion.div>
    </div>
  );
}
