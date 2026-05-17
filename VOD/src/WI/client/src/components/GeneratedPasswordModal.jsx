//GeneratedPasswordModal.jsx
import React, { useState } from 'react';
import { Copy, Check, ShieldAlert } from 'lucide-react';

const GeneratedPasswordModal = ({ password, onConfirm, onCancel }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(password);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in duration-300">
      <div className="bg-[#0a1628] border border-[#3bb5ff]/30 rounded-2xl w-full max-w-md shadow-[0_0_50px_-12px_rgba(59,181,255,0.3)] overflow-hidden animate-in zoom-in-95 duration-300">
        <div className="p-6 text-center space-y-4">
          <div className="mx-auto w-16 h-16 bg-[#3bb5ff]/10 rounded-full flex items-center justify-center mb-2">
            <ShieldAlert size={32} className="text-[#3bb5ff]" />
          </div>
          
          <h2 className="text-xl font-bold text-white tracking-tight">Save Your Password</h2>
          
          <p className="text-gray-400 text-sm leading-relaxed">
            A random password has been generated for your zero-knowledge encryption. 
            <span className="text-[#3bb5ff] font-semibold block mt-1">
              You MUST save this password now. It cannot be recovered later.
            </span>
          </p>

          <div className="relative group mt-6">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] rounded-lg blur opacity-30 group-hover:opacity-50 transition duration-1000"></div>
            <div className="relative flex items-center gap-3 bg-[#060d1a] border border-[#1a3a5c] rounded-lg px-4 py-4 font-mono text-lg text-white break-all select-all">
              <span className="flex-1 text-center">{password}</span>
              <button 
                onClick={handleCopy}
                className="p-2 hover:bg-[#0f1f3a] rounded-md transition-colors text-[#3bb5ff] flex-shrink-0"
                title="Copy to clipboard"
              >
                {copied ? <Check size={20} /> : <Copy size={20} />}
              </button>
            </div>
          </div>

          <div className="pt-6 flex flex-col gap-3">
            <button
              onClick={onConfirm}
              className="w-full py-3.5 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] hover:from-[#005a9e] hover:to-[#2aa5ef] text-white rounded-xl font-bold shadow-lg shadow-[#3bb5ff]/20 transition-all active:scale-[0.98] btn-click"
            >
              I Have Safely Saved It
            </button>
            <button
              onClick={onCancel}
              className="w-full py-2.5 text-gray-500 hover:text-gray-300 text-sm transition-colors"
            >
              Cancel Upload
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GeneratedPasswordModal;
