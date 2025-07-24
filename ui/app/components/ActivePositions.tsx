import React from 'react';

interface Position {
  symbol: string;
  pnl: number;
  pct: number;
}

interface ActivePositionsProps {
  positions: Position[];
}

export default function ActivePositions({ positions }: ActivePositionsProps) {
  const formatCurrency = (value: number) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}$${Math.abs(value).toFixed(0)}`;
  };

  const formatPercent = (value: number) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(1)}%`;
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <h2 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
        <span className="mr-2">📈</span> ACTIVE POSITIONS
      </h2>
      
      {positions.length === 0 ? (
        <p className="text-gray-500 text-center py-4">No active positions</p>
      ) : (
        <div className="space-y-2">
          {positions.map((position, index) => (
            <div
              key={`${position.symbol}-${index}`}
              className="flex items-center justify-between p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
            >
              <span className="font-medium text-gray-800">{position.symbol}</span>
              <div className="flex items-center space-x-4">
                <span className={`font-medium ${position.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatCurrency(position.pnl)}
                </span>
                <span className={`text-sm font-medium px-2 py-1 rounded ${
                  position.pct >= 0 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {formatPercent(position.pct)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}