//DeleteModal.jsx
import React, { useState, useEffect } from 'react';

export default function DeleteModal({ isOpen, onClose, onConfirm, itemName, selectedItems = [], selectedDb, currentPath, onAlert, showVersionControls = false }) {
  const [scope, setScope] = useState(showVersionControls ? 'all' : 'all'); // Default to all
  const [type, setType] = useState('soft'); // soft, hard
  const [version, setVersion] = useState('');
  const [startVersion, setStartVersion] = useState('');
  const [endVersion, setEndVersion] = useState('');
  
  const [availableVersions, setAvailableVersions] = useState([]);
  const [loadingVersions, setLoadingVersions] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && selectedItems.length > 0 && selectedDb) {
      fetchVersions();
    }
  }, [isOpen, selectedItems, selectedDb]);

  const fetchVersions = async () => {
    try {
      setLoadingVersions(true);
      setError(null);
      
      const item = selectedItems[0];
      let itemid = item.itemid;
      
      // If we don't have itemid directly, we might need to fetch it via path
      if (!itemid) {
        const itemPath = currentPath === '.' ? item.displayName : `${currentPath}/${item.displayName}`;
        const pathResponse = await fetch(
          `http://localhost:8000/api/listfiles?db=${encodeURIComponent(selectedDb)}&path=${encodeURIComponent(itemPath)}`
        );
        if (!pathResponse.ok) throw new Error('Failed to fetch item details');
        const pathData = await pathResponse.json();
        
        if (pathData.results) {
          const keys = Object.keys(pathData.results);
          if (keys.length > 0) itemid = keys[0];
        }
      }

      if (!itemid) throw new Error('Could not find item identifier');

      // Now fetch all versions using the itemid
      const versionsResponse = await fetch(
        `http://localhost:8000/api/listfiles?db=${encodeURIComponent(selectedDb)}&itemid=${encodeURIComponent(itemid)}`
      );

      if (!versionsResponse.ok) throw new Error('Failed to fetch versions');
      const versionsData = await versionsResponse.json();

      // Extract versions from the results
      const versionSet = new Set();
      const versionData = [];
      if (versionsData.results) {
        Object.values(versionsData.results).forEach(item => {
          if (item.version && !versionSet.has(item.version)) {
            versionSet.add(item.version);
            versionData.push({
              version: item.version,
              upload_timestamp: item.upload_timestamp || ''
            });
          }
        });
      }

      // Sort versions by upload_timestamp (newest first)
      const sortedVersions = versionData
        .sort((a, b) => {
          if (a.upload_timestamp && b.upload_timestamp) {
            return new Date(b.upload_timestamp) - new Date(a.upload_timestamp);
          }
          const aParts = a.version.split('.').map(Number);
          const bParts = b.version.split('.').map(Number);
          for (let i = 0; i < Math.max(aParts.length, bParts.length); i++) {
            const aVal = aParts[i] || 0;
            const bVal = bParts[i] || 0;
            if (aVal !== bVal) return bVal - aVal;
          }
          return 0;
        })
        .map(v => v.version);

      setAvailableVersions(sortedVersions);
      
      // Auto-select latest version for specific delete
      if (sortedVersions.length > 0) {
        setVersion(sortedVersions[0]);
      }
    } catch (err) {
      console.error('Error fetching versions for delete modal:', err);
      setError(err.message);
    } finally {
      setLoadingVersions(false);
    }
  };

  if (!isOpen) return null;

  const handleConfirm = () => {
    if (scope === 'specific' && !version) {
      onAlert("Please select a specific version to delete.", "Missing Version");
      return;
    }
    
    if (scope === 'range' && (!startVersion || !endVersion)) {
      onAlert("Please select both a start and end version for the range.", "Missing Version Range");
      return;
    }

    const options = {
      scope,
      type,
      version: scope === 'specific' ? version : null,
      startVersion: scope === 'range' ? startVersion : null,
      endVersion: scope === 'range' ? endVersion : null
    };
    onConfirm(options);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-[#0a1628] border border-[#1a3a5c] rounded-2xl w-full max-w-md overflow-hidden shadow-2xl animate-in fade-in zoom-in duration-200">
        <div className="px-6 py-4 border-b border-[#1a3a5c] bg-[#0d1b2e] flex justify-between items-center">
          <h3 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
            <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            Delete Item
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6 space-y-6">
          <p className="text-sm text-gray-400">
            You are about to delete <span className="text-red-400 font-medium">"{itemName}"</span>. This action can be permanent depending on the options chosen.
          </p>

          {/* Scope Selection - Only show if requested and only 1 item selected */}
          {showVersionControls && selectedItems.length === 1 && (
            <div className="space-y-3">
              <label className="text-xs font-bold text-[#3bb5ff] uppercase tracking-wider">Deletion Scope</label>
              <div className="grid grid-cols-1 gap-2">
                <button
                  onClick={() => setScope('all')}
                  className={`px-4 py-3 rounded-xl border text-left transition-all duration-200 ${
                    scope === 'all' 
                      ? 'bg-[#1a3a5c]/40 border-[#3bb5ff] text-white shadow-[0_0_15px_rgba(59,181,255,0.2)]' 
                      : 'bg-[#0d1b2e] border-[#1a3a5c] text-gray-400 hover:border-[#3bb5ff]/50'
                  }`}
                >
                  <div className="font-medium">All Versions</div>
                  <div className="text-xs opacity-60">Delete every version of this item</div>
                </button>
                
                <button
                  onClick={() => setScope('specific')}
                  className={`px-4 py-3 rounded-xl border text-left transition-all duration-200 ${
                    scope === 'specific' 
                      ? 'bg-[#1a3a5c]/40 border-[#3bb5ff] text-white shadow-[0_0_15px_rgba(59,181,255,0.2)]' 
                      : 'bg-[#0d1b2e] border-[#1a3a5c] text-gray-400 hover:border-[#3bb5ff]/50'
                  }`}
                >
                  <div className="font-medium">Specific Version</div>
                  <div className="text-xs opacity-60">Only delete one version</div>
                </button>

                {scope === 'specific' && (
                  <div className="mt-1">
                    {loadingVersions ? (
                      <div className="text-xs text-gray-500 animate-pulse">Loading versions...</div>
                    ) : error ? (
                      <div className="text-xs text-red-400">Error loading versions: {error}</div>
                    ) : (
                      <select
                        value={version}
                        onChange={(e) => setVersion(e.target.value)}
                        className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-[#3bb5ff] transition-colors"
                      >
                        <option value="" disabled>Select version...</option>
                        {availableVersions.map((v, idx) => (
                          <option key={idx} value={v}>Version {v}</option>
                        ))}
                      </select>
                    )}
                  </div>
                )}

                <button
                  onClick={() => setScope('range')}
                  className={`px-4 py-3 rounded-xl border text-left transition-all duration-200 ${
                    scope === 'range' 
                      ? 'bg-[#1a3a5c]/40 border-[#3bb5ff] text-white shadow-[0_0_15px_rgba(59,181,255,0.2)]' 
                      : 'bg-[#0d1b2e] border-[#1a3a5c] text-gray-400 hover:border-[#3bb5ff]/50'
                  }`}
                >
                  <div className="font-medium">Version Range</div>
                  <div className="text-xs opacity-60">Delete a sequence of versions</div>
                </button>

                {scope === 'range' && (
                  <div className="grid grid-cols-2 gap-2 mt-1">
                    <div className="space-y-1">
                      <label className="text-[10px] text-gray-500 uppercase px-1">From</label>
                      {loadingVersions ? (
                        <div className="h-9 bg-[#060d1a] border border-[#1a3a5c] rounded-lg animate-pulse" />
                      ) : (
                        <select
                          value={startVersion}
                          onChange={(e) => setStartVersion(e.target.value)}
                          className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-[#3bb5ff] transition-colors"
                        >
                          <option value="">Start...</option>
                          {availableVersions.map((v, idx) => (
                            <option key={idx} value={v}>V {v}</option>
                          ))}
                        </select>
                      )}
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] text-gray-500 uppercase px-1">To</label>
                      {loadingVersions ? (
                        <div className="h-9 bg-[#060d1a] border border-[#1a3a5c] rounded-lg animate-pulse" />
                      ) : (
                        <select
                          value={endVersion}
                          onChange={(e) => setEndVersion(e.target.value)}
                          className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-[#3bb5ff] transition-colors"
                        >
                          <option value="">End...</option>
                          {availableVersions.map((v, idx) => (
                            <option key={idx} value={v}>V {v}</option>
                          ))}
                        </select>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Delete Type Selection */}
          <div className="space-y-3">
            <label className="text-xs font-bold text-[#3bb5ff] uppercase tracking-wider">Deletion Type</label>
            <div className="flex gap-4">
              <label className="flex-1 cursor-pointer group">
                <input
                  type="radio"
                  name="type"
                  className="hidden"
                  checked={type === 'soft'}
                  onChange={() => setType('soft')}
                />
                <div className={`p-3 rounded-xl border text-center transition-all duration-200 ${
                  type === 'soft' 
                    ? 'bg-green-500/10 border-green-500/50 text-green-400' 
                    : 'bg-[#0d1b2e] border-[#1a3a5c] text-gray-400 hover:border-green-500/30'
                }`}>
                  <div className="text-sm font-bold">SOFT DELETE</div>
                  <div className="text-[10px] opacity-70">Database only</div>
                </div>
              </label>
              
              <label className="flex-1 cursor-pointer group">
                <input
                  type="radio"
                  name="type"
                  className="hidden"
                  checked={type === 'hard'}
                  onChange={() => setType('hard')}
                />
                <div className={`p-3 rounded-xl border text-center transition-all duration-200 ${
                  type === 'hard' 
                    ? 'bg-red-500/10 border-red-500/50 text-red-400' 
                    : 'bg-[#0d1b2e] border-[#1a3a5c] text-gray-400 hover:border-red-500/30'
                }`}>
                  <div className="text-sm font-bold">HARD DELETE</div>
                  <div className="text-[10px] opacity-70">Remove attachments</div>
                </div>
              </label>
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
            disabled={loadingVersions && scope !== 'all'}
            className={`px-6 py-2 rounded-lg text-sm font-bold transition-all duration-200 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed ${
              type === 'hard' 
                ? 'bg-red-500 hover:bg-red-600 text-white shadow-[0_0_20px_rgba(239,68,68,0.3)]' 
                : 'bg-[#3bb5ff] hover:bg-[#2e9ee6] text-[#060d1a] shadow-[0_0_20px_rgba(59,181,255,0.3)]'
            }`}
          >
            Confirm Deletion
          </button>
        </div>
      </div>
    </div>
  );
}
