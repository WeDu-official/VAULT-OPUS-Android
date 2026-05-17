//DownloadModal.jsx
import React, { useState } from 'react';

export default function DownloadModal({ isOpen, onClose, onConfirm, selectedItems = [] }) {
  const [strictnessMode, setStrictnessMode] = useState('NA');

  if (!isOpen) return null;

  const handleConfirm = () => {
    onConfirm({ strictnessMode });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-[#0a1628] border border-[#1a3a5c] rounded-2xl w-full max-w-sm overflow-hidden shadow-2xl animate-in fade-in zoom-in duration-200">
        <div className="px-6 py-4 border-b border-[#1a3a5c] bg-[#0d1b2e] flex justify-between items-center">
          <h3 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
            <svg className="w-5 h-5 text-[#3bb5ff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Download Options
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6 space-y-6">
          <p className="text-sm text-gray-400">
            You are about to download <span className="text-[#3bb5ff] font-medium">{selectedItems.length}</span> item(s).
          </p>

          <div className="space-y-3">
            <label className="text-xs font-bold text-[#3bb5ff] uppercase tracking-wider">Strictness Mode</label>
            <div className="grid grid-cols-1 gap-2">
              <button
                onClick={() => setStrictnessMode('NA')}
                className={`px-4 py-3 rounded-xl border text-left transition-all duration-200 ${
                  strictnessMode === 'NA' 
                    ? 'bg-[#1a3a5c]/40 border-[#3bb5ff] text-white shadow-[0_0_15px_rgba(59,181,255,0.2)]' 
                    : 'bg-[#0d1b2e] border-[#1a3a5c] text-gray-400 hover:border-[#3bb5ff]/50'
                }`}
              >
                <div className="font-medium">NOT ATOMIC (DEFAULT)</div>
                <div className="text-xs opacity-60">Continue downloading on failure</div>
              </button>
              
              <button
                onClick={() => setStrictnessMode('SA')}
                className={`px-4 py-3 rounded-xl border text-left transition-all duration-200 ${
                  strictnessMode === 'SA' 
                    ? 'bg-[#1a3a5c]/40 border-[#3bb5ff] text-white shadow-[0_0_15px_rgba(59,181,255,0.2)]' 
                    : 'bg-[#0d1b2e] border-[#1a3a5c] text-gray-400 hover:border-[#3bb5ff]/50'
                }`}
              >
                <div className="font-medium">SOFT ATOMIC</div>
                <div className="text-xs opacity-60">Stop immediately, ask before cleanup</div>
              </button>

              <button
                onClick={() => setStrictnessMode('HA')}
                className={`px-4 py-3 rounded-xl border text-left transition-all duration-200 ${
                  strictnessMode === 'HA' 
                    ? 'bg-[#1a3a5c]/40 border-[#3bb5ff] text-white shadow-[0_0_15px_rgba(59,181,255,0.2)]' 
                    : 'bg-[#0d1b2e] border-[#1a3a5c] text-gray-400 hover:border-[#3bb5ff]/50'
                }`}
              >
                <div className="font-medium">HARD ATOMIC</div>
                <div className="text-xs opacity-60">Stop immediately, auto-cleanup</div>
              </button>
            </div>
          </div>
        </div>

        <div className="px-6 py-4 bg-[#0d1b2e] flex justify-end gap-3 border-t border-[#1a3a5c]">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            className="px-6 py-2 rounded-lg text-sm font-bold bg-[#3bb5ff] hover:bg-[#2e9ee6] text-[#060d1a] shadow-[0_0_20px_rgba(59,181,255,0.3)] transition-all duration-200 active:scale-95"
          >
            Start Download
          </button>
        </div>
      </div>
    </div>
  );
}
