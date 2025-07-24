import React from 'react';

interface TrafficLightProps {
  status: 'green' | 'yellow' | 'red';
}

export default function TrafficLight({ status }: TrafficLightProps) {
  const config = {
    green: {
      color: 'bg-green-500',
      label: 'System OK',
      glow: 'shadow-lg shadow-green-500/50'
    },
    yellow: {
      color: 'bg-yellow-500',
      label: 'Caution',
      glow: 'shadow-lg shadow-yellow-500/50'
    },
    red: {
      color: 'bg-red-500',
      label: 'Paused',
      glow: 'shadow-lg shadow-red-500/50'
    }
  };

  const { color, label, glow } = config[status];

  return (
    <div className="flex items-center space-x-3">
      <div className={`w-12 h-12 rounded-full ${color} ${glow} animate-pulse`} />
      <span className="text-lg font-semibold text-gray-800">{label}</span>
    </div>
  );
}