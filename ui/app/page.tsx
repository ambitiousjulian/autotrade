'use client';

import { useState, useEffect } from 'react';
import TrafficLight from './components/TrafficLight';
import AccountStatus from './components/AccountStatus';
import ActivePositions from './components/ActivePositions';
import QuickControls from './components/QuickControls';

interface Stats {
  mode: 'income' | 'turbo';
  balance: number;
  todayPnl: number;
  weekPnl: number;
  positions: { symbol: string; pnl: number; pct: number }[];
  systemStatus: 'green' | 'yellow' | 'red';
  isPaused: boolean;
  riskUsed: number;
  lastUpdate: string;
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Fetch stats from API
  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/stats`);
      if (!response.ok) throw new Error('Failed to fetch stats');
      const data = await response.json();
      setStats(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  // Control handlers
  const handlePause = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/pause`, { method: 'POST' });
      if (!response.ok) throw new Error('Failed to pause');
      await fetchStats();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to pause');
    }
  };

  const handleResume = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/resume`, { method: 'POST' });
      if (!response.ok) throw new Error('Failed to resume');
      await fetchStats();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resume');
    }
  };

  const handleEmergencyExit = async () => {
    if (!confirm('⚠️ Are you sure? This will close ALL positions immediately!')) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/exit_all`, { method: 'POST' });
      if (!response.ok) throw new Error('Failed to exit positions');
      await fetchStats();
      alert('✅ Emergency exit completed');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to exit positions');
    }
  };

  const handleToggleMode = async (mode: 'income' | 'turbo') => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/toggle_mode?mode=${mode}`, { method: 'POST' });
      if (!response.ok) throw new Error('Failed to toggle mode');
      await fetchStats();
      alert(`✅ Switched to ${mode.toUpperCase()} mode`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle mode');
    }
  };

  const handleRiskLevel = async (level: 'low' | 'medium' | 'high') => {
    const riskSettings = {
      low: { daily: 0.02, perTrade: 0.005 },
      medium: { daily: 0.06, perTrade: 0.01 },
      high: { daily: 0.10, perTrade: 0.02 }
    };
    
    try {
      const settings = riskSettings[level];
      const response = await fetch(`${API_BASE_URL}/api/update_risk`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          daily_limit: settings.daily,
          per_trade_limit: settings.perTrade
        })
      });
      
      if (!response.ok) throw new Error('Failed to update risk');
      await fetchStats();
      alert(`✅ Risk level set to ${level.toUpperCase()}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update risk level');
    }
  };

  // Auto-refresh every 5 seconds
  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <h2 className="text-red-800 font-bold mb-2">Connection Error</h2>
          <p className="text-red-600">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-4 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">🤖 Robo-Pilot MAX</h1>
              <TrafficLight status={stats.systemStatus} />
            </div>
            <div className="text-sm text-gray-500">
              Last update: {new Date(stats.lastUpdate).toLocaleTimeString()}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Alert if paused */}
        {stats.isPaused && (
          <div className="mb-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-yellow-800 font-medium">
              ⚠️ Trading is currently PAUSED. Click RESUME to continue trading.
            </p>
          </div>
        )}

        {/* Risk Usage Bar */}
        <div className="mb-8 bg-white rounded-lg shadow-md p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-700 font-medium">Daily Risk Used</span>
            <span className="text-gray-900 font-bold">{stats.riskUsed}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div 
              className={`h-3 rounded-full transition-all duration-500 ${
                stats.riskUsed > 80 ? 'bg-red-500' : 
                stats.riskUsed > 50 ? 'bg-yellow-500' : 'bg-green-500'
              }`}
              style={{ width: `${Math.min(stats.riskUsed, 100)}%` }}
            />
          </div>
        </div>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <AccountStatus 
            balance={stats.balance}
            mode={stats.mode}
            todayPnl={stats.todayPnl}
            weekPnl={stats.weekPnl}
          />
          
          <ActivePositions positions={stats.positions} />
          
          <div className="lg:col-span-2">
            <QuickControls 
              onPause={handlePause}
              onResume={handleResume}
              onEmergencyExit={handleEmergencyExit}
              onToggleMode={handleToggleMode}
              onRiskLevel={handleRiskLevel}
              currentMode={stats.mode}
              isPaused={stats.isPaused}
            /> 
          </div>
        </div>
      </main>
    </div>
  );
}