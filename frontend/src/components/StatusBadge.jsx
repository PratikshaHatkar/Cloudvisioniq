import React from 'react';
import { CheckCircle, Clock, XCircle, ShieldAlert } from 'lucide-react';

export const StatusBadge = ({ status }) => {
  const norm = (status || '').toLowerCase();

  switch (norm) {
    case 'completed':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <CheckCircle className="w-3.5 h-3.5" />
          Completed
        </span>
      );
    case 'processing':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse">
          <Clock className="w-3.5 h-3.5 animate-spin" />
          Processing
        </span>
      );
    case 'uploaded':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
          <Clock className="w-3.5 h-3.5" />
          Uploaded
        </span>
      );
    case 'failed':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
          <XCircle className="w-3.5 h-3.5" />
          Failed
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
          {status}
        </span>
      );
  }
};

export const ActivityBadge = ({ activity, className = '' }) => {
  const label = activity || 'Unknown';

  const categoryMap = {
    Fighting: {
      badge: 'bg-black/85 backdrop-blur-md border-rose-500/80 text-rose-100 shadow-md shadow-black/80',
      icon: 'text-rose-400',
      dot: 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.8)]',
    },
    Robbery: {
      badge: 'bg-black/85 backdrop-blur-md border-amber-500/80 text-amber-100 shadow-md shadow-black/80',
      icon: 'text-amber-400',
      dot: 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.8)]',
    },
    Burglary: {
      badge: 'bg-black/85 backdrop-blur-md border-orange-500/80 text-orange-100 shadow-md shadow-black/80',
      icon: 'text-orange-400',
      dot: 'bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,0.8)]',
    },
    Shoplifting: {
      badge: 'bg-black/85 backdrop-blur-md border-purple-400/80 text-purple-100 shadow-md shadow-black/80',
      icon: 'text-purple-400',
      dot: 'bg-purple-500 shadow-[0_0_8px_rgba(168,85,247,0.8)]',
    },
    Vandalism: {
      badge: 'bg-black/85 backdrop-blur-md border-fuchsia-400/80 text-fuchsia-100 shadow-md shadow-black/80',
      icon: 'text-fuchsia-400',
      dot: 'bg-fuchsia-500 shadow-[0_0_8px_rgba(217,70,239,0.8)]',
    },
    RoadAccidents: {
      badge: 'bg-black/85 backdrop-blur-md border-cyan-400/80 text-cyan-100 shadow-md shadow-black/80',
      icon: 'text-cyan-400',
      dot: 'bg-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.8)]',
    },
    Normal: {
      badge: 'bg-black/85 backdrop-blur-md border-emerald-500/80 text-emerald-100 shadow-md shadow-black/80',
      icon: 'text-emerald-400',
      dot: 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]',
    },
  };

  const style = categoryMap[label] || {
    badge: 'bg-black/85 backdrop-blur-md border-blue-500/80 text-blue-100 shadow-md shadow-black/80',
    icon: 'text-blue-400',
    dot: 'bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.8)]',
  };

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold tracking-wide border ${style.badge} ${className}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${style.dot}`} />
      <ShieldAlert className={`w-3.5 h-3.5 ${style.icon} shrink-0`} />
      <span>{label}</span>
    </span>
  );
};

export default StatusBadge;
