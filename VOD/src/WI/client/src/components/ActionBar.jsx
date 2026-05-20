// ActionBar.jsx (FOR CLIENT/DESKTOP) from the VAULT OPUS PROJECT version 1-beta-release-6-ESEN-2
// ==================== FULL CLIENT/DESKTOP GUI====================
import React, { useState, useRef } from 'react';
import FolderPicker from './FolderPicker';
import GeneratedPasswordModal from './GeneratedPasswordModal';

export default function ActionBar({ onUpload, onDownload, onDeleteRequest, selectedItems = [], selectedDb, currentPath, onAlert }) {
  const hasSelection = selectedItems.length > 0;
  const [showUploadMenu, setShowUploadMenu] = useState(false);
  const [showFolderPicker, setShowFolderPicker] = useState(false);
  const [encryption, setEncryption] = useState('automatic');
  const [password, setPassword] = useState('');
  const [randomSeed, setRandomSeed] = useState(false);
  const [zeroKnowledge, setZeroKnowledge] = useState(false);
  const [uploadPaths, setUploadPaths] = useState([]);
  const [uploadName, setUploadName] = useState('');
  const [newVersionString, setNewVersionString] = useState('');
  const [nameCheck, setNameCheck] = useState(true);
  const [strictnessMode, setStrictnessMode] = useState('NA');
  const [chunkSizeMb, setChunkSizeMb] = useState('');
  const [minimize, setMinimize] = useState(false);

  const [generatedPassword, setGeneratedPassword] = useState('');
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  const generateRandomPassword = () => {
    const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+";
    return Array.from(crypto.getRandomValues(new Uint32Array(24)))
      .map((x) => chars[x % chars.length])
      .join("");
  };

  const handleStartUpload = () => {
    if (uploadPaths.length === 0) {
      onAlert("Please select at least one path to upload.", "Upload Error");
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
    // Each item gets its own upload task
    uploadPaths.forEach(path => {
      onUpload(
        [{ path: path, name: path.split(/[/\\]/).pop() }],
        encryption,
        finalPassword,
        {
          randomSeed: false,
          saveHash: encryption === 'not_automatic' ? !zeroKnowledge : true,
          uploadName: uploadPaths.length === 1 ? uploadName : '', // Only apply custom name if single item
          uploadMode: 'new_upload',
          newVersionString,
          nameCheck,
          strictnessMode,
          chunkSizeMb: chunkSizeMb ? parseFloat(chunkSizeMb) : undefined,
          idBased: false,
          minimize
        }
      );
    });
    resetUploadForm();
  };

  const resetUploadForm = () => {
    setShowUploadMenu(false);
    setUploadPaths([]);
    setPassword('');
    setRandomSeed(false);
    setZeroKnowledge(false);
    setUploadName('');
    setNewVersionString('');
    setNameCheck(true);
    setStrictnessMode('NA');
    setChunkSizeMb('');
    setMinimize(false);
    setGeneratedPassword('');
    setShowPasswordModal(false);
  };

  return (
    <div className="px-6 py-4 bg-[#0a1628] border-b border-[#1a3a5c] flex flex-wrap items-center justify-between gap-4 shadow-sm z-10 relative">
      <div className="flex gap-3">
        <div className="relative">
          <button
            onClick={() => setShowUploadMenu(!showUploadMenu)}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] hover:from-[#005a9e] hover:to-[#2aa5ef] text-white rounded-md font-medium shadow-lg shadow-[#3bb5ff]/20 transition-all hover:-translate-y-0.5 active:translate-y-0 btn-click"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
            New Upload
          </button>

          {showUploadMenu && (
            <div className={`absolute top-full left-0 mt-2 ${showFolderPicker ? 'w-[500px]' : 'w-96'} bg-[#0a1628] border border-[#1a3a5c] rounded-lg shadow-xl z-50 animate-in fade-in slide-in-from-top-2 overflow-hidden`}>
              {showFolderPicker ? (
                <div className="flex flex-col h-[500px]">
                  <div className="sticky top-0 bg-[#0a1628] border-b border-[#1a3a5c] p-3 z-10">
                    <button onClick={() => setShowFolderPicker(false)} className="text-[#3bb5ff] hover:text-white text-sm flex items-center gap-1">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
                      Back to options
                    </button>
                  </div>
                  <FolderPicker
                    initialPath={uploadPaths[0] || ''}
                    onSelect={(paths) => {
                      setUploadPaths(paths);
                      setShowFolderPicker(false);
                    }}
                    onCancel={() => setShowFolderPicker(false)}
                    showFiles={true}
                    multiple={true}
                  />
                </div>
              ) : (
                <div className="p-4 space-y-4">
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider border-b border-[#1a3a5c] pb-2">Upload Options</h3>

                  {/* Local Path */}
                  <div>
                    <label className="block text-xs text-[#3bb5ff]/70 mb-1 uppercase tracking-wide">Local Path</label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        readOnly
                        value={uploadPaths.length > 0
                          ? `${uploadPaths.length} item(s) selected: ${uploadPaths[0]}${uploadPaths.length > 1 ? '...' : ''}`
                          : ''}
                        placeholder="Select files or folders..."
                        className="flex-1 bg-[#060d1a] border border-[#1a3a5c] rounded px-3 py-2 text-sm focus:border-[#3bb5ff] outline-none placeholder-gray-600 text-gray-200 cursor-default"
                        onClick={() => setShowFolderPicker(true)}
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

                  {/* Upload Name - Only relevant for single item upload */}
                  {uploadPaths.length <= 1 && (
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
                  )}

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
          )}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => {
            const event = new CustomEvent('open-settings');
            window.dispatchEvent(event);
          }}
          className="flex items-center gap-2 px-4 py-2 bg-[#0f1f3a] hover:bg-[#1a3a5c] text-gray-200 rounded-md transition-all duration-150 active:scale-95 btn-click border border-[#1a3a5c]"
          title="Settings"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
          Settings
        </button>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onDownload(false)}
            disabled={!hasSelection}
            className="flex items-center gap-2 px-4 py-2 bg-[#0f1f3a] hover:bg-[#1a3a5c] disabled:opacity-40 disabled:hover:bg-[#0f1f3a] text-gray-200 rounded-md transition-all duration-150 active:scale-95 ripple-btn btn-click border border-[#1a3a5c]"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
            Download
          </button>
          <button
            onClick={() => onDeleteRequest({ showVersionControls: false })}
            disabled={!hasSelection}
            className="flex items-center gap-2 px-4 py-2 bg-red-900/20 hover:bg-red-900/40 text-red-400 disabled:opacity-40 disabled:hover:bg-red-900/20 border border-red-900/40 rounded-md transition-all duration-150 active:scale-95 ripple-btn btn-click"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
            Delete
          </button>
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