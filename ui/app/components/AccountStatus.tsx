import React from 'react';

interface AccountStatusProps {
  balance: number;
  mode: 'income' | 'turbo';
  todayPnl: number;
  weekPnl: number;
}

export default function AccountStatus({ balance, mode, todayPnl, weekPnl }: AccountStatusProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatPnl = (value: number) => {
    const formatted = formatCurrency(Math.abs(value));
    const percent = ((value / (balance - value)) * 100).toFixed(1);
    const sign = value >= 0 ? '+' : '-';
    return `${sign}${formatted} (${sign}${percent}%)`;
  };

  const modeConfig = {
    income: { color: 'bg-green-100 text-green-800', icon: '🟢' },
    turbo: { color: 'bg-red-100 text-red-800', icon: '🔴' }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <h2 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
        <span className="mr-2">📊</span> ACCOUNT STATUS
      </h2>
      
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Balance:</span>
          <span className="text-xl font-semibold text-gray-900">{formatCurrency(balance)}</span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Mode:</span>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${modeConfig[mode].color}`}>
            {modeConfig[mode].icon} {mode.toUpperCase()}
          </span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Today P&L:</span>
          <span className={`font-medium ${todayPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {formatPnl(todayPnl)}
          </span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Week P&L:</span>
          <span className={`font-medium ${weekPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {formatPnl(weekPnl)}
          </span>
        </div>
      </div>
    </div>
  );
}