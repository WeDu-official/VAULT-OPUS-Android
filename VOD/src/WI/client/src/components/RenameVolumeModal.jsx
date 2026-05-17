//RenameVolumeModal.jsx
import React, { useState, useEffect } from 'react';
import { Edit2, Save, X } from 'lucide-react';

export default function RenameVolumeModal({
  isOpen,
  onClose,
  onConfirm,
  currentName
}) {
  const [newName, setNewName] = useState('');
  const [error, setError] = useState('');
  const [isRenaming, setIsRenaming] = useState(false);

  useEffect(() => {
    if (isOpen && currentName) {
      setNewName(currentName.replace(/\.db$/i, ''));
      setError('');
      setIsRenaming(false);
    }
  }, [isOpen, currentName]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    let trimmedName = newName.trim();
    if (!trimmedName) {
      setError('Please enter a new name');
      return;
    }

    if (!trimmedName.endsWith('.db')) {
      trimmedName += '.db';
    }

    if (trimmedName === currentName) {
      onClose();
      return;
    }

    setIsRenaming(true);
    setError('');

    try {
      await onConfirm(currentName, trimmedName);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to rename volume');
      setIsRenaming(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
      <div className="bg-[#0a1628] border border-[#1a3a5c] rounded-xl shadow-2xl p-6 w-full max-w-md animate-in zoom-in-95 duration-200 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-white hover:bg-[#1a3a5c] transition-all duration-150 active:scale-95"
        >
          <X size={18} />
        </button>

        <div className="flex items-center gap-3 mb-4 text-[#3bb5ff] pt-2">
          <Edit2 size={24} />
          <h3 className="text-lg font-semibold text-white">Rename Volume</h3>
        </div>

        <p className="text-gray-300 text-sm mb-5">
          Change the name of the database file.
        </p>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-xs text-[#3bb5ff]/70 mb-2 uppercase tracking-wide">New Name</label>
            <input
              type="text"
              value={newName}
              onChange={(e) => {
                setNewName(e.target.value);
                setError('');
              }}
              placeholder="new_name"
              className="w-full bg-[#060d1a] border border-[#1a3a5c] focus:border-[#3bb5ff] rounded-lg px-4 py-2.5 text-gray-200 outline-none transition-colors shadow-inner"
              autoFocus
              disabled={isRenaming}
            />
            {error && (
              <p className="text-red-400 text-xs mt-2 flex items-center gap-1">
                {error}
              </p>
            )}
          </div>

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isRenaming}
              className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-all duration-150 active:scale-95"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isRenaming}
              className="px-4 py-2 text-sm bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] hover:from-[#005a9e] hover:to-[#2aa5ef] text-white rounded-lg transition-all duration-150 active:scale-95 shadow-md disabled:opacity-50 flex items-center gap-2"
            >
              {isRenaming ? 'Renaming...' : 'Save Name'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
