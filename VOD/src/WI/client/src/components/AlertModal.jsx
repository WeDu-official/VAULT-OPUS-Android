//AlertModal.jsx
import React from 'react';
import { AlertCircle, XCircle, Info, CheckCircle2 } from 'lucide-react';

const AlertModal = ({ isOpen, onClose, title, message, type = 'error', action = null }) => {
  if (!isOpen) return null;

  const icons = {
    error: <XCircle className="w-12 h-12 text-red-500" />,
    warning: <AlertCircle className="w-12 h-12 text-amber-500" />,
    info: <Info className="w-12 h-12 text-[#3bb5ff]" />,
    success: <CheckCircle2 className="w-12 h-12 text-emerald-500" />,
  };

  const borderColors = {
    error: 'border-red-500/30',
    warning: 'border-amber-500/30',
    info: 'border-[#3bb5ff]/30',
    success: 'border-emerald-500/30',
  };

  const bgGlow = {
    error: 'shadow-[0_0_50px_-12px_rgba(239,68,68,0.3)]',
    warning: 'shadow-[0_0_50px_-12px_rgba(245,158,11,0.3)]',
    info: 'shadow-[0_0_50px_-12px_rgba(59,181,255,0.3)]',
    success: 'shadow-[0_0_50px_-12px_rgba(16,185,129,0.3)]',
  };

  return (
    <div className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in duration-300">
      <div className={`bg-[#0a1628] border ${borderColors[type]} rounded-2xl w-full max-w-sm ${bgGlow[type]} overflow-hidden animate-in zoom-in-95 duration-300`}>
        <div className="p-8 text-center flex flex-col items-center gap-4">
          <div className="mb-2 animate-in slide-in-from-top-4 duration-500">
            {icons[type]}
          </div>
          
          <div className="space-y-2">
            <h2 className="text-xl font-bold text-white tracking-tight">{title || 'Attention'}</h2>
            <div className="text-gray-400 text-sm leading-relaxed max-w-[280px] mx-auto whitespace-pre-wrap">
              {message}
            </div>
          </div>

          <div className="pt-4 w-full space-y-3">
            {action && (
              <button
                onClick={() => {
                  action.onClick();
                  if (action.closeOnClick !== false) onClose();
                }}
                className={`w-full py-3 rounded-xl font-bold transition-all active:scale-[0.98] shadow-lg
                  ${action.isDanger 
                    ? 'bg-red-600 hover:bg-red-500 shadow-red-900/20 text-white' 
                    : 'bg-[#1a3a5c] hover:bg-[#254d7a] text-[#3bb5ff] border border-[#3bb5ff]/20'}`}
              >
                {action.label}
              </button>
            )}
            <button
              onClick={onClose}
              className="w-full py-3 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] hover:from-[#005a9e] hover:to-[#2aa5ef] shadow-[#3bb5ff]/20 text-white rounded-xl font-bold transition-all active:scale-[0.98] btn-click shadow-lg"
            >
              {action ? 'Dismiss' : 'Understand'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlertModal;
