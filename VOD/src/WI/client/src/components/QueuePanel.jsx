// QueuePanel.jsx (FOR CLIENT/DESKTOP) from the VAULT OPUS PROJECT version 1-beta-release-6-ESEN-2
// ==================== FULL CLIENT/DESKTOP GUI====================
import React from 'react';

export default function QueuePanel({ queue, onClear }) {
  if (!queue || queue.length === 0) return null;

  return (
    <div className="absolute bottom-6 left-6 w-80 max-h-96 bg-[#0a1628] border border-[#1a3a5c] rounded-2xl shadow-2xl flex flex-col overflow-hidden z-[80] animate-in slide-in-from-bottom-5">
      <div className="p-4 border-b border-[#1a3a5c] flex items-center justify-between bg-[#0f1f3a]">
        <h3 className="font-semibold text-sm flex items-center gap-2">
          <span className="w-2 h-2 bg-[#3bb5ff] rounded-full animate-pulse"></span>
          Operations Queue
        </h3>
        <button onClick={onClear} className="text-[10px] text-gray-500 hover:text-gray-300 uppercase tracking-wider font-bold transition-all duration-150 active:scale-95 py-1 px-2 rounded">
          Clear All
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {queue.map((item, idx) => (
          <div key={idx} className="p-3 bg-[#060d1a] rounded-lg border border-[#1a3a5c] flex flex-col gap-2">
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs font-medium truncate flex-1">{item.name}</span>
              <span className={`text-[10px] px-1.5 py-0.5 rounded uppercase font-bold
                ${item.status === 'running' ? 'bg-[#3bb5ff]/15 text-[#3bb5ff]' :
                  item.status === 'completed' ? 'bg-green-900/30 text-green-400' :
                    item.status === 'failed' ? 'bg-red-900/30 text-red-400' :
                      'bg-gray-800 text-gray-500'}`}
              >
                {item.status}
              </span>
            </div>

            {item.status === 'running' && (
              <div className="w-full bg-[#0a1628] h-1 rounded-full overflow-hidden">
                <div
                  className="bg-[#3bb5ff] h-full transition-all duration-500"
                  style={{ width: `${item.progress || 0}%` }}
                ></div>
              </div>
            )}

            {item.error && (
              <p className="text-[10px] text-red-500 truncate">{item.error}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}