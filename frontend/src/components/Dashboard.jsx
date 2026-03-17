import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Terminal, Play, Pause, Rewind, FastForward, SkipForward,
  Clock, Activity, Bug, Code, Database,
  Settings, LogOut, Plus, Search, Filter, MoreHorizontal,
  Cpu, Layers
} from 'lucide-react';

const mockTimeline = [
  { id: '1', time: '00:00:00.000', type: 'call', label: 'main()', details: 'app.py:1' },
  { id: '2', time: '00:00:00.125', type: 'call', label: 'initialize_db()', details: 'app.py:15' },
  { id: '3', time: '00:00:00.342', type: 'variable', label: 'config.loaded', details: 'True' },
  { id: '4', time: '00:00:00.567', type: 'call', label: 'process_request()', details: 'app.py:42' },
  { id: '5', time: '00:00:00.891', type: 'breakpoint', label: 'Breakpoint #1', details: 'app.py:78' },
  { id: '6', time: '00:00:01.234', type: 'exception', label: 'ConnectionError', details: 'db.py:103' },
  { id: '7', time: '00:00:01.456', type: 'call', label: 'handle_error()', details: 'app.py:156' },
];

const mockSessions = [
  { id: '1', name: 'user_auth_flow', timestamp: '2 min ago', duration: '3.2s', status: 'failed' },
  { id: '2', name: 'data_pipeline_v2', timestamp: '15 min ago', duration: '12.8s', status: 'completed' },
  { id: '3', name: 'api_endpoint_test', timestamp: '1 hour ago', duration: '1.4s', status: 'completed' },
  { id: '4', name: 'ml_model_inference', timestamp: '2 hours ago', duration: '45.2s', status: 'completed' },
];

