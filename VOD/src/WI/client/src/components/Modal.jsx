// Modal.jsx (FOR CLIENT/DESKTOP) from the VAULT OPUS PROJECT version 1-beta-release-6-ESEN-2
// ==================== FULL CLIENT/DESKTOP GUI====================
import React from 'react';

export default function Modal({ isOpen, onClose, title, size = 'medium', children }) {
  if (!isOpen) return null;

  const sizeClasses = {
    small: 'max-w-sm',
    medium: 'max-w-md',
    large: 'max-w-lg',
    xlarge: 'max-w-2xl',
  };

  return (
    <div className="fixed inset-0 bg-black/75 backdrop-blur-md flex items-center justify-center z-50 animate-in fade-in duration-200">
      <div className={`bg-[#0a1628]/95 border border-[#1a3a5c] rounded-2xl shadow-2xl overflow-hidden w-full ${sizeClasses[size] || 'max-w-md'} animate-in zoom-in-95 duration-200`}>
        <div className="flex justify-between items-center px-6 py-4 border-b border-[#1a3a5c]/50 bg-[#060d1a]/80">
          <h3 className="font-bold text-white tracking-wide">{title}</h3>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1.5 hover:bg-[#132844] rounded-lg transition-colors text-gray-400 hover:text-white"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
        <div className="p-6 max-h-[80vh] overflow-y-auto custom-scrollbar">
          {children}
        </div>
      </div>
    </div>
  );
}
