// VolumeCreationModal.jsx (FOR CLIENT/DESKTOP) from the VAULT OPUS PROJECT version 1-beta-release-5
// ==================== FULL CLIENT/DESKTOP GUI====================
import React, { useState, useEffect } from 'react';

export default function VolumeCreationModal({
  isOpen,
  onClose,
  onConfirm,
  uploadFiles,
  uploadOptions
}) {
  const [volumeName, setVolumeName] = useState('');
  const [error, setError] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setVolumeName('');
      setError('');
      setIsCreating(false);
    }
  }, [isOpen]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    let trimmedName = volumeName.trim();
    if (!trimmedName) {
      setError('Please enter a volume name');
      return;
    }

    if (!trimmedName.endsWith('.db')) {
      trimmedName += '.db';
    }

    setIsCreating(true);
    setError('');

    try {
      await onConfirm(trimmedName, uploadFiles, uploadOptions);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to create volume');
      setIsCreating(false);
    }
  };

  const handleCancel = () => {
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
      <div className="bg-[#0a1628] border border-[#1a3a5c] rounded-xl shadow-2xl p-6 w-full max-w-md animate-in zoom-in-95 duration-200 relative">
        {/* Close button */}
        <button
          onClick={handleCancel}
          className="absolute top-4 right-4 w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-white hover:bg-[#1a3a5c] transition-all duration-150 active:scale-95"
          title="Cancel volume creation"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>

        <div className="flex items-center gap-3 mb-4 text-[#3bb5ff] pt-2">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
          <h3 className="text-lg font-semibold text-white">Create New Volume</h3>
        </div>

        <p className="text-gray-300 text-sm mb-5">
          No volume selected. Create a new SQLite database to store your upload.
        </p>

        {uploadFiles && uploadFiles.length > 0 && (
          <div className="bg-[#060d1a] border border-[#1a3a5c] rounded-lg p-3 mb-4">
            <p className="text-xs text-[#3bb5ff]/50 uppercase tracking-wider mb-1">Uploading:</p>
            <p className="text-sm text-gray-300 truncate">{uploadFiles[0].name}</p>
            {uploadFiles.length > 1 && (
              <p className="text-xs text-gray-500">+{uploadFiles.length - 1} more files</p>
            )}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-xs text-[#3bb5ff]/70 mb-2 uppercase tracking-wide">Volume Name</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={volumeName}
                onChange={(e) => {
                  setVolumeName(e.target.value);
                  setError('');
                }}
                placeholder="my_volume.db"
                className="flex-1 bg-[#060d1a] border border-[#1a3a5c] focus:border-[#3bb5ff] rounded-lg px-4 py-2.5 text-gray-200 outline-none transition-colors shadow-inner"
                autoFocus
                disabled={isCreating}
              />
            </div>
            {error && (
              <p className="text-red-400 text-xs mt-2 flex items-center gap-1">
                <svg className="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                {error}
              </p>
            )}
          </div>

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={handleCancel}
              disabled={isCreating}
              className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-all duration-150 active:scale-95 disabled:opacity-50 disabled:hover:text-gray-400"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isCreating}
              className="px-4 py-2 text-sm bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] hover:from-[#005a9e] hover:to-[#2aa5ef] text-white rounded-lg transition-all duration-150 active:scale-95 shadow-md disabled:opacity-50 disabled:hover:from-[#006fbe] disabled:hover:to-[#3bb5ff] flex items-center gap-2"
            >
              {isCreating ? (
                <>
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Creating...
                </>
              ) : (
                'Create & Upload'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}