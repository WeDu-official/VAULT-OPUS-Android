//NewVersionUploadModal.jsx
import React, { useState, useEffect } from 'react';
import FolderPicker from './FolderPicker';
import GeneratedPasswordModal from './GeneratedPasswordModal';

export default function NewVersionUploadModal({ targetItemPath, selectedDb, onUpload, onClose, onAlert }) {
  const [showFolderPicker, setShowFolderPicker] = useState(false);
  const [encryption, setEncryption] = useState('automatic');
  const [password, setPassword] = useState('');
  const [randomSeed, setRandomSeed] = useState(false);
  const [zeroKnowledge, setZeroKnowledge] = useState(false);
  const [uploadPath, setUploadPath] = useState('');
  const [uploadName, setUploadName] = useState('');
  const [newVersionString, setNewVersionString] = useState('');
  const [nameCheck, setNameCheck] = useState(true);
  const [strictnessMode, setStrictnessMode] = useState('NA');
  const [chunkSizeMb, setChunkSizeMb] = useState('');
  const [minimize, setMinimize] = useState(false);

  const [additionMode, setAdditionMode] = useState(false);
  const [sourceVersion, setSourceVersion] = useState('');
  const [availableVersions, setAvailableVersions] = useState([]);
  const [isLoadingVersions, setIsLoadingVersions] = useState(false);

  const [generatedPassword, setGeneratedPassword] = useState('');
  const [showPasswordModal, setShowPasswordModal] = useState(false);

  const generateRandomPassword = () => {
    const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+";
    return Array.from(crypto.getRandomValues(new Uint32Array(24)))
      .map((x) => chars[x % chars.length])
      .join("");
  };

  useEffect(() => {
    if (targetItemPath && selectedDb) {
      setIsLoadingVersions(true);
      // First get itemid
      fetch(`http://localhost:8000/api/listfiles?db=${encodeURIComponent(selectedDb)}&path=${encodeURIComponent(targetItemPath)}`)
        .then(res => res.json())
        .then(pathData => {
          let itemid = null;
          if (pathData.results) {
            const keys = Object.keys(pathData.results);
            if (keys.length > 0) itemid = keys[0];
          }
          if (!itemid) throw new Error('Could not resolve itemid');
          return fetch(`http://localhost:8000/api/listfiles?db=${encodeURIComponent(selectedDb)}&itemid=${encodeURIComponent(itemid)}`);
        })
        .then(res => res.json())
        .then(versionsData => {
          const versionSet = new Set();
          const versionData = [];
          if (versionsData.results) {
            Object.values(versionsData.results).forEach(item => {
              if (item.version && !versionSet.has(item.version)) {
                versionSet.add(item.version);
                versionData.push({
                  version: item.version,
                  timestamp: item.upload_timestamp || ''
                });
              }
            });
          }
          // Sort newest first
          const sorted = versionData.sort((a, b) => {
            if (a.timestamp && b.timestamp) return new Date(b.timestamp) - new Date(a.timestamp);
            return b.version.localeCompare(a.version, undefined, { numeric: true, sensitivity: 'base' });
          }).map(v => v.version);
          setAvailableVersions(sorted);
          if (sorted.length > 0) setSourceVersion(sorted[0]);
        })
        .catch(err => console.error('Error fetching versions:', err))
        .finally(() => setIsLoadingVersions(false));
    }
  }, [targetItemPath, selectedDb]);

  const handleStartUpload = () => {
    if (!uploadPath) {
      onAlert("Please select a path to upload.", "Upload Error");
      return;
    }

    // Validation for Not Automatic encryption
    if (encryption === 'not_automatic' && !minimize) {
      if (!password && !randomSeed) {
        onAlert("Please provide a password or select 'Random' for non-automatic encryption.", "Missing Password");
        return;
      }

      if (randomSeed) {
        const pass = generateRandomPassword();
        setGeneratedPassword(pass);
        setShowPasswordModal(true);
        return; // Wait for modal confirmation
      }
    }

    proceedWithUpload(password);
  };

  const proceedWithUpload = (finalPassword) => {
    onUpload(
      [{ path: uploadPath, name: uploadPath.split(/[/\\]/).pop() }],
      encryption,
      finalPassword,
      {
        randomSeed: false, // We've already handled it or it's not random
        saveHash: encryption === 'not_automatic' ? !zeroKnowledge : true,
        uploadName,
        uploadMode: 'new_version',
        targetItemPath: targetItemPath,
        newVersionString,
        nameCheck,
        strictnessMode,
        chunkSizeMb: chunkSizeMb ? parseFloat(chunkSizeMb) : undefined,
        idBased: false,
        additionMode,
        sourceVersion,
        minimize
      }
    );
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
      <div className="bg-[#0a1628] border border-[#1a3a5c] rounded-xl shadow-2xl w-full max-w-xl max-h-[90vh] overflow-hidden animate-in zoom-in-95 duration-200 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[#1a3a5c] sticky top-0 bg-[#0a1628] z-10">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-[#3bb5ff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4-4m0 0L8 8m4-4v12"></path>
            </svg>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">New Version Upload</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-[#0f1f3a] rounded-full transition-colors text-gray-400"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
          </button>
        </div>

        {/* Target Item Info */}
        <div className="mx-4 mt-4 p-3 bg-[#3bb5ff]/10 border border-[#3bb5ff]/30 rounded-lg">
          <div className="text-[10px] text-[#3bb5ff] uppercase tracking-wider mb-1">Target Item</div>
          <div className="text-xs text-gray-300 font-mono truncate">{targetItemPath}</div>
        </div>

        <div className="p-4 space-y-4 flex-1 overflow-y-auto custom-scrollbar">
          {showFolderPicker ? (
            <div className="space-y-3 h-[500px] flex flex-col">
              <div className="sticky top-0 bg-[#0a1628] border-b border-[#1a3a5c] p-3 -mx-4 -mt-3">
                <button onClick={() => setShowFolderPicker(false)} className="text-[#3bb5ff] hover:text-white text-sm flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
                  Back to options
                </button>
              </div>
              <FolderPicker
                initialPath={uploadPath}
                onSelect={(path) => {
                  setUploadPath(path);
                  setShowFolderPicker(false);
                }}
                onCancel={() => setShowFolderPicker(false)}
                showFiles={true}
              />
            </div>
          ) : (
            <div className="space-y-4">
              {/* Upload Mode Selector */}
              <div className="bg-[#0f1f3a] p-3 rounded-lg border border-[#1a3a5c] space-y-2">
                <label className="block text-xs text-[#3bb5ff]/70 uppercase tracking-wide">Upload Strategy</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => setAdditionMode(false)}
                    className={`flex flex-col items-center gap-1 p-2 rounded border transition-all ${!additionMode 
                      ? 'bg-[#3bb5ff]/20 border-[#3bb5ff] text-white' 
                      : 'bg-[#060d1a] border-[#1a3a5c] text-gray-500 hover:border-[#1a3a5c]/80'}`}
                  >
                    <span className="text-xs font-bold">Independent</span>
                    <span className="text-[9px] opacity-60">Fresh Version</span>
                  </button>
                  <button
                    onClick={() => setAdditionMode(true)}
                    className={`flex flex-col items-center gap-1 p-2 rounded border transition-all ${additionMode 
                      ? 'bg-[#3bb5ff]/20 border-[#3bb5ff] text-white' 
                      : 'bg-[#060d1a] border-[#1a3a5c] text-gray-500 hover:border-[#1a3a5c]/80'}`}
                  >
                    <span className="text-xs font-bold">Addition</span>
                    <span className="text-[9px] opacity-60">Keep Previous</span>
                  </button>
                </div>
                
                {additionMode && (
                  <div className="pt-2 animate-in slide-in-from-top-1 duration-200">
                    <label className="block text-[10px] text-[#3bb5ff]/50 mb-1 uppercase">Source Version</label>
                    {isLoadingVersions ? (
                      <div className="text-[10px] text-gray-500 italic">Loading versions...</div>
                    ) : (
                      <select
                        value={sourceVersion}
                        onChange={(e) => setSourceVersion(e.target.value)}
                        className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded px-2 py-1.5 text-xs focus:border-[#3bb5ff] outline-none text-gray-200"
                      >
                        {availableVersions.map(v => (
                          <option key={v} value={v}>{v}</option>
                        ))}
                        {availableVersions.length === 0 && <option value="">Latest (Auto)</option>}
                      </select>
                    )}
                  </div>
                )}
              </div>

              {/* Local Path */}
              <div>
                <label className="block text-xs text-[#3bb5ff]/70 mb-1 uppercase tracking-wide">Local Path</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={uploadPath}
                    onChange={(e) => setUploadPath(e.target.value)}
                    placeholder="Select a file or folder..."
                    className="flex-1 bg-[#060d1a] border border-[#1a3a5c] rounded px-3 py-2 text-sm focus:border-[#3bb5ff] outline-none placeholder-gray-600 text-gray-200"
                  />
                  <button
                    onClick={() => setShowFolderPicker(true)}
                    className="px-3 py-2 bg-[#0f1f3a] border border-[#1a3a5c] rounded hover:bg-[#1a3a5c] text-sm text-gray-300 transition-all duration-150 btn-click"
                  >
                    Browse
                  </button>
                </div>
              </div>

              {/* Encryption Mode */}
              <div style={{ opacity: minimize ? 0.5 : 1, pointerEvents: minimize ? 'none' : 'auto' }}>
                <label className="block text-xs text-[#3bb5ff]/70 mb-1 uppercase tracking-wide">Encryption Mode</label>
                <select
                  value={encryption}
                  disabled={minimize}
                  onChange={(e) => setEncryption(e.target.value)}
                  className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded px-3 py-2 text-sm focus:border-[#3bb5ff] outline-none text-gray-200"
                >
                  <option value="automatic">Automatic (Bot-managed)</option>
                  <option value="off">Off (No Encryption)</option>
                  <option value="not_automatic">Not Automatic (Password)</option>
                </select>
              </div>

              {/* Password Seed */}
              {encryption === 'not_automatic' && (
                <div style={{ opacity: minimize ? 0.5 : 1, pointerEvents: minimize ? 'none' : 'auto' }}>
                  <label className="block text-xs text-[#3bb5ff]/70 mb-1 uppercase tracking-wide">Password Seed</label>
                  <div className="flex gap-2">
                    <input
                      type="password"
                      value={password}
                      disabled={minimize}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter password seed..."
                      className="flex-1 bg-[#060d1a] border border-[#1a3a5c] rounded px-3 py-2 text-sm focus:border-[#3bb5ff] outline-none placeholder-gray-600 text-gray-200"
                    />
                    <label className="flex items-center gap-2 px-3 py-1.5 bg-[#0f1f3a] border border-[#1a3a5c] rounded cursor-pointer hover:bg-[#1a3a5c] transition-all duration-150 active:scale-95">
                      <input
                        type="checkbox"
                        checked={randomSeed}
                        disabled={minimize}
                        onChange={(e) => setRandomSeed(e.target.checked)}
                        className="w-3 h-3 accent-[#3bb5ff]"
                      />
                      <span className="text-xs text-gray-300">Random</span>
                    </label>
                  </div>
                </div>
              )}

              {/* New Version String */}
              <div>
                <label className="block text-xs text-[#3bb5ff]/70 mb-1 uppercase tracking-wide">Version String</label>
                <input
                  type="text"
                  value={newVersionString}
                  onChange={(e) => setNewVersionString(e.target.value)}
                  placeholder="Override version string (e.g., 1.0.0)"
                  className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded px-3 py-2 text-sm focus:border-[#3bb5ff] outline-none placeholder-gray-600 text-gray-200"
                />
              </div>

              {/* Upload Name */}
              <div>
                <label className="block text-xs text-[#3bb5ff]/70 mb-1 uppercase tracking-wide">Custom Name</label>
                <input
                  type="text"
                  value={uploadName}
                  onChange={(e) => setUploadName(e.target.value)}
                  placeholder="Optional custom name (max 60 chars)"
                  maxLength={60}
                  className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded px-3 py-2 text-sm focus:border-[#3bb5ff] outline-none placeholder-gray-600 text-gray-200"
                />
              </div>

              {/* Strictness Mode */}
              <div>
                <label className="block text-xs text-[#3bb5ff]/70 mb-1 uppercase tracking-wide">Strictness Mode</label>
                <select
                  value={strictnessMode}
                  onChange={(e) => setStrictnessMode(e.target.value)}
                  className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded px-3 py-2 text-sm focus:border-[#3bb5ff] outline-none text-gray-200"
                >
                  <option value="NA">NOT ATOMIC (DEFAULT)</option>
                  <option value="SA">SOFT ATOMIC</option>
                  <option value="HA">HARD ATOMIC</option>
                </select>
              </div>

              {/* Chunk Size */}
              <div>
                <label className="block text-xs text-[#3bb5ff]/70 mb-1 uppercase tracking-wide">Chunk Size (MB)</label>
                <input
                  type="number"
                  step="0.1"
                  min="1"
                  max="50"
                  value={chunkSizeMb}
                  onChange={(e) => setChunkSizeMb(e.target.value)}
                  placeholder="Auto: 5-10 (off), 3-7.5 (enc)"
                  className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded px-3 py-2 text-sm focus:border-[#3bb5ff] outline-none placeholder-gray-600 text-gray-200"
                />
              </div>

              {/* Name Check Checkbox */}
              <label className="flex items-center gap-2 px-3 py-2 bg-[#0f1f3a] border border-[#1a3a5c] rounded cursor-pointer hover:bg-[#1a3a5c] transition-all duration-150 active:scale-95">
                <input
                  type="checkbox"
                  checked={nameCheck}
                  onChange={(e) => setNameCheck(e.target.checked)}
                  className="w-3 h-3 accent-[#3bb5ff]"
                />
                <span className="text-xs text-gray-300">Name Check</span>
              </label>

              {/* Minimize Checkbox */}
              <label className="flex items-center gap-2 px-3 py-2 bg-[#0f1f3a] border border-[#1a3a5c] rounded cursor-pointer hover:bg-[#1a3a5c] transition-all duration-150 active:scale-95">
                <input
                  type="checkbox"
                  checked={minimize}
                  onChange={(e) => setMinimize(e.target.checked)}
                  className="w-3 h-3 accent-[#3bb5ff]"
                />
                <span className="text-xs text-gray-300">Minimize (Reuse Chunks)</span>
              </label>

              {/* Zero Knowledge Encryption Checkbox - Only show if not automatic */}
              {encryption === 'not_automatic' && (
                <label 
                  className="flex items-center gap-2 px-3 py-2 bg-[#0f1f3a] border border-[#1a3a5c] rounded cursor-pointer hover:bg-[#1a3a5c] transition-all duration-150 active:scale-95"
                  style={{ opacity: minimize ? 0.5 : 1, pointerEvents: minimize ? 'none' : 'auto' }}
                >
                  <input
                    type="checkbox"
                    checked={zeroKnowledge}
                    disabled={minimize}
                    onChange={(e) => setZeroKnowledge(e.target.checked)}
                    className="w-3 h-3 accent-[#3bb5ff]"
                  />
                  <span className="text-xs text-gray-300">Zero Knowledge Encryption</span>
                </label>
              )}

              <button
                onClick={handleStartUpload}
                className="w-full py-2.5 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] hover:from-[#005a9e] hover:to-[#2aa5ef] text-white rounded-md text-sm font-medium transition-all duration-150 shadow-lg shadow-[#3bb5ff]/20 mt-2 active:scale-95 ripple-btn btn-click"
              >
                Start Upload
              </button>
            </div>
          )}
        </div>
      </div>

      {showPasswordModal && (
        <GeneratedPasswordModal
          password={generatedPassword}
          onConfirm={() => proceedWithUpload(generatedPassword)}
          onCancel={() => setShowPasswordModal(false)}
        />
      )}
    </div>
  );
}