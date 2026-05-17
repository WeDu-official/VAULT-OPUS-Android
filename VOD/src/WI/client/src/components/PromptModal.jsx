//PromptModal.jsx
import React, { useState, useEffect } from 'react';

export default function PromptModal({ promptText, isPassword, onSubmit, onCancel }) {
  const [input, setInput] = useState('');

  // Handle common choice patterns
  const isYesNo = promptText.toLowerCase().includes('(yes/no)');
  const isDeleteOptions = promptText.includes('(S/F/E/G)');

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    onSubmit(input);
  };

  const handleChoice = (choice) => {
    onSubmit(choice);
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
      <div className="bg-[#0a1628] border border-[#1a3a5c] rounded-xl shadow-2xl p-6 w-full max-w-md animate-in zoom-in-95 duration-200">
        <div className="flex items-center gap-3 mb-4 text-[#3bb5ff]">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
          <h3 className="text-lg font-semibold text-white">Input Required</h3>
        </div>

        <div className="text-gray-300 text-sm mb-5 break-words whitespace-pre-wrap max-h-60 overflow-y-auto custom-scrollbar pr-2">
          {promptText}
        </div>

        {isYesNo ? (
          <div className="flex gap-3 mt-4">
            <button
              onClick={() => handleChoice('yes')}
              className="flex-1 px-4 py-2 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] hover:from-[#005a9e] hover:to-[#2aa5ef] text-white rounded-lg transition-all duration-150 active:scale-95 shadow-md font-medium"
            >
              Yes
            </button>
            <button
              onClick={() => handleChoice('no')}
              className="flex-1 px-4 py-2 bg-[#0f1f3a] border border-[#1a3a5c] hover:bg-[#1a3a5c] text-gray-200 rounded-lg transition-all duration-150 active:scale-95"
            >
              No
            </button>
          </div>
        ) : isDeleteOptions ? (
          <div className="grid grid-cols-2 gap-3 mt-4">
            <button
              onClick={() => handleChoice('S')}
              className="px-4 py-3 bg-[#0f1f3a] border border-[#1a3a5c] hover:bg-[#1a3a5c] text-gray-200 rounded-lg transition-all duration-150 active:scale-95 flex flex-col items-center"
              title="Switch to Soft Delete"
            >
              <span className="font-bold text-[#3bb5ff]">S</span>
              <span className="text-[10px] opacity-60">Soft Delete</span>
            </button>
            <button
              onClick={() => handleChoice('F')}
              className="px-4 py-3 bg-red-900/20 border border-red-900/40 hover:bg-red-900/30 text-red-400 rounded-lg transition-all duration-150 active:scale-95 flex flex-col items-center"
              title="Force Hard Delete"
            >
              <span className="font-bold">F</span>
              <span className="text-[10px] opacity-60">Force Hard</span>
            </button>
            <button
              onClick={() => handleChoice('E')}
              className="px-4 py-3 bg-indigo-900/20 border border-indigo-900/40 hover:bg-indigo-900/30 text-indigo-400 rounded-lg transition-all duration-150 active:scale-95 flex flex-col items-center"
              title="Exclusion Delete"
            >
              <span className="font-bold">E</span>
              <span className="text-[10px] opacity-60">Exclusion</span>
            </button>
            <button
              onClick={() => handleChoice('G')}
              className="px-4 py-3 bg-rose-900/40 border border-rose-900/60 hover:bg-rose-900/50 text-rose-300 rounded-lg transition-all duration-150 active:scale-95 flex flex-col items-center"
              title="Shotgun Delete"
            >
              <span className="font-bold">G</span>
              <span className="text-[10px] opacity-60">Shotgun</span>
            </button>
            <button
              onClick={onCancel}
              className="col-span-2 mt-2 px-4 py-2 text-sm text-gray-400 hover:text-white transition-all duration-150 active:scale-95"
            >
              Cancel Deletion
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <input
              type={isPassword ? "password" : "text"}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className="w-full bg-[#060d1a] border border-[#1a3a5c] focus:border-[#3bb5ff] rounded-lg px-4 py-2.5 text-gray-200 outline-none transition-colors mb-6 shadow-inner"
              autoFocus
            />

            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={onCancel}
                className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-all duration-150 active:scale-95"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] hover:from-[#005a9e] hover:to-[#2aa5ef] text-white rounded-lg transition-all duration-150 active:scale-95 shadow-md font-medium"
              >
                Submit
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}