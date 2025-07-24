import React from 'react';

interface QuickControlsProps {
  onPause: () => void;
  onResume: () => void;
  onEmergencyExit: () => void;
  onToggleMode?: (mode: 'income' | 'turbo') => void;
  onRiskLevel?: (level: 'low' | 'medium' | 'high') => void;
  currentMode?: 'income' | 'turbo';
  isPaused?: boolean;
  currentRiskLevel?: 'low' | 'medium' | 'high';
}

export default function QuickControls({ 
  onPause, 
  onResume, 
  onEmergencyExit, 
  onToggleMode, 
  onRiskLevel,
  currentMode = 'income',
  isPaused = false,
  currentRiskLevel = 'medium'
}: QuickControlsProps) {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <h2 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
        <span className="mr-2">⚙️</span> QUICK CONTROLS
      </h2>
      
      <div className="flex flex-col space-y-3">
        <div className="flex space-x-3">
          <button
            onClick={onPause}
            disabled={isPaused}
            className={`flex-1 font-bold py-3 px-4 rounded-lg transition-all duration-200 shadow-md ${
              isPaused 
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                : 'bg-yellow-500 hover:bg-yellow-600 text-white hover:shadow-lg cursor-pointer'
            }`}
          >
            ⏸️ PAUSE
          </button>
          
          <button
            onClick={onResume}
            disabled={!isPaused}
            className={`flex-1 font-bold py-3 px-4 rounded-lg transition-all duration-200 shadow-md ${
              !isPaused 
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                : 'bg-green-500 hover:bg-green-600 text-white hover:shadow-lg cursor-pointer'
            }`}
          >
            ▶️ RESUME
          </button>
        </div>
        
        <button
          onClick={onEmergencyExit}
          className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-4 rounded-lg transition-colors duration-200 shadow-md hover:shadow-lg flex items-center justify-center"
        >
          <span className="mr-2">🚨</span> EMERGENCY EXIT
        </button>
      </div>
      
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-gray-600 font-medium">Mode:</span>
            <div className="flex space-x-2">
              <button 
                onClick={() => onToggleMode?.('income')}
                disabled={currentMode === 'income'}
                className={`px-4 py-2 text-sm font-medium rounded-full transition-all duration-200 ${
                  currentMode === 'income' 
                    ? 'bg-green-500 text-white cursor-default shadow-md' 
                    : 'bg-gray-100 text-gray-600 hover:bg-green-100 hover:text-green-700 cursor-pointer hover:shadow'
                }`}
              >
                💰 INCOME
              </button>
              <button 
                onClick={() => onToggleMode?.('turbo')}
                disabled={currentMode === 'turbo'}
                className={`px-4 py-2 text-sm font-medium rounded-full transition-all duration-200 ${
                  currentMode === 'turbo' 
                    ? 'bg-red-500 text-white cursor-default shadow-md' 
                    : 'bg-gray-100 text-gray-600 hover:bg-red-100 hover:text-red-700 cursor-pointer hover:shadow'
                }`}
              >
                🚀 TURBO
              </button>
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-gray-600 font-medium">Risk Level:</span>
            <div className="flex space-x-2">
              {(['low', 'medium', 'high'] as const).map((level) => (
                <button
                  key={level}
                  onClick={() => onRiskLevel?.(level)}
                  className={`px-3 py-2 text-sm font-medium rounded-full transition-all duration-200 ${
                    currentRiskLevel === level
                      ? level === 'low' 
                        ? 'bg-blue-500 text-white shadow-md'
                        : level === 'medium'
                        ? 'bg-yellow-500 text-white shadow-md'
                        : 'bg-orange-500 text-white shadow-md'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200 cursor-pointer hover:shadow'
                  }`}
                >
                  {level.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Status indicator */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500">Bot Status:</span>
          <span className={`font-medium ${isPaused ? 'text-red-600' : 'text-green-600'}`}>
            {isPaused ? '⏸️ Paused' : '▶️ Running'}
          </span>
        </div>
      </div>
    </div>
  );
}