export default function Dashboard({ onLogout }) {
  const [currentTime, setCurrentTime] = useState(2500);
  const [isPlaying, setIsPlaying] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState(null);

  const formatTime = (ms) => {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    const millis = ms % 1000;
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}.${millis.toString().padStart(3, '0')}`;
  };

  const getEventColor = (type) => {
    switch (type) {
      case 'call': return 'text-blue-400 bg-blue-400/10 border-blue-400/30';
      case 'exception': return 'text-red-400 bg-red-400/10 border-red-400/30';
      case 'breakpoint': return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30';
      case 'variable': return 'text-green-400 bg-green-400/10 border-green-400/30';
      default: return 'text-gray-400 bg-gray-400/10 border-gray-400/30';
    }
  };

  return (
    <div className="relative z-10 min-h-screen flex">
      <motion.aside
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="w-64 bg-[#0a0a0f]/80 border-r border-white/5 flex flex-col"
      >
        <div className="p-6 border-b border-white/5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-red-600/20 to-red-500/10 border border-red-500/30 flex items-center justify-center">
              <Terminal className="w-5 h-5 text-red-500" />
            </div>
            <div>
              <h1 className="font-['Orbitron'] text-sm font-semibold tracking-[0.15em] uppercase text-white">
                TimeLoop
              </h1>
              <p className="text-[10px] tracking-[0.2em] uppercase text-gray-500">Labs</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          <NavItem icon={<Activity className="w-4 h-4" />} label="Timeline" active />
          <NavItem icon={<Code className="w-4 h-4" />} label="Source Code" />
          <NavItem icon={<Database className="w-4 h-4" />} label="Sessions" />
          <NavItem icon={<Bug className="w-4 h-4" />} label="Breakpoints" />
          <NavItem icon={<Cpu className="w-4 h-4" />} label="Variables" />
          <NavItem icon={<Settings className="w-4 h-4" />} label="Settings" />
        </nav>

        <div className="p-4 border-t border-white/5">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-red-500/30 to-blue-500/30 border border-white/10" />
            <div className="flex-1 min-w-0">
              <p className="text-sm text-white truncate font-['Inter']">dev@timeloop</p>
              <p className="text-[10px] text-gray-500 tracking-[0.1em] uppercase">Pro</p>
            </div>
          </div>
          <button 
            onClick={onLogout}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-gray-400 hover:text-white hover:bg-white/5 transition-all"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </motion.aside>

      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 border-b border-white/5 flex items-center justify-between px-6 bg-[#0a0a0f]/50">
          <div className="flex items-center gap-4">
            <h2 className="font-['Orbitron'] text-sm tracking-[0.15em] uppercase text-white">
              Timeline Explorer
            </h2>
            <span className="text-xs text-gray-500 font-['JetBrains_Mono']">•</span>
            <span className="text-xs text-gray-500 font-['JetBrains_Mono']">user_auth_flow.py</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10">
              <Search className="w-4 h-4 text-gray-500" />
              <input 
                type="text" 
                placeholder="Search..." 
                className="bg-transparent text-sm text-white placeholder-gray-500 outline-none w-32 font-['Inter']"
              />
            </div>
            <button className="p-2 rounded-lg hover:bg-white/5 transition-colors">
              <Filter className="w-4 h-4 text-gray-500" />
            </button>
            <button className="px-4 py-2 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs tracking-[0.1em] uppercase hover:bg-red-500/20 transition-all flex items-center gap-2">
              <Plus className="w-3 h-3" />
              New Session
            </button>
          </div>
        </header>

        <div className="flex-1 flex overflow-hidden">
          <div className="w-80 border-r border-white/5 flex flex-col bg-[#0a0a0f]/30">
            <div className="p-4 border-b border-white/5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs tracking-[0.1em] uppercase text-gray-500">Execution Timeline</span>
                <span className="text-xs font-['JetBrains_Mono'] text-red-400">{mockTimeline.length} events</span>
              </div>
              <div className="flex items-center justify-center gap-2">
                <button className="p-2 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white transition-all">
                  <Rewind className="w-4 h-4" />
                </button>
                <button 
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="p-3 rounded-full bg-red-500/20 border border-red-500/50 text-red-400 hover:bg-red-500/30 transition-all"
                >
                  {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                </button>
                <button className="p-2 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white transition-all">
                  <FastForward className="w-4 h-4" />
                </button>
                <button className="p-2 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white transition-all">
                  <SkipForward className="w-4 h-4" />
                </button>
              </div>
              <div className="mt-3 text-center">
                <span className="font-['JetBrains_Mono'] text-xl text-white">{formatTime(currentTime)}</span>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-2">
              {mockTimeline.map((event, index) => (
                <motion.div
                  key={event.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  onClick={() => setSelectedEvent(event.id)}
                  className={`relative p-3 rounded-lg mb-2 cursor-pointer transition-all border ${
                    selectedEvent === event.id 
                      ? 'bg-white/10 border-white/20' 
                      : 'bg-transparent border-transparent hover:bg-white/5 hover:border-white/10'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`w-2 h-2 rounded-full mt-1.5 ${event.type === 'exception' ? 'bg-red-400' : event.type === 'breakpoint' ? 'bg-yellow-400' : event.type === 'call' ? 'bg-blue-400' : 'bg-green-400'}`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className={`text-xs px-2 py-0.5 rounded border ${getEventColor(event.type)}`}>
                          {event.type}
                        </span>
                        <span className="font-['JetBrains_Mono'] text-[10px] text-gray-500">{event.time}</span>
                      </div>
                      <p className="text-sm text-white mt-1 font-['JetBrains_Mono']">{event.label}</p>
                      {event.details && (
                        <p className="text-xs text-gray-500 mt-0.5 font-['JetBrains_Mono']">{event.details}</p>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          <div className="flex-1 flex flex-col">
            <div className="h-10 border-b border-white/5 flex items-center px-4 bg-[#0a0a0f]/30">
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400">app.py</span>
                <span className="text-xs text-gray-600">—</span>
                <span className="text-xs text-gray-500">User authentication flow</span>
              </div>
            </div>

            <div className="flex-1 overflow-auto p-4 font-['JetBrains_Mono'] text-sm">
              <CodeViewer />
            </div>

            <div className="h-48 border-t border-white/5 bg-[#0a0a0f]/30">
              <div className="p-3 border-b border-white/5 flex items-center justify-between">
                <span className="text-xs tracking-[0.1em] uppercase text-gray-500">Variable Inspector</span>
                <button className="p-1 rounded hover:bg-white/5">
                  <MoreHorizontal className="w-4 h-4 text-gray-500" />
                </button>
              </div>
              <div className="p-3 grid grid-cols-2 gap-2">
                <VariableItem name="user_id" type="str" value="'usr_8x7y6z5'" />
                <VariableItem name="session_token" type="str" value="'eyJhbGci...'" />
                <VariableItem name="is_authenticated" type="bool" value="True" />
                <VariableItem name="request_count" type="int" value="42" />
                <VariableItem name="config" type="dict" value="{...}" />
                <VariableItem name="error_log" type="list" value="[3 items]" />
              </div>
            </div>
          </div>

          <div className="w-72 border-l border-white/5 bg-[#0a0a0f]/30 flex flex-col">
            <div className="p-4 border-b border-white/5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs tracking-[0.1em] uppercase text-gray-500">Recent Sessions</span>
                <Clock className="w-4 h-4 text-gray-500" />
              </div>
              <div className="grid grid-cols-2 gap-2 mb-3">
                <StatCard label="Total" value="128" icon={<Activity className="w-3 h-3" />} />
                <StatCard label="Failed" value="12" icon={<Bug className="w-3 h-3" />} />
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-2">
              {mockSessions.map((session, index) => (
                <motion.div
                  key={session.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="p-3 rounded-lg bg-white/5 border border-white/5 hover:border-white/10 cursor-pointer transition-all mb-2"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-white font-['JetBrains_Mono']">{session.name}</span>
                    <StatusBadge status={session.status} />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-gray-500">{session.timestamp}</span>
                    <span className="text-[10px] text-gray-400 font-['JetBrains_Mono']">{session.duration}</span>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function NavItem({ icon, label, active = false }) {
  return (
    <button
      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${
        active 
          ? 'bg-red-500/10 border border-red-500/20 text-red-400' 
          : 'text-gray-400 hover:text-white hover:bg-white/5'
      }`}
    >
      {icon}
      <span className="text-xs tracking-[0.1em] uppercase">{label}</span>
    </button>
  );
}

function CodeViewer() {
  const lines = [
    { num: 1, code: 'def authenticate_user(username: str, password: str) -> dict:', highlight: false },
    { num: 2, code: '    """Authenticate user and return session token."""', highlight: false },
    { num: 3, code: '    config = load_config()', highlight: false },
    { num: 4, code: '    ', highlight: false },
    { num: 5, code: '    # Validate credentials', highlight: false },
    { num: 6, code: '    user = db.get_user(username)', highlight: false },
    { num: 7, code: '    if not user:', highlight: false },
    { num: 8, code: '        raise AuthenticationError("User not found")', highlight: true },
    { num: 9, code: '    ', highlight: false },
    { num: 10, code: '    if not verify_password(password, user.hash):', highlight: false },
    { num: 11, code: '        raise AuthenticationError("Invalid password")', highlight: true },
    { num: 12, code: '    ', highlight: false },
    { num: 13, code: '    # Generate session token', highlight: false },
    { num: 14, code: '    token = generate_token(user.id)', highlight: false },
    { num: 15, code: '    ', highlight: false },
    { num: 16, code: '    return {', highlight: false },
    { num: 17, code: '        "user_id": user.id,', highlight: false },
    { num: 18, code: '        "token": token,', highlight: false },
    { num: 19, code: '        "expires_in": 3600', highlight: false },
    { num: 20, code: '    }', highlight: false },
  ];

  return (
    <div className="font-['JetBrains_Mono']">
      {lines.map((line) => (
        <div key={line.num} className="flex">
          <span className="w-12 text-gray-600 text-right pr-4 select-none">{line.num}</span>
          <span className={line.highlight ? 'text-red-400 bg-red-400/10 px-1 -mx-1 rounded' : 'text-gray-300'}>
            {line.code}
          </span>
        </div>
      ))}
    </div>
  );
}

function VariableItem({ name, type, value }) {
  const typeColors = {
    str: 'text-blue-400',
    int: 'text-green-400',
    bool: 'text-yellow-400',
    dict: 'text-purple-400',
    list: 'text-orange-400',
  };

  return (
    <div className="p-2 rounded bg-white/5 border border-white/5">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-white font-['JetBrains_Mono']">{name}</span>
        <span className={`text-[10px] font-['JetBrains_Mono'] ${typeColors[type] || 'text-gray-400'}`}>{type}</span>
      </div>
      <span className="text-[10px] text-gray-500 font-['JetBrains_Mono'] truncate block">{value}</span>
    </div>
  );
}

function StatCard({ label, value, icon }) {
  return (
    <div className="p-2 rounded bg-white/5 border border-white/5">
      <div className="flex items-center justify-between mb-1">
        <span className="text-[10px] text-gray-500 uppercase tracking-wider">{label}</span>
        <span className="text-gray-500">{icon}</span>
      </div>
      <span className="text-lg text-white font-['JetBrains_Mono']">{value}</span>
    </div>
  );
}

function StatusBadge({ status }) {
  const colors = {
    completed: 'bg-green-500/20 text-green-400 border-green-500/30',
    failed: 'bg-red-500/20 text-red-400 border-red-500/30',
    running: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  };

  return (
    <span className={`text-[10px] px-2 py-0.5 rounded border ${colors[status]}`}>
      {status}
    </span>
  );
}
