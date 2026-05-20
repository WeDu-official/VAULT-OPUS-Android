// FullNameModal.jsx (FOR CLIENT/DESKTOP) from the VAULT OPUS PROJECT version 1-beta-release-6-ESEN-2
// ==================== FULL CLIENT/DESKTOP GUI====================
import React from 'react';

export default function FullNameModal({ isOpen, onClose, item }) {
  if (!isOpen || !item) return null;

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-[#0a1628] border border-[#1a3a5c] rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between p-6 border-b border-[#1a3a5c]">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[#3bb5ff]/10 rounded-lg text-[#3bb5ff]">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-white">Full Name Metadata</h2>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-[#0f1f3a] rounded-full transition-colors text-gray-400">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Box 1: Display Name / Nickname */}
          <div className="space-y-2">
            <label className="text-[10px] text-[#3bb5ff] font-bold uppercase tracking-widest opacity-70">
              {item.is_nicknamed ? "Nickname (Display Name)" : "Original Base Filename (Display Name)"}
            </label>
            <div className="p-4 bg-[#060d1a] border border-[#1a3a5c] rounded-xl text-[#3bb5ff] font-mono text-sm break-all max-h-32 overflow-y-auto custom-scrollbar">
              {item.is_nicknamed
                ? (item.db_name || item.base_filename || item.name || item.displayName || "Unknown Nickname")
                : (item.original_name || item.original_base_filename || item.db_name || item.base_filename || item.name || item.displayName || "Unknown Name")}
            </div>
          </div>

          {/* Box 2: Original Name (only if nicknamed) */}
          {item.is_nicknamed && (
            <div className="space-y-2">
              <label className="text-[10px] text-[#3bb5ff] font-bold uppercase tracking-widest opacity-70">
                Original Base Filename
              </label>
              <div className="p-4 bg-[#060d1a] border border-[#1a3a5c] rounded-xl text-gray-400 font-mono text-sm max-h-40 overflow-y-auto custom-scrollbar break-all shadow-inner">
                {item.original_name || item.original_base_filename || item.db_name || item.base_filename || item.name || "N/A"}
              </div>
            </div>
          )}

          {/* Box 3: Item ID */}
          <div className="space-y-2">
            <label className="text-[10px] text-[#3bb5ff] font-bold uppercase tracking-widest opacity-70">
              Item ID
            </label>
            <div className="p-4 bg-[#060d1a] border border-[#1a3a5c] rounded-xl text-white font-mono text-sm break-all">
              {item.itemid}
            </div>
          </div>
        </div>

        <div className="p-6 bg-[#060d1a]/50 border-t border-[#1a3a5c]">
          <button
            onClick={onClose}
            className="w-full py-3 bg-[#0f1f3a] hover:bg-[#1a3a5c] text-white rounded-xl font-medium transition-all duration-150 active:scale-95 border border-[#1a3a5c]"
          >
            Close Dialog
          </button>
        </div>
      </div>
    </div>
  );
}
