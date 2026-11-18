import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Radio, RefreshCw } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0B0F17] flex flex-col items-center justify-center p-4">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="p-4 rounded-2xl bg-blue-600/20 border border-blue-500/30 text-blue-400">
              <Radio className="w-8 h-8 animate-pulse text-blue-400" />
            </div>
            <div className="absolute inset-0 rounded-2xl ring-2 ring-blue-500/20 animate-ping" />
          </div>
          <div className="text-center">
            <div className="text-base font-bold text-white tracking-tight flex items-center justify-center gap-2">
              <span>VisionIQ</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30 font-semibold">
                SECURE GATEWAY
              </span>
            </div>
            <div className="text-xs text-slate-400 mt-1 flex items-center justify-center gap-2">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-400" />
              <span>Verifying authenticated session...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

export default ProtectedRoute;
