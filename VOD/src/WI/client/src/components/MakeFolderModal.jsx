// MakeFolderModal.jsx (FOR CLIENT/DESKTOP) from the VAULT OPUS PROJECT version 1-beta-release-5
// ==================== FULL CLIENT/DESKTOP GUI====================
import React, { useState } from 'react';
import ArchiveFolderPicker from './ArchiveFolderPicker';

export default function MakeFolderModal({ selectedDb, currentPath, onConfirm, onCancel }) {
  const [folderName, setFolderName] = useState('');
  const [selectedParent, setSelectedParent] = useState(currentPath || '.');
  const [showFolderPicker, setShowFolderPicker] = useState(false);
  const [parentLabel, setParentLabel] = useState(currentPath === '.' ? 'Root' : currentPath);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    setError('');

    const name = folderName.trim();
    if (!name) {
      setError('Folder name cannot be empty.');
      return;
    }

    // Validate forbidden characters
    const forbidden = ['/', '\\', ':', '*', '?', '"', '<', '>', '|'];
    for (const c of forbidden) {
      if (name.includes(c)) {
        setError(`Folder name cannot contain '${c}'.`);
        return;
      }
    }

    setSubmitting(true);
    try {
      const res = await fetch('http://localhost:8000/api/folders/make', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          db_name: selectedDb,
          folder_name: name,
          parent_path: selectedParent,
          id_based: false
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to create folder');
      }

      const data = await res.json();
      onConfirm(data.message);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
      <div className="bg-[#0a1628] border border-[#1a3a5c] rounded-xl shadow-2xl p-6 w-full max-w-md animate-in zoom-in-95 duration-200">
        <div className="flex items-center gap-3 mb-6 text-[#3bb5ff]">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 13h6m-3-3v6m-5 4h10a2 2 0 002-2V9a2 2 0 00-2-2h-2.586a1 1 0 01-.707-.293l-1.414-1.414a1 1 0 00-.707-.293H7a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <h3 className="text-xl font-bold text-white">Create New Folder</h3>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Parent Location */}
          <div>
            <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Parent Location</label>
            {showFolderPicker ? (
              <div className="max-h-[300px] overflow-hidden border border-[#1a3a5c] rounded-lg bg-[#060d1a]">
                <ArchiveFolderPicker
                  selectedDb={selectedDb}
                  onSelect={(path) => {
                    setSelectedParent(path);
                    setParentLabel(path === '.' ? 'Root' : path);
                    setShowFolderPicker(false);
                  }}
                  initialPath={selectedParent}
                />
              </div>
            ) : (
              <div className="flex gap-2">
                <div
                  className="flex-1 bg-[#060d1a] border border-[#1a3a5c] rounded-lg px-4 py-2.5 text-sm text-gray-300 cursor-pointer hover:border-[#3bb5ff]/50 transition-colors truncate"
                  onClick={() => setShowFolderPicker(true)}
                >
                  {parentLabel === '.' ? 'Root' : parentLabel === currentPath && currentPath !== '.' ? `${currentPath} (current)` : parentLabel}
                </div>
                <button
                  type="button"
                  onClick={() => setShowFolderPicker(true)}
                  className="px-3 py-2 bg-[#0f1f3a] border border-[#1a3a5c] rounded-lg hover:bg-[#1a3a5c] text-sm text-gray-300 transition-all btn-click"
                >
                  Browse
                </button>
              </div>
            )}
          </div>

          {/* Folder Name */}
          {!showFolderPicker && (
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Folder Name</label>
              <input
                type="text"
                value={folderName}
                onChange={(e) => setFolderName(e.target.value)}
                placeholder="Enter folder name..."
                className="w-full bg-[#060d1a] border border-[#1a3a5c] focus:border-[#3bb5ff] rounded-lg px-4 py-2.5 text-gray-200 outline-none transition-colors"
                autoFocus
                maxLength={60}
              />
              <p className="mt-1 text-[10px] text-gray-500">{'Max 60 characters. No special characters like / \\ : * ? " < > |'}</p>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="bg-red-900/20 border border-red-900/40 rounded-lg px-4 py-2 text-red-400 text-sm">
              {error}
            </div>
          )}

          {/* Actions */}
          {!showFolderPicker && (
            <div className="flex justify-end gap-3 pt-2 border-t border-[#1a3a5c]">
              <button
                type="button"
                onClick={onCancel}
                className="px-6 py-2 text-sm font-medium text-gray-400 hover:text-white transition-all active:scale-95"
                disabled={submitting}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting || !folderName.trim()}
                className="px-8 py-2 text-sm bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] hover:from-[#005a9e] hover:to-[#2aa5ef] text-white rounded-lg transition-all active:scale-95 shadow-lg font-bold disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? 'Creating...' : 'Create Folder'}
              </button>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}