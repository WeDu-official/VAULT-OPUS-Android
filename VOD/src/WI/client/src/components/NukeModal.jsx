// NukeModal.jsx (FOR CLIENT/DESKTOP) from the VAULT OPUS PROJECT version 1-beta-release-5
// ==================== FULL CLIENT/DESKTOP GUI====================
import React, { useState } from 'react';
import { Bomb, AlertTriangle } from 'lucide-react';

export default function NukeModal({ isOpen, onClose, dbName, onConfirm }) {
    const [confirmText, setConfirmText] = useState('');
    const [isNuking, setIsNuking] = useState(false);

    if (!isOpen) return null;

    const handleConfirm = async () => {
        if (confirmText.trim().toUpperCase() !== 'NUKE') return;
        setIsNuking(true);
        await onConfirm();
        setIsNuking(false);
        setConfirmText('');
    };

    const handleClose = () => {
        setConfirmText('');
        onClose();
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            <div className="bg-[#0a1628] border border-orange-900/50 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl animate-in fade-in zoom-in duration-200">
                {/* Header */}
                <div className="px-6 py-4 border-b border-orange-900/30 bg-gradient-to-r from-orange-900/20 to-red-900/20 flex justify-between items-center">
                    <h3 className="text-lg font-semibold text-orange-400 flex items-center gap-2">
                        <Bomb size={20} />
                        ☢️ NUKE VOLUME
                    </h3>
                    <button onClick={handleClose} className="text-gray-400 hover:text-white transition-colors">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <div className="p-6 space-y-5">
                    {/* Warning Banner */}
                    <div className="bg-red-900/20 border border-red-900/40 rounded-xl p-4 flex gap-3">
                        <AlertTriangle size={24} className="text-red-400 flex-shrink-0 mt-0.5" />
                        <div className="text-sm text-red-300/90">
                            <p className="font-bold text-red-400 mb-1">EXTREME DANGER</p>
                            <p>This will <strong>permanently destroy ALL data</strong> in the volume while keeping the empty database file.</p>
                        </div>
                    </div>

                    {/* Target Info */}
                    <div className="bg-[#060d1a] border border-[#1a3a5c] rounded-xl p-4">
                        <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Target Volume</p>
                        <p className="text-lg font-mono text-orange-300">{dbName}</p>
                    </div>

                    {/* What gets destroyed */}
                    <div className="space-y-2">
                        <p className="text-xs text-gray-500 uppercase tracking-wider">Will be destroyed:</p>
                        <ul className="text-sm text-gray-400 space-y-1.5 pl-1">
                            <li className="flex items-center gap-2">
                                <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                                All files and folders
                            </li>
                            <li className="flex items-center gap-2">
                                <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                                All versions of all items
                            </li>
                            <li className="flex items-center gap-2">
                                <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                                All Discord message references
                            </li>
                            <li className="flex items-center gap-2">
                                <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />
                                Database will be vacuumed (empty but kept)
                            </li>
                        </ul>
                    </div>

                    {/* Confirmation Input */}
                    <div className="space-y-2">
                        <label className="text-xs text-orange-400/70 uppercase tracking-wider font-bold">
                            Type <span className="text-orange-400 font-mono">NUKE</span> to confirm
                        </label>
                        <input
                            type="text"
                            value={confirmText}
                            onChange={(e) => setConfirmText(e.target.value)}
                            placeholder="Type NUKE here..."
                            className="w-full bg-[#060d1a] border border-orange-900/40 focus:border-orange-500 rounded-lg px-4 py-2.5 text-gray-200 outline-none transition-colors shadow-inner font-mono tracking-widest uppercase"
                            autoFocus
                            disabled={isNuking}
                        />
                    </div>
                </div>

                {/* Actions */}
                <div className="px-6 py-4 bg-[#0d1b2e] flex justify-end gap-3 border-t border-[#1a3a5c]">
                    <button
                        onClick={handleClose}
                        disabled={isNuking}
                        className="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white transition-colors disabled:opacity-50"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleConfirm}
                        disabled={confirmText.trim().toUpperCase() !== 'NUKE' || isNuking}
                        className="px-6 py-2 rounded-lg text-sm font-bold transition-all duration-200 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-500 hover:to-red-500 text-white shadow-[0_0_25px_rgba(239,68,68,0.4)]"
                    >
                        {isNuking ? (
                            <span className="flex items-center gap-2">
                                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                </svg>
                                Nuking...
                            </span>
                        ) : (
                            <span className="flex items-center gap-2">
                                <Bomb size={14} />
                                CONFIRM NUKE
                            </span>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}