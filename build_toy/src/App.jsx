// ==================== ANDROID-FRIENDLY FULL-FEATURED App.jsx 1-R9====================
// Intercept all relative fetch calls to point to the backend at 127.0.0.1:8000
const originalFetch = window.fetch;
window.fetch = async (input, init) => {
  if (typeof input === 'string' && input.startsWith('/api/')) {
    input = 'http://127.0.0.1:8000' + input;
  }
  return originalFetch(input, init);
};

import React, { useState, useEffect, useRef } from 'react';

// ---------- Icon Set ----------
const Ico = {
  folder: <svg viewBox="0 0 20 20" fill="currentColor" className="w-12 h-12 text-[#3bb5ff]"><path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" /></svg>,
  file: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-12 h-12 text-gray-400"><path d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>,
  upload: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>,
  download: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>,
  trash: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>,
  back: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>,
  plus: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M12 4v16m8-8H4" /></svg>,
  close: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M6 18L18 6M6 6l12 12" /></svg>,
  menu: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-7 h-7"><path d="M4 6h16M4 12h16M4 18h16" /></svg>,
  settings: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>,
  cube: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>,
  clock: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
  terminal: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>,
  rename: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>,
  move: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" /></svg>,
  check: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M5 13l4 4L19 7" /></svg>,
  info: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
  newFolder: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M9 13h6m-3-3v6m-5 4h10a2 2 0 002-2V9a2 2 0 00-2-2h-2.586a1 1 0 01-.707-.293l-1.414-1.414a1 1 0 00-.707-.293H7a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>,
  selectAll: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M4 6h16M4 10h16M4 14h16M4 18h16" /></svg>,
  share: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" /></svg>,
  version: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" /><path d="M21 3v5h-5" /><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" /><path d="M8 16H3v5" /></svg>,
  alert: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M12 9v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
  copy: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>,
  folderOpen: <svg viewBox="0 0 20 20" fill="currentColor" className="w-6 h-6 text-[#3bb5ff]"><path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" /></svg>,
  home: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" /></svg>,
  import: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>,
  bomb: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
  externalLink: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6m4-3h6v6m-11 5L21 3" /></svg>,
};

// ---------- Helper Components ----------
function Sheet({ open, onClose, title, children }) {
  if (!open) return null;
  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="fixed bottom-0 left-0 right-0 z-50 safe-bottom" style={{ maxHeight: '85vh' }}>
        <div className="bg-[#0a1628] border-t border-[#1a3a5c] rounded-t-2xl shadow-2xl flex flex-col max-h-[85vh]">
          <div className="flex items-center justify-between p-4 border-b border-[#1a3a5c] sticky top-0 bg-[#0a1628] rounded-t-2xl z-10">
            <h3 className="text-lg font-bold text-white">{title}</h3>
            <button onClick={onClose} className="p-2 btn-touch text-gray-400 hover:text-white">{Ico.close}</button>
          </div>
          <div className="overflow-y-auto p-4 flex-1">{children}</div>
        </div>
      </div>
    </>
  );
}

function Modal({ open, onClose, title, children, wide }) {
  if (!open) return null;
  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className={`bg-[#0a1628] border border-[#1a3a5c] rounded-xl shadow-2xl ${wide ? 'w-full max-w-lg' : 'w-full max-w-md'} max-h-[85vh] overflow-y-auto p-4 animate-in fade-in`}>
          <div className="flex items-center justify-between mb-4 border-b border-[#1a3a5c] pb-3">
            <h3 className="text-lg font-bold text-white">{title}</h3>
            <button onClick={onClose} className="p-2 btn-touch text-gray-400 hover:text-white">{Ico.close}</button>
          </div>
          {children}
        </div>
      </div>
    </>
  );
}

function Toast({ message, type, onClose }) {
  useEffect(() => { const t = setTimeout(onClose, 3000); return () => clearTimeout(t); }, []);
  const bg = type === 'error' ? 'bg-red-900/80 border-red-500/50' : type === 'success' ? 'bg-green-900/80 border-green-500/50' : 'bg-[#0a1628] border-[#1a3a5c]';
  const icon = type === 'error' ? 'text-red-400' : type === 'success' ? 'text-green-400' : 'text-[#3bb5ff]';
  return (
    <div className={`fixed top-16 left-4 right-4 z-50 ${bg} border rounded-xl px-4 py-3 shadow-2xl flex items-center gap-3 animate-in fade-in`}>
      <span className={icon}>{Ico.alert}</span>
      <span className="text-sm text-gray-200 flex-1">{message}</span>
      <button onClick={onClose} className="text-gray-500 btn-touch p-1">{Ico.close}</button>
    </div>
  );
}

// ---------- Remote Folder Picker ----------
function RemoteFolderPicker({ initialPath, onSelect, onCancel, showFiles = false, multiSelect = false, singleSelectOnly = false }) {
  const [currentPath, setCurrentPath] = useState(initialPath || '');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedPaths, setSelectedPaths] = useState([]);

  const fetchDirectory = async (path) => {
    setLoading(true); setError(null);
    try {
      const url = path ? `/api/fs/browse?path=${encodeURIComponent(path)}` : `/api/fs/browse`;
      const r = await fetch(url);
      if (!r.ok) throw new Error('Failed to fetch');
      const data = await r.json();
      setCurrentPath(data.current_path);
      setItems(showFiles ? data.items : data.items.filter(i => i.is_dir));
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchDirectory(initialPath); }, [initialPath]);

  const toggleSelect = (path) => {
    if (singleSelectOnly) {
      setSelectedPaths(prev => prev.includes(path) ? [] : [path]);
      return;
    }
    setSelectedPaths(prev => prev.includes(path) ? prev.filter(p => p !== path) : [...prev, path]);
  };

  const handleItemTap = (item) => {
    if (item.name === '..') { fetchDirectory(item.path); return; }
    if (item.is_dir) {
      if (!multiSelect) {
        fetchDirectory(item.path);
      } else {
        fetchDirectory(item.path);
      }
    } else {
      if (multiSelect) {
        toggleSelect(item.path);
      } else {
        onSelect(item.path);
      }
    }
  };

  return (
    <div className="flex flex-col h-[70vh]">
      <div className="flex items-center gap-2 p-4 bg-[#0a1628] border-b border-[#1a3a5c]">
        <button onClick={async () => { const r = await fetch('/api/fs/home'); const d = await r.json(); fetchDirectory(d.path); }} className="p-3 btn-touch text-[#3bb5ff] bg-[#0f1f3a] rounded-xl">{Ico.home}</button>
        <div className="flex-1 overflow-hidden">
          <div className="text-[10px] text-[#3bb5ff] font-bold uppercase mb-0.5 opacity-50">Current Location</div>
          <div className="text-xs text-gray-300 font-mono truncate">{currentPath}</div>
        </div>
        {selectedPaths.length > 0 && (
          <div className="px-3 py-1.5 bg-[#3bb5ff]/20 border border-[#3bb5ff]/40 rounded-full">
            <span className="text-[10px] text-[#3bb5ff] font-black">{selectedPaths.length} SEL</span>
          </div>
        )}
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {loading ? <p className="text-center p-8 text-gray-500 animate-pulse">Scanning...</p> : error ? <p className="text-red-400 p-4 text-center">{error}</p> : items.map(item => {
          const isSel = selectedPaths.includes(item.path);
          const isDir = item.is_dir;
          const isBack = item.name === '..';
          return (
            <div key={item.path} className={`w-full flex items-center gap-3 px-4 py-3 rounded-2xl border btn-touch transition-all ${isSel ? 'bg-[#3bb5ff]/20 border-[#3bb5ff] text-white' : isDir ? 'text-[#3bb5ff] bg-[#0f1f3a]/40 border-[#1a3a5c]' : 'text-gray-300 bg-[#060d1a] border-[#1a3a5c]'}`}>
              {multiSelect && !isBack && (
                <button onClick={(e) => { e.stopPropagation(); toggleSelect(item.path); }} className={`w-7 h-7 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-all ${isSel ? 'bg-[#3bb5ff] border-[#3bb5ff]' : 'border-gray-600 bg-transparent'}`}>
                  {isSel && <div className="text-white">{Ico.check}</div>}
                </button>
              )}
              <button onClick={() => handleItemTap(item)} className="flex-1 flex items-center gap-3 min-w-0 text-left">
                <span className={isSel ? 'text-white' : isDir ? 'text-[#3bb5ff]' : 'text-gray-500'}>{isSel && !isDir ? Ico.check : isDir ? Ico.folder : Ico.file}</span>
                <div className="flex-1 flex flex-col items-start min-w-0">
                  <span className="text-sm font-medium truncate w-full">{isBack ? 'Parent Directory' : item.name}</span>
                  {isDir && !isBack && <span className="text-[9px] text-[#3bb5ff]/50 uppercase tracking-widest">Tap to open</span>}
                </div>
              </button>
              {isDir && !isBack && (
                <button onClick={() => fetchDirectory(item.path)} className="p-2 text-gray-600 hover:text-[#3bb5ff] transition-colors flex-shrink-0">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4"><path d="M9 5l7 7-7 7" /></svg>
                </button>
              )}
            </div>
          );
        })}
      </div>
      <div className="p-4 bg-[#0a1628] border-t border-[#1a3a5c] flex gap-3">
        {multiSelect ? (
          <button onClick={() => onSelect(selectedPaths)} disabled={selectedPaths.length === 0} className="flex-1 py-4 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-2xl font-bold btn-touch shadow-lg shadow-[#3bb5ff]/20 disabled:opacity-40 uppercase tracking-widest text-xs">Confirm ({selectedPaths.length})</button>
        ) : !showFiles ? (
          <button onClick={() => onSelect(currentPath)} className="flex-1 py-4 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-2xl font-bold btn-touch shadow-lg shadow-[#3bb5ff]/20 uppercase tracking-widest text-xs">Select This Folder</button>
        ) : null}
        <button onClick={onCancel} className="px-8 py-4 bg-[#0f1f3a] text-white rounded-2xl border border-[#1a3a5c] btn-touch font-bold uppercase tracking-widest text-xs">Cancel</button>
      </div>
    </div>
  );
}

// ---------- Archive Folder Picker ----------
function ArchiveFolderPicker({ selectedDb, onSelect, onCancel, initialPath = '.' }) {
  const [path, setPath] = useState(initialPath);
  const [folders, setFolders] = useState([]);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    if (selectedDb) {
      setLoading(true);
      fetch(`/api/listfiles?db=${encodeURIComponent(selectedDb)}&path=${encodeURIComponent(path)}&depth=1`)
        .then(r => r.json())
        .then(d => {
          let f = [];
          if (path === '.' || path === '') {
            f = Object.values(d.results || {}).filter(i => i.type === 'folder').map(i => ({ name: i.name, path: i.name }));
          } else {
            const k = Object.keys(d.results || {});
            if (k.length) {
              const t = d.results[k[0]];
              if (t.contents) f = Object.values(t.contents).filter(i => i.type === 'folder').map(i => ({ name: i.name, path: `${path}/${i.name}` }));
            }
          }
          setFolders(f);
          setLoading(false);
        })
        .catch(() => setLoading(false));
    }
  }, [selectedDb, path]);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <button onClick={() => setPath('.')} className="btn-touch text-[#3bb5ff] p-1">{Ico.home}</button>
        {path !== '.' && <button onClick={() => { const p = path.split('/'); p.pop(); setPath(p.length ? p.join('/') : '.'); }} className="btn-touch text-gray-400 p-1">{Ico.back}</button>}
        <span className="text-xs text-gray-300 font-mono truncate flex-1">{path}</span>
      </div>
      <div className="max-h-48 overflow-y-auto space-y-1">
        {loading ? <p className="text-xs text-gray-500">Loading...</p> : folders.length === 0 ? <p className="text-xs text-gray-500 italic">No subfolders</p> : folders.map(f => (
          <button key={f.path} onClick={() => setPath(f.path)} className="w-full flex items-center gap-2 px-3 py-2 bg-[#0f1f3a] rounded-lg text-sm text-[#3bb5ff] btn-touch">{Ico.folderOpen}{f.name}</button>
        ))}
      </div>
      <button onClick={() => onSelect(path)} className="w-full py-3 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-xl font-bold btn-touch">Select "{path}"</button>
      {onCancel && <button onClick={onCancel} className="w-full py-3 bg-[#0f1f3a] text-gray-300 rounded-xl border border-[#1a3a5c] btn-touch">Cancel</button>}
    </div>
  );
}

// ---------- Type Casting Helper ----------
const castConfigTypes = (base, override) => {
  const result = JSON.parse(JSON.stringify(override));
  const traverse = (b, o) => {
    for (const key in o) {
      if (b && key in b) {
        if (typeof b[key] === 'object' && b[key] !== null && typeof o[key] === 'object' && o[key] !== null) {
          traverse(b[key], o[key]);
        } else if (typeof b[key] === 'number') {
          o[key] = parseFloat(o[key]);
          if (isNaN(o[key])) o[key] = 0;
        } else if (typeof b[key] === 'boolean') {
          o[key] = Boolean(o[key]);
        }
      }
    }
  };
  traverse(base, result);
  return result;
};

function SettingsTabContent({ config, fetchConfig, showToast }) {
  const [localConfig, setLocalConfig] = useState(null);
  const [downloadFolder, setDownloadFolder] = useState(localStorage.getItem('VAULT_OPUS_download_folder') || '/storage/emulated/0/Download');
  const [showPicker, setShowPicker] = useState(false);

  useEffect(() => {
    if (config) {
      const mapToStrings = (obj) => {
        const result = {};
        for (const k in obj) {
          if (obj[k] !== null && typeof obj[k] === 'object' && !Array.isArray(obj[k])) {
            result[k] = mapToStrings(obj[k]);
          } else {
            result[k] = obj[k] === null || obj[k] === undefined ? '' : String(obj[k]);
          }
        }
        return result;
      };
      setLocalConfig(mapToStrings(config));
    }
  }, [config]);

  const saveSettings = async () => {
    if (localConfig && config) {
      const castedConfig = castConfigTypes(config, localConfig);
      try {
        const res = await fetch('/api/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(castedConfig)
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || 'Failed to save config');
        }
        localStorage.setItem('VAULT_OPUS_download_folder', downloadFolder);
        showToast('Settings saved', 'success');
        await fetchConfig();
      } catch (e) {
        showToast(e.message, 'error');
      }
    }
  };

  if (showPicker) {
    return (
      <RemoteFolderPicker
        initialPath={downloadFolder}
        onSelect={p => {
          setDownloadFolder(p);
          setShowPicker(false);
        }}
        onCancel={() => setShowPicker(false)}
      />
    );
  }

  if (!localConfig) return (
    <div className="flex flex-col items-center justify-center h-full space-y-4">
      <div className="animate-spin text-[#3bb5ff]">{Ico.version}</div>
      <p className="text-gray-500">Loading configuration...</p>
      <button onClick={fetchConfig} className="px-6 py-2 bg-[#0f1f3a] border border-[#1a3a5c] text-[#3bb5ff] rounded-xl text-sm font-bold btn-touch">Retry Connection</button>
    </div>
  );

  const handleFieldChange = (path, value) => {
    setLocalConfig(prev => {
      const upd = JSON.parse(JSON.stringify(prev));
      let obj = upd;
      for (let i = 0; i < path.length - 1; i++) obj = obj[path[i]];
      obj[path[path.length - 1]] = value;
      return upd;
    });
  };

  const renderField = (key, value, path) => {
    const fieldPath = [...path, key];
    const getOriginalVal = (p) => {
      let current = config;
      for (const step of p) {
        if (current && typeof current === 'object') current = current[step];
        else return undefined;
      }
      return current;
    };
    const originalVal = getOriginalVal(fieldPath);
    const isBoolean = typeof originalVal === 'boolean';

    if (isBoolean) {
      const isChecked = value === 'true' || value === true;
      return (
        <label key={key} className="flex items-center justify-between p-3 bg-[#060d1a] border border-[#1a3a5c] rounded-xl active:bg-[#1a3a5c]/50 transition-all">
          <span className="text-sm text-gray-300">{key.replace(/_/g, ' ')}</span>
          <div className="relative">
            <input type="checkbox" checked={isChecked} onChange={e => handleFieldChange(fieldPath, e.target.checked)} className="sr-only peer" />
            <div className="w-11 h-6 bg-[#1a3a5c] rounded-full peer peer-checked:bg-[#3bb5ff] transition-colors" />
            <div className="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full shadow-md transition-transform peer-checked:translate-x-5" />
          </div>
        </label>
      );
    }

    return (
      <div key={key} className="space-y-1">
        <label className="text-[10px] text-[#3bb5ff]/70 uppercase tracking-wider font-bold ml-1">{key.replace(/_/g, ' ')}</label>
        <input type="text" value={value ?? ''} onChange={e => handleFieldChange(fieldPath, e.target.value)} className="w-full bg-[#060d1a] border border-[#1a3a5c] focus:border-[#3bb5ff] rounded-xl px-3 py-3 text-sm text-gray-200 outline-none transition-colors" placeholder={`Enter ${key.replace(/_/g, ' ')}...`} />
      </div>
    );
  };

  const renderSection = (title, data, path = []) => {
    if (data === null || data === undefined || typeof data !== 'object' || Array.isArray(data)) {
      return renderField(title, data, path);
    }
    return (
      <div key={title} className="bg-[#0a1628] p-4 rounded-2xl border border-[#1a3a5c] space-y-4">
        <h3 className="text-xs font-bold text-[#3bb5ff] uppercase tracking-wider">{title.replace(/_/g, ' ')}</h3>
        {Object.entries(data).map(([k, v]) => {
          if (v !== null && v !== undefined && typeof v === 'object' && !Array.isArray(v)) {
            return renderSection(k, v, [...path, k]);
          }
          return renderField(k, v, [...path]);
        })}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full overflow-y-auto p-4 pb-32">
      <div className="space-y-4">
        <div className="bg-[#0a1628] p-4 rounded-2xl border border-[#1a3a5c] space-y-3">
          <h3 className="text-xs font-bold text-[#3bb5ff] uppercase tracking-wider">Interface</h3>
          <div className="space-y-1">
            <label className="text-[10px] text-[#3bb5ff]/70 uppercase tracking-wider font-bold ml-1">Download Destination</label>
            <div className="flex gap-2">
              <input type="text" value={downloadFolder} onChange={e => setDownloadFolder(e.target.value)} className="flex-1 bg-[#060d1a] border border-[#1a3a5c] focus:border-[#3bb5ff] rounded-xl px-3 py-3 text-sm text-gray-200 outline-none transition-colors" />
              <button onClick={() => setShowPicker(true)} className="px-4 py-3 bg-[#0f1f3a] border border-[#1a3a5c] rounded-xl text-[#3bb5ff] btn-touch">Choose another</button>
            </div>
          </div>
        </div>
        {Object.entries(localConfig)
          .filter(([_, d]) => d !== null && typeof d === 'object' && !Array.isArray(d))
          .map(([section, data]) => renderSection(section, data, [section]))}
      </div>
      <div className="fixed bottom-24 left-4 right-4"><button onClick={saveSettings} className="w-full py-4 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-2xl font-bold shadow-xl">Commit Settings</button></div>
    </div>
  );
}

// ---------- Main App Component ----------
export default function App() {
  // State
  const [tab, setTab] = useState('explorer');
  const [dbs, setDbs] = useState([]);
  const [selectedDb, setSelectedDb] = useState(localStorage.getItem('mob_selectedDb') || '');
  const [tree, setTree] = useState(null);
  const [currentPath, setCurrentPath] = useState('.');
  const [currentVersion, setCurrentVersion] = useState(null);
  const [selectedItems, setSelectedItems] = useState([]);
  const [ws, setWs] = useState(null);
  const [terminalOutput, setTerminalOutput] = useState('');
  const [queue, setQueue] = useState([]);
  const [config, setConfig] = useState(null);
  const [promptQueue, setPromptQueue] = useState([]);
  const [bottomSheet, setBottomSheet] = useState(null);
  const [modal, setModal] = useState(null);
  const [showCreateVolume, setShowCreateVolume] = useState(false);
  const [showSetupModal, setShowSetupModal] = useState(false);
  const [setupData, setSetupData] = useState({ token: '', channel_id: '', db_name: '' });
  const [setupStatus, setSetupStatus] = useState({ has_valid_token: false, has_valid_channel: false, has_valid_volume: false });
  const [newDbName, setNewDbName] = useState('');
  const [externalVolumes, setExternalVolumes] = useState(() => { const saved = localStorage.getItem('mob_externalVolumes'); return saved ? JSON.parse(saved) : []; });
  const [recentVolumes, setRecentVolumes] = useState(() => { const saved = localStorage.getItem('mob_recentVolumes'); return saved ? JSON.parse(saved) : []; });
  const [toast, setToast] = useState(null);
  const [passwordModal, setPasswordModal] = useState({ open: false, path: '', password: '', error: '' });
  const [showSharePasswordModal, setShowSharePasswordModal] = useState(false);
  const [dbToShare, setDbToShare] = useState('');
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [volumeError, setVolumeError] = useState(null);
  const [isRetrying, setIsRetrying] = useState(false);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const retryCountRef = useRef(0);
  const maxRetries = 10;
  const retryInterval = 2000;

  const showToast = (msg, type = 'info') => setToast({ message: msg, type, key: Date.now() });

  // Android‑friendly WebSocket with fallback to 127.0.0.1:8000

  const doImport = async (path, password) => {
    if (passwordModal.error) {
      setPasswordModal(prev => ({ ...prev, error: '' }));
      await new Promise(resolve => setTimeout(resolve, 150));
    }
    try {
      const body = { vov_path: path };
      if (password) body.password = password;
      const res = await fetch('/api/dbs/import', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Import failed');
      }
      showToast('Imported successfully', 'success');
      setPasswordModal({ open: false, path: '', password: '', error: '' });
      setModal(null);
      fetchDbs();
    } catch (error) {
      if (password !== null && error.message && (error.message.toLowerCase().includes('password') || error.message.toLowerCase().includes('incorrect') || error.message.toLowerCase().includes('mac'))) {
        setPasswordModal(prev => ({ ...prev, error: 'Incorrect password. Try again.', password: '' }));
      } else {
        setPasswordModal({ open: false, path: '', password: '', error: '' });
        showToast('Import failed: ' + error.message, 'error');
      }
    }
  };
  

  const executeShare = async (password = null) => {
    setShowSharePasswordModal(false);
    try {
      const body = { db_name: dbToShare };
      if (password) body.password = password;
      const res = await fetch('/api/dbs/share', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to package volume');
      }
      const data = await res.json();
      const lockIcon = password ? '🔒 ' : '';
      setModal({
        title: password ? '🔒 Volume Packaged' : 'Volume Packaged',
        content: (
          <div className="space-y-4">
            <div className="p-4 bg-green-900/20 border border-green-500/30 rounded-xl">
              <p className="text-sm text-green-400 font-bold">{lockIcon}📦 Packaged Successfully!</p>
              <p className="text-xs text-gray-300 mt-2">
                Volume <span className="text-white font-mono">{dbToShare}</span> packaged successfully!<br />
                Package: <span className="text-white font-mono">{data.filename}</span><br />
                Stored in <span className="text-white font-mono">src/SHARABLES</span> folder.
                {password && <span className="block mt-1 text-amber-300">This package is password-protected.</span>}
              </p>
            </div>
            <button onClick={() => { fetch('/api/dbs/open_sharables', { method: 'POST' }); setModal(null); }} className="w-full py-3 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-xl font-bold flex items-center justify-center gap-2 btn-touch">{Ico.share} Open src/SHARABLES Folder</button>
            <button onClick={() => setModal(null)} className="w-full py-3 bg-[#0f1f3a] text-gray-300 rounded-xl text-sm btn-touch">Close</button>
          </div>
        )
      });
    } catch (e) {
      showToast(e.message, 'error');
    } finally {
      setDbToShare('');
    }
  };

const connectWS = () => {
    if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    let host = window.location.host;
    // Android‑friendly fallback: if we're on dev server (port 5173) or no port (file:/// or localhost), use the backend directly
    if (window.location.port === '5173' || !host.includes(':')) host = '127.0.0.1:8000';
    setConnectionStatus('connecting');
    const socket = new WebSocket(`${proto}//${host}/ws/cli`);

    socket.onopen = () => {
      setWs(socket);
      setConnectionStatus('connected');
      reconnectAttemptsRef.current = 0;
      setTerminalOutput(p => p + '\n[Connected to VAULT OPUS CLI]\n');
      // Fetch initial data once connected
      fetchDbs(); fetchConfig(); fetchRecentVolumes(); fetchSetupStatus();

      // Fix: If a volume is pre-selected, try to load its files once connected
      if (localStorage.getItem('mob_selectedDb')) {
        setTimeout(() => fetchFiles('.', null), 500);
      }
    };

        socket.onmessage = e => {
          const msg = JSON.parse(e.data);
          const tid = msg.task_id;
          const line = msg.data || '';
          if (msg.type === 'stdout' || msg.type === 'stderr') {
            setTerminalOutput(p => p + line);

            // Detect type-mismatch fallback sentinel and show a modal dialog
            const dialogMatch = line.match(/\[DIALOG:TYPE_MISMATCH\]([^|]+)\|([^|]+)\|(.+)/);
            if (dialogMatch) {
              const [, localName, targetName, fallbackNickname] = dialogMatch;
              setModal({
                title: '⚠️ Type Mismatch — Converted to New Upload',
                content: (
                  <div className="space-y-4">
                    <p className="text-sm text-amber-300 leading-relaxed">
                      The upload for <span className="font-bold text-white">"{localName}"</span> could not be saved as a new version of <span className="font-bold text-white">"{targetName}"</span> because one is a file and the other is a folder.
                    </p>
                    <p className="text-sm text-gray-400 leading-relaxed">
                      It has been automatically re-submitted as a <span className="font-bold text-white">NEW UPLOAD</span> with the auto-generated name:
                    </p>
                    <div className="p-3 bg-[#060d1a] border border-amber-500/30 rounded-xl font-mono text-xs text-amber-300 break-all">
                      {fallbackNickname}
                    </div>
                  </div>
                ),
                onClose: () => setModal(null)
              });
            }

            const progressMatch = line.match(/Overall.*Progress.*\((\d+)%\)/i) || line.match(/Overall:.*\((\d+)%\)/i);
            setQueue(q => q.map(i => {
              if (i.id !== tid) return i;
              if (i.status === 'completed' || i.status === 'failed') return i;
              if (line.includes('[OP_SUCCESS]')) return { ...i, status: 'completed', progress: 100 };
              if (line.includes('[OP_FAILURE]')) return { ...i, status: 'failed' };
              if (progressMatch) return { ...i, status: 'running', progress: parseInt(progressMatch[1], 10) };
              return i;
            }));
          } else if (msg.type === 'status') {
            setQueue(q => q.map(i => i.id === tid ? { ...i, status: line.includes('Queued') ? 'queued' : 'running' } : i));
          } else if (msg.type === 'prompt') {
            setPromptQueue(prev => [...prev, { text: msg.prompt, isPassword: msg.is_password, taskId: tid }]);
          } else if (msg.type === 'exit') {
            setTerminalOutput(p => p + `\n[Process ${tid} exited with code: ${msg.code}]\n`);
            setQueue(q => q.map(i => i.id === tid ? { ...i, status: msg.code === 0 ? 'completed' : 'failed', progress: msg.code === 0 ? 100 : i.progress } : i));
            if (msg.code === 0) { showToast('Operation completed', 'success'); setTimeout(() => { fetchFiles(currentPath); }, 300); }
            else showToast('Operation failed', 'error');
          }
        };

    socket.onclose = () => {
      setWs(null);
      setConnectionStatus('disconnected');
      setTerminalOutput(p => p + '\n[Disconnected from VAULT OPUS CLI]\n');
      if (reconnectAttemptsRef.current < 10) {
        reconnectAttemptsRef.current++;
        reconnectTimeoutRef.current = setTimeout(connectWS, 2000);
      }
    };

    socket.onerror = () => socket.close();
  };

  useEffect(() => {
    connectWS();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (ws) ws.close();
    };
  }, []);

  const sendWS = (action, args, task_id) => { if (ws?.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ action, args, task_id })); };
  const addQueue = (name, type) => { const id = `${type}-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`; setQueue(q => [...q, { id, name, status: 'queued', progress: 0 }]); return id; };
  const runCmd = (args, name, type) => { const id = addQueue(name, type); sendWS('run', args, id); };

  // Data fetching
  const fetchDbs = async () => {
    try {
      const r = await fetch('/api/dbs');
      const data = await r.json();
      const availableDbs = data.dbs || [];
      const all = [...availableDbs];
      externalVolumes.forEach(ext => { if (!all.includes(ext)) all.push(ext); });
      setDbs(all);
    } catch (e) { showToast('Failed to fetch volumes', 'error'); }
  };
  const fetchConfig = async () => {
    try {
      const r = await fetch('/api/config');
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      setConfig(data);
    } catch (e) {
      console.error('Failed to fetch config:', e);
    }
  };
  const fetchRecentVolumes = async () => {
    try {
      const r = await fetch('/api/recent_volumes');
      const data = await r.json();
      const recent = data.recent || [];
      setRecentVolumes(recent);
      localStorage.setItem('mob_recentVolumes', JSON.stringify(recent));
    } catch (e) { console.error('Failed to fetch recent volumes:', e); }
  };
  const updateRecentVolumes = (updater) => {
    setRecentVolumes(prev => {
      const nextRecent = typeof updater === 'function' ? updater(prev) : updater;
      localStorage.setItem('mob_recentVolumes', JSON.stringify(nextRecent));
      fetch('/api/recent_volumes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ recent: nextRecent }) }).catch(err => console.error('Failed to save recent volumes:', err));
      return nextRecent;
    });
  };
  const fetchFiles = async (path, version = currentVersion) => {
    if (!selectedDb) return;
    setVolumeError(null);
    try {
      // Normalize db name: preserve path if absolute, ensure .db extension
      const isAbsolute = selectedDb.startsWith('/') || selectedDb.includes(':\\');
      const dbParam = isAbsolute
        ? (selectedDb.endsWith('.db') ? selectedDb : `${selectedDb}.db`)
        : selectedDb.split(/[\/\\]/).pop().endsWith('.db') ? selectedDb.split(/[\/\\]/).pop() : `${selectedDb.split(/[\/\\]/).pop()}.db`;

      let url = `/api/listfiles?db=${encodeURIComponent(dbParam)}&path=${encodeURIComponent(path)}`;
      if (version) url += `&version=${encodeURIComponent(version)}`;
      const r = await fetch(url);
      const data = await r.json();

      if (!r.ok || data.error) {
        // If it's a "not found" error, it's likely a real issue, not a race condition
        if (path !== '.' && (data.error?.toLowerCase().includes('not found') || !r.ok)) {
          setCurrentPath('.');
          fetchFiles('.');
          return;
        }

        // Handle possible race condition on root path
        if (path === '.') {
          try {
            const checkR = await fetch(`/api/dbs`);
            const checkData = await checkR.json();
            const availableDbs = checkData.dbs || [];

            const normalizedSelected = dbParam.split(/[\/\\]/).pop();
            const normalizedAvailable = availableDbs.map(db => db.split(/[\/\\]/).pop());
            const isExternal = externalVolumes.some(ext => {
              const extBase = ext.split(/[\/\\]/).pop();
              return ext === dbParam || extBase === normalizedSelected;
            });

            if (!normalizedAvailable.includes(normalizedSelected) && !isExternal) {
              setVolumeError("This volume doesn't exist");
              setTree(null);
              retryCountRef.current = 0; // Don't retry if it definitely doesn't exist
              return;
            }
          } catch (_) { }

          // If we reach here, it might just be the server starting up
          if (retryCountRef.current < maxRetries) {
            retryCountRef.current++;
            setIsRetrying(true);
            setTimeout(() => fetchFiles(path, version), retryInterval);
            return;
          }
        }

        setVolumeError(data.error || "Error accessing volume");
        setTree(null);
        setIsRetrying(false);
        retryCountRef.current = 0;
        return;
      }
      setTree(data);
      setIsRetrying(false);
      retryCountRef.current = 0;
    } catch (e) {
      if (retryCountRef.current < maxRetries) {
        retryCountRef.current++;
        setIsRetrying(true);
        setTimeout(() => fetchFiles(path, version), retryInterval);
      } else {
        setVolumeError("Could not connect to volume");
        setTree(null);
        setIsRetrying(false);
        retryCountRef.current = 0;
      }
    }
  };
  const fetchSetupStatus = async () => {
    try {
      const r = await fetch('/api/setup_status');
      const data = await r.json();
      setSetupStatus({ has_valid_token: data.has_valid_token, has_valid_channel: data.has_valid_channel, has_valid_volume: data.has_valid_volume });
      if (data.setup_complete === 0) setShowSetupModal(true);
    } catch (e) { }
  };

  useEffect(() => { fetchDbs(); fetchConfig(); fetchRecentVolumes(); fetchSetupStatus(); }, []);
  useEffect(() => {
    if (selectedDb) {
      // Normalize: preserve path if absolute, ensure .db extension
      const isAbsolute = selectedDb.startsWith('/') || selectedDb.includes(':\\');
      const dbWithExt = isAbsolute
        ? (selectedDb.endsWith('.db') ? selectedDb : `${selectedDb}.db`)
        : (selectedDb.split(/[\/\\]/).pop().endsWith('.db') ? selectedDb.split(/[\/\\]/).pop() : `${selectedDb.split(/[\/\\]/).pop()}.db`);

      if (dbWithExt !== selectedDb) {
        setSelectedDb(dbWithExt);
        return;
      }

      localStorage.setItem('mob_selectedDb', dbWithExt);
      updateRecentVolumes(prev => [dbWithExt, ...prev.filter(db => db !== dbWithExt)].slice(0, 10));
      setCurrentVersion(null);
      setCurrentPath('.');
      const load = async () => {
        await fetchDbs();
        fetchFiles('.', null);
      };
      load();
    }
  }, [selectedDb]);

  const handleNavigate = (path) => { setCurrentPath(path); setSelectedItems([]); fetchFiles(path, currentVersion); };
  const handleRefresh = () => { if (selectedDb) fetchFiles(currentPath, currentVersion); };

  // Build items list from tree
  let items = [];
  if (tree?.results) {
    const keys = Object.keys(tree.results);
    if (currentPath !== '.' && keys.length === 1) {
      const single = tree.results[keys[0]];
      if (single.type === 'folder' && single.contents) {
        items = Object.values(single.contents).map(i => ({ ...i, displayName: i.name || i.db_name || 'Unknown', type: i.type || (i.itemid?.startsWith('d') ? 'folder' : 'file') }));
      } else {
        items = keys.map(k => ({ ...tree.results[k], itemid: k, displayName: tree.results[k].name || tree.results[k].db_name || 'Unknown', type: tree.results[k].type || (tree.results[k].itemid?.startsWith('d') ? 'folder' : 'file') }));
      }
    } else {
      items = keys.map(k => ({ ...tree.results[k], itemid: k, displayName: tree.results[k].name || tree.results[k].db_name || 'Unknown', type: tree.results[k].type || (tree.results[k].itemid?.startsWith('d') ? 'folder' : 'file') }));
    }
  }

  // Selection helpers
  const toggleSelect = (item) => {
    setSelectedItems(prev => prev.find(i => i.itemid === item.itemid) ? prev.filter(i => i.itemid !== item.itemid) : [...prev, item]);
  };
  const clearSelection = () => setSelectedItems([]);

  // ---------- Modal Components (Mirroring Desktop) ----------
  const DownloadModalContent = ({ onConfirm, onCancel }) => {
    const [strictnessMode, setStrictnessMode] = useState('NA');
    return (
      <div className="space-y-4">
        <p className="text-sm text-gray-400">Download {selectedItems.length} item(s)</p>
        <div>
          <label className="text-xs text-gray-500 uppercase mb-1 block">Strictness Mode</label>
          <div className="grid grid-cols-1 gap-2">
            {[
              { value: 'NA', label: 'NOT ATOMIC (DEFAULT)', desc: 'Continue on failure' },
              { value: 'SA', label: 'SOFT ATOMIC', desc: 'Stop immediately, ask before cleanup' },
              { value: 'HA', label: 'HARD ATOMIC', desc: 'Stop immediately, auto‑cleanup' }
            ].map(m => (
              <button key={m.value} onClick={() => setStrictnessMode(m.value)} className={`px-4 py-3 rounded-xl border text-left transition-all ${strictnessMode === m.value ? 'bg-[#1a3a5c]/40 border-[#3bb5ff] text-white shadow-[0_0_15px_rgba(59,181,255,0.2)]' : 'bg-[#0d1b2e] border-[#1a3a5c] text-gray-400 hover:border-[#3bb5ff]/50'}`}>
                <div className="font-medium">{m.label}</div>
                <div className="text-xs opacity-60">{m.desc}</div>
              </button>
            ))}
          </div>
        </div>
        <div className="flex justify-end gap-3 pt-4">
          <button onClick={onCancel} className="px-4 py-2 text-sm text-gray-400 hover:text-white">Cancel</button>
          <button onClick={() => onConfirm({ strictnessMode })} className="px-6 py-2 rounded-lg text-sm font-bold bg-[#3bb5ff] hover:bg-[#2e9ee6] text-[#060d1a] shadow-[0_0_20px_rgba(59,181,255,0.3)]">Start Download</button>
        </div>
      </div>
    );
  };

  const FullNameModalContent = ({ item, onClose }) => {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <label className="text-[10px] text-[#3bb5ff] font-bold uppercase tracking-widest opacity-70">
            {item.is_nicknamed ? "Nickname (Display Name)" : "Original Base Filename (Display Name)"}
          </label>
          <div className="p-4 bg-[#060d1a] border border-[#1a3a5c] rounded-xl text-[#3bb5ff] font-mono text-sm break-all max-h-32 overflow-y-auto custom-scrollbar">
            {item.is_nicknamed
              ? (item.db_name || item.base_filename || item.name || item.displayName || "Unknown Nickname")
              : (item.original_name || item.original_base_filename || item.db_name || item.base_filename || item.name || item.displayName || "Unknown Name")}
          </div>
        </div>
        {item.is_nicknamed && (
          <div className="space-y-2">
            <label className="text-[10px] text-[#3bb5ff] font-bold uppercase tracking-widest opacity-70">Original Base Filename</label>
            <div className="p-4 bg-[#060d1a] border border-[#1a3a5c] rounded-xl text-gray-400 font-mono text-sm max-h-40 overflow-y-auto custom-scrollbar break-all shadow-inner">
              {item.original_name || item.original_base_filename || item.db_name || item.base_filename || item.name || "N/A"}
            </div>
          </div>
        )}
        <div className="space-y-2">
          <label className="text-[10px] text-[#3bb5ff] font-bold uppercase tracking-widest opacity-70">Item ID</label>
          <div className="p-4 bg-[#060d1a] border border-[#1a3a5c] rounded-xl text-white font-mono text-sm break-all">{item.itemid}</div>
        </div>
        <button onClick={onClose} className="mt-4 w-full py-3 bg-[#0f1f3a] hover:bg-[#1a3a5c] text-white rounded-xl font-medium transition-all duration-150 active:scale-95 border border-[#1a3a5c]">Close Dialog</button>
      </div>
    );
  };

  const DeleteModalContent = ({ onConfirm, onCancel, singleItem }) => {
    const [deleteType, setDeleteType] = useState('soft');
    const [scope, setScope] = useState(singleItem ? 'all' : 'all');
    const [version, setVersion] = useState('');
    const [startVersion, setStartVersion] = useState('');
    const [endVersion, setEndVersion] = useState('');
    const [availableVersions, setAvailableVersions] = useState([]);
    const [loadingVersions, setLoadingVersions] = useState(false);

    useEffect(() => {
      if (singleItem && selectedDb) {
        setLoadingVersions(true);
        const itemPath = currentPath === '.' ? singleItem.displayName : `${currentPath}/${singleItem.displayName}`;
        fetch(`/api/listfiles?db=${encodeURIComponent(selectedDb)}&path=${encodeURIComponent(itemPath)}`)
          .then(r => r.json())
          .then(pathData => {
            let itemid = null;
            if (pathData.results) { const keys = Object.keys(pathData.results); if (keys.length) itemid = keys[0]; }
            if (!itemid) throw new Error('No itemid');
            return fetch(`/api/listfiles?db=${encodeURIComponent(selectedDb)}&itemid=${encodeURIComponent(itemid)}`);
          })
          .then(r => r.json())
          .then(vd => {
            const versionSet = new Set();
            const vers = [];
            if (vd.results) {
              Object.values(vd.results).forEach(item => { if (item.version && !versionSet.has(item.version)) { versionSet.add(item.version); vers.push(item.version); } });
            }
            vers.sort((a, b) => b.localeCompare(a, undefined, { numeric: true }));
            setAvailableVersions(vers);
            if (vers.length) setVersion(vers[0]);
          })
          .catch(console.error)
          .finally(() => setLoadingVersions(false));
      }
    }, [singleItem]);

    const handleConfirm = () => {
      if (scope === 'specific' && !version) { showToast('Select a version', 'error'); return; }
      if (scope === 'range' && (!startVersion || !endVersion)) { showToast('Select version range', 'error'); return; }
      onConfirm({ type: deleteType, scope, version, startVersion, endVersion });
    };

    return (
      <div className="space-y-4">
        <p className="text-sm text-gray-400">Delete {singleItem ? `"${singleItem.displayName}"` : `${selectedItems.length} items`}</p>
        <div>
          <label className="text-xs text-gray-500 uppercase mb-1 block">Delete Type</label>
          <div className="flex gap-2">
            <button onClick={() => setDeleteType('soft')} className={`flex-1 py-3 rounded-xl text-sm border transition-all ${deleteType === 'soft' ? 'bg-green-500/10 border-green-500/50 text-green-400' : 'bg-[#0d1b2e] border-[#1a3a5c] text-gray-400'}`}>SOFT DELETE</button>
            <button onClick={() => setDeleteType('hard')} className={`flex-1 py-3 rounded-xl text-sm border transition-all ${deleteType === 'hard' ? 'bg-red-500/10 border-red-500/50 text-red-400' : 'bg-[#0d1b2e] border-[#1a3a5c] text-gray-400'}`}>HARD DELETE</button>
          </div>
        </div>
        {singleItem && (
          <div>
            <label className="text-xs text-gray-500 uppercase mb-1 block">Version Scope</label>
            <div className="grid grid-cols-1 gap-2">
              <button onClick={() => setScope('all')} className={`px-4 py-3 rounded-xl border text-left ${scope === 'all' ? 'bg-[#1a3a5c]/40 border-[#3bb5ff]' : 'bg-[#0d1b2e] border-[#1a3a5c]'} text-gray-300`}>All Versions</button>
              <button onClick={() => setScope('specific')} className={`px-4 py-3 rounded-xl border text-left ${scope === 'specific' ? 'bg-[#1a3a5c]/40 border-[#3bb5ff]' : 'bg-[#0d1b2e] border-[#1a3a5c]'} text-gray-300`}>Specific Version</button>
              {scope === 'specific' && (
                <div className="mt-2">
                  {loadingVersions ? <div className="text-xs text-gray-500 animate-pulse">Loading versions...</div> : (
                    <select value={version} onChange={e => setVersion(e.target.value)} className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-lg px-3 py-2 text-sm text-gray-200">
                      {availableVersions.map(v => <option key={v} value={v}>{v}</option>)}
                    </select>
                  )}
                </div>
              )}
              <button onClick={() => setScope('range')} className={`px-4 py-3 rounded-xl border text-left ${scope === 'range' ? 'bg-[#1a3a5c]/40 border-[#3bb5ff]' : 'bg-[#0d1b2e] border-[#1a3a5c]'} text-gray-300`}>Version Range</button>
              {scope === 'range' && (
                <div className="flex gap-2 mt-2">
                  <select value={startVersion} onChange={e => setStartVersion(e.target.value)} className="flex-1 bg-[#060d1a] border border-[#1a3a5c] rounded-lg px-3 py-2 text-sm">
                    <option value="">Start</option>
                    {availableVersions.map(v => <option key={v} value={v}>{v}</option>)}
                  </select>
                  <select value={endVersion} onChange={e => setEndVersion(e.target.value)} className="flex-1 bg-[#060d1a] border border-[#1a3a5c] rounded-lg px-3 py-2 text-sm">
                    <option value="">End</option>
                    {availableVersions.map(v => <option key={v} value={v}>{v}</option>)}
                  </select>
                </div>
              )}
            </div>
          </div>
        )}
        <div className="flex justify-end gap-3 pt-4 border-t border-[#1a3a5c]">
          <button onClick={onCancel} className="px-4 py-2 text-sm text-gray-400 hover:text-white">Cancel</button>
          <button onClick={handleConfirm} className={`px-6 py-2 rounded-lg text-sm font-bold ${deleteType === 'hard' ? 'bg-red-500 hover:bg-red-600 text-white' : 'bg-[#3bb5ff] hover:bg-[#2e9ee6] text-[#060d1a]'} transition-all`}>Confirm Deletion</button>
        </div>
      </div>
    );
  };

  const DownloadVersionModalContent = ({ itemPath, item, onDownload }) => {
    const [versionInput, setVersionInput] = useState('');
    const [startVersion, setStartVersion] = useState('');
    const [endVersion, setEndVersion] = useState('');
    const [allVersions, setAllVersions] = useState(false);
    const [strictnessMode, setStrictnessMode] = useState('NA');
    const [availableVersions, setAvailableVersions] = useState([]);
    const [loadingVersions, setLoadingVersions] = useState(true);

    useEffect(() => {
      if (!selectedDb) return;
      setLoadingVersions(true);
      fetch(`/api/listfiles?db=${encodeURIComponent(selectedDb)}&path=${encodeURIComponent(itemPath)}`)
        .then(r => r.json())
        .then(pathData => {
          let itemid = null;
          if (pathData.results) { const keys = Object.keys(pathData.results); if (keys.length) itemid = keys[0]; }
          if (!itemid) throw new Error('No itemid');
          return fetch(`/api/listfiles?db=${encodeURIComponent(selectedDb)}&itemid=${encodeURIComponent(itemid)}`);
        })
        .then(r => r.json())
        .then(vd => {
          const vers = [];
          if (vd.results) { Object.values(vd.results).forEach(i => { if (i.version) vers.push(i.version); }); }
          vers.sort((a, b) => b.localeCompare(a, undefined, { numeric: true }));
          setAvailableVersions(vers);
        })
        .catch(console.error)
        .finally(() => setLoadingVersions(false));
    }, [itemPath]);

    const handleDownload = () => {
      const args = ['download', itemPath, '-db', selectedDb, '--download_folder', localStorage.getItem('VAULT_OPUS_download_folder') || '/storage/emulated/0/Download'];
      if (allVersions) args.push('--all_versions', 'yes');
      else if (startVersion && endVersion) args.push('--st_version', startVersion, '--en_version', endVersion);
      else if (versionInput) args.push('--version', versionInput);
      if (strictnessMode !== 'NA') args.push('--strictness_mode', strictnessMode);
      onDownload(args);
    };

    return (
      <div className="space-y-4">
        <div className="p-3 bg-[#3bb5ff]/10 border border-[#3bb5ff]/30 rounded-lg">
          <div className="text-[10px] text-[#3bb5ff] uppercase">Item</div>
          <div className="text-xs text-gray-300 font-mono truncate">{itemPath}</div>
        </div>
        <div>
          <label className="text-xs text-gray-500 uppercase mb-1 block">Specific Version</label>
          {loadingVersions ? <div className="h-9 bg-[#060d1a] border border-[#1a3a5c] rounded animate-pulse" /> : (
            <select value={versionInput} onChange={e => { setVersionInput(e.target.value); setStartVersion(''); setEndVersion(''); setAllVersions(false); }} className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-lg px-3 py-2 text-sm text-gray-200">
              <option value="">Select version...</option>
              {availableVersions.map(v => <option key={v} value={v}>{v}</option>)}
            </select>
          )}
        </div>
        <div>
          <label className="text-xs text-gray-500 uppercase mb-1 block">Version Range</label>
          <div className="flex gap-2">
            <select value={startVersion} onChange={e => { setStartVersion(e.target.value); setVersionInput(''); setAllVersions(false); }} className="flex-1 bg-[#060d1a] border border-[#1a3a5c] rounded-lg px-3 py-2 text-sm">
              <option value="">Start</option>
              {availableVersions.map(v => <option key={v} value={v}>{v}</option>)}
            </select>
            <select value={endVersion} onChange={e => { setEndVersion(e.target.value); setVersionInput(''); setAllVersions(false); }} className="flex-1 bg-[#060d1a] border border-[#1a3a5c] rounded-lg px-3 py-2 text-sm">
              <option value="">End</option>
              {availableVersions.map(v => <option key={v} value={v}>{v}</option>)}
            </select>
          </div>
        </div>
        <label className="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" checked={allVersions} onChange={e => { setAllVersions(e.target.checked); if (e.target.checked) { setVersionInput(''); setStartVersion(''); setEndVersion(''); } }} className="w-4 h-4 accent-[#3bb5ff]" />
          <span className="text-sm text-gray-300">Download All Versions</span>
        </label>
        <div>
          <label className="text-xs text-gray-500 uppercase mb-1 block">Strictness Mode</label>
          <div className="grid grid-cols-1 gap-2">
            {['NA', 'SA', 'HA'].map(s => (
              <button key={s} onClick={() => setStrictnessMode(s)} className={`px-3 py-2 rounded-lg border text-left transition-all ${strictnessMode === s ? 'bg-[#1a3a5c]/40 border-[#3bb5ff] text-white' : 'bg-[#060d1a] border-[#1a3a5c] text-gray-400'}`}>
                {s === 'NA' ? 'NOT ATOMIC (DEFAULT)' : s === 'SA' ? 'SOFT ATOMIC' : 'HARD ATOMIC'}
              </button>
            ))}
          </div>
        </div>
        <div className="flex justify-end gap-3 pt-4">
          <button onClick={() => onDownload(null)} className="px-4 py-2 text-sm text-gray-400 hover:text-white">Cancel</button>
          <button onClick={handleDownload} className="px-6 py-2 rounded-lg text-sm font-bold bg-[#3bb5ff] text-[#060d1a]">Download</button>
        </div>
      </div>
    );
  };

  const SeeVersionsModalContent = ({ itemPath, onClose }) => {
    const [versions, setVersions] = useState([]);
    const [loading, setLoading] = useState(true);
    useEffect(() => {
      fetch(`/api/listfiles?db=${encodeURIComponent(selectedDb)}&path=${encodeURIComponent(itemPath)}`)
        .then(r => r.json())
        .then(d => {
          let itemid = null;
          if (d.results) { const keys = Object.keys(d.results); if (keys.length) itemid = keys[0]; }
          if (!itemid) throw new Error('No itemid');
          return fetch(`/api/listfiles?db=${encodeURIComponent(selectedDb)}&itemid=${encodeURIComponent(itemid)}`);
        })
        .then(r => r.json())
        .then(vd => {
          const vers = [];
          if (vd.results) { Object.values(vd.results).forEach(i => { if (i.version) vers.push(i.version); }); }
          vers.sort((a, b) => b.localeCompare(a, undefined, { numeric: true }));
          setVersions(vers);
        })
        .catch(console.error)
        .finally(() => setLoading(false));
    }, [itemPath]);
    return (
      <div className="space-y-2">
        {loading ? <div className="text-center py-8 text-gray-500">Loading versions...</div> : versions.length === 0 ? <div className="text-center py-8 text-gray-500">No versions found</div> : versions.map(v => (
          <div key={v} className="flex items-center justify-between px-3 py-2 bg-[#0f1f3a] border border-[#1a3a5c] rounded-lg">
            <span className="text-sm text-gray-200">Version {v}</span>
          </div>
        ))}
        <button onClick={onClose} className="w-full py-2 mt-4 text-[#3bb5ff] btn-touch">Close</button>
      </div>
    );
  };

  const NewVersionUploadModalContent = ({ targetItemPath, onUpload }) => {
    const [showFolderPicker, setShowFolderPicker] = useState(false);
    const [uploadPath, setUploadPath] = useState('');
    const [encryption, setEncryption] = useState('automatic');
    const [password, setPassword] = useState('');
    const [randomSeed, setRandomSeed] = useState(false);
    const [zeroKnowledge, setZeroKnowledge] = useState(false);
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
      return Array.from(crypto.getRandomValues(new Uint32Array(24))).map(x => chars[x % chars.length]).join('');
    };

    useEffect(() => {
      if (targetItemPath && selectedDb) {
        setIsLoadingVersions(true);
        fetch(`/api/listfiles?db=${encodeURIComponent(selectedDb)}&path=${encodeURIComponent(targetItemPath)}`)
          .then(r => r.json())
          .then(d => {
            let itemid = null;
            if (d.results) { const keys = Object.keys(d.results); if (keys.length) itemid = keys[0]; }
            if (!itemid) throw new Error('No itemid');
            return fetch(`/api/listfiles?db=${encodeURIComponent(selectedDb)}&itemid=${encodeURIComponent(itemid)}`);
          })
          .then(r => r.json())
          .then(vd => {
            const vers = [];
            if (vd.results) { Object.values(vd.results).forEach(i => { if (i.version) vers.push(i.version); }); }
            vers.sort((a, b) => b.localeCompare(a, undefined, { numeric: true }));
            setAvailableVersions(vers);
            if (vers.length) setSourceVersion(vers[0]);
          })
          .catch(console.error)
          .finally(() => setIsLoadingVersions(false));
      }
    }, [targetItemPath]);

    const handleStartUpload = () => {
      if (!uploadPath) { showToast('Select a path to upload', 'error'); return; }
      if (encryption === 'not_automatic' && !minimize) {
        if (!password && !randomSeed) { showToast('Provide password or select Random', 'error'); return; }
        if (randomSeed) {
          const pass = generateRandomPassword();
          setGeneratedPassword(pass);
          setShowPasswordModal(true);
          return;
        }
      }
      proceedWithUpload(password);
    };
    const proceedWithUpload = (finalPassword) => {
      const enc = minimize && encryption === 'not_automatic' ? 'automatic' : encryption;
      const args = [
        'upload', uploadPath, '-db', selectedDb, '-c', config?.discord?.channel_id || '',
        '--encryption_mode', enc,
        '--target_item_path', targetItemPath, '--upload_mode', 'new_version'
      ];
      if (enc === 'not_automatic' && finalPassword) args.push('--password_seed', finalPassword);
      if (uploadName) args.push('--upload_name', uploadName);
      if (newVersionString) args.push('--new_version_string', newVersionString);
      if (strictnessMode !== 'NA') args.push('--strictness_mode', strictnessMode);
      if (chunkSizeMb) args.push('--chunk_size_mb', chunkSizeMb);
      if (minimize) args.push('--minimize', 'yes');
      if (!nameCheck) args.push('--no_name_check');
      if (additionMode) { args.push('--addition'); if (sourceVersion) args.push('--source_version', sourceVersion); }
      args.push('--save_hash', encryption === 'not_automatic' && zeroKnowledge ? 'False' : 'True');
      runCmd(args, uploadPath.split(/[/\\]/).pop(), 'upload');
      setModal(null);
      showToast('New version queued', 'success');
    };

    if (showPasswordModal) {
      return (
        <div className="space-y-4 text-center">
          <div className="p-4 bg-[#3bb5ff]/10 border border-[#3bb5ff]/30 rounded-xl">
            <p className="text-sm text-[#3bb5ff] font-bold">Save This Password</p>
            <code className="block mt-2 p-2 bg-[#060d1a] rounded text-white font-mono text-xs break-all">{generatedPassword}</code>
            <button onClick={() => { navigator.clipboard?.writeText(generatedPassword); showToast('Copied', 'success'); }} className="mt-2 px-4 py-2 text-xs bg-[#0f1f3a] rounded">Copy</button>
          </div>
          <button onClick={() => proceedWithUpload(generatedPassword)} className="w-full py-3 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-xl font-bold">Confirm & Upload</button>
          <button onClick={() => setShowPasswordModal(false)} className="text-sm text-gray-500">Cancel</button>
        </div>
      );
    }

    if (showFolderPicker) {
      return <RemoteFolderPicker initialPath={uploadPath} showFiles multiSelect singleSelectOnly onSelect={p => { setUploadPath(p[0] || ''); setShowFolderPicker(false); }} onCancel={() => setShowFolderPicker(false)} />;
    }

    return (
      <div className="space-y-4">
        <div className="p-3 bg-[#3bb5ff]/10 border border-[#3bb5ff]/30 rounded-lg">
          <div className="text-[10px] text-[#3bb5ff] uppercase">Target Item</div>
          <div className="text-xs text-gray-300 font-mono truncate">{targetItemPath}</div>
        </div>
        <div className="flex gap-2">
          <input type="text" value={uploadPath} onChange={e => setUploadPath(e.target.value)} placeholder="Local file/folder" className="flex-1 bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm text-gray-200" />
          <button onClick={() => setShowFolderPicker(true)} className="px-4 py-3 bg-[#0f1f3a] border border-[#1a3a5c] rounded-xl text-[#3bb5ff] btn-touch">Browse</button>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-[10px] text-gray-500 uppercase">Encryption</label>
            <select value={encryption} onChange={e => setEncryption(e.target.value)} disabled={minimize} className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm">
              <option value="automatic">Automatic</option>
              <option value="off">Off</option>
              <option value="not_automatic">Password</option>
            </select>
          </div>
          <div>
            <label className="text-[10px] text-gray-500 uppercase">Strictness</label>
            <select value={strictnessMode} onChange={e => setStrictnessMode(e.target.value)} className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm">
              <option value="NA">Not Atomic</option>
              <option value="SA">Soft Atomic</option>
              <option value="HA">Hard Atomic</option>
            </select>
          </div>
        </div>
        {encryption === 'not_automatic' && (
          <div className="flex gap-2">
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} disabled={randomSeed} placeholder="Password seed" className="flex-1 bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm" />
            <button onClick={() => setRandomSeed(!randomSeed)} className={`px-4 py-3 rounded-xl text-xs font-bold border ${randomSeed ? 'bg-[#3bb5ff]/20 border-[#3bb5ff] text-white' : 'bg-[#0f1f3a] border-[#1a3a5c] text-gray-400'}`}>Random</button>
          </div>
        )}
        <div>
          <label className="text-[10px] text-gray-500 uppercase">Upload Strategy</label>
          <div className="flex gap-2 mt-1">
            <button onClick={() => setAdditionMode(false)} className={`flex-1 py-2 rounded-xl text-sm border ${!additionMode ? 'bg-[#3bb5ff]/20 border-[#3bb5ff] text-white' : 'bg-[#060d1a] border-[#1a3a5c] text-gray-400'}`}>Independent</button>
            <button onClick={() => setAdditionMode(true)} className={`flex-1 py-2 rounded-xl text-sm border ${additionMode ? 'bg-[#3bb5ff]/20 border-[#3bb5ff] text-white' : 'bg-[#060d1a] border-[#1a3a5c] text-gray-400'}`}>Addition</button>
          </div>
        </div>
        {additionMode && (
          <div>
            <label className="text-[10px] text-gray-500 uppercase">Source Version</label>
            {isLoadingVersions ? <div className="h-9 bg-[#060d1a] animate-pulse rounded" /> : (
              <select value={sourceVersion} onChange={e => setSourceVersion(e.target.value)} className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm">
                {availableVersions.map(v => <option key={v} value={v}>{v}</option>)}
                {availableVersions.length === 0 && <option value="">Latest (Auto)</option>}
              </select>
            )}
          </div>
        )}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-[10px] text-gray-500 uppercase">Version String</label>
            <input type="text" value={newVersionString} onChange={e => setNewVersionString(e.target.value)} placeholder="e.g. 1.0.0" className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm" />
          </div>
          <div>
            <label className="text-[10px] text-gray-500 uppercase">Chunk Size (MB)</label>
            <input type="number" step="0.1" value={chunkSizeMb} onChange={e => setChunkSizeMb(e.target.value)} placeholder="Auto" className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm" />
          </div>
        </div>
        <div className="flex flex-wrap gap-4">
          <label className="flex items-center gap-2"><input type="checkbox" checked={nameCheck} onChange={e => setNameCheck(e.target.checked)} className="accent-[#3bb5ff]" /><span className="text-xs">Name Check</span></label>
          <label className="flex items-center gap-2"><input type="checkbox" checked={minimize} onChange={e => setMinimize(e.target.checked)} className="accent-[#3bb5ff]" /><span className="text-xs">Minimize</span></label>
          {encryption === 'not_automatic' && <label className="flex items-center gap-2"><input type="checkbox" checked={zeroKnowledge} onChange={e => setZeroKnowledge(e.target.checked)} disabled={minimize} className="accent-[#3bb5ff]" /><span className="text-xs">Zero‑Knowledge</span></label>}
        </div>
        <button onClick={handleStartUpload} className="w-full py-4 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-2xl font-bold btn-touch shadow-lg">Start Upload</button>
      </div>
    );
  };

  const ModifyModalContent = ({ type, item, onConfirm }) => {
    const [destination, setDestination] = useState('.');
    const [newName, setNewName] = useState(item.displayName);
    const [copyMode, setCopyMode] = useState(false);
    const [nameMode, setNameMode] = useState('D');
    const [nameCheck, setNameCheck] = useState(true);
    const [showPicker, setShowPicker] = useState(false);

    if (showPicker && type === 'move') {
      return <ArchiveFolderPicker selectedDb={selectedDb} onSelect={p => { setDestination(p); setShowPicker(false); }} onCancel={() => setShowPicker(false)} initialPath={destination} />;
    }

    const handleSubmit = () => {
      if (type === 'rename' && !newName.trim()) {
        showToast('New name cannot be empty', 'error');
        return;
      }
      if (type === 'move') {
        onConfirm({
          type: 'move',
          src: item.itemid || (currentPath === '.' ? item.displayName : `${currentPath}/${item.displayName}`),
          dst: destination,
          copyMode,
          nameCheck,
          srcIdBased: !!item.itemid,
          dstIdBased: false
        });
      } else {
        onConfirm({
          type: 'rename',
          item: item.itemid || (currentPath === '.' ? item.displayName : `${currentPath}/${item.displayName}`),
          newName,
          nameMode,
          nameCheck,
          idBased: !!item.itemid
        });
      }
    };

    return (
      <div className="space-y-4">
        <div className="bg-[#060d1a] p-3 rounded-lg border border-[#1a3a5c]">
          <p className="text-xs text-gray-500">Source:</p>
          <p className="text-sm text-white truncate">{item.displayName}</p>
        </div>
        {type === 'move' ? (
          <>
            <div>
              <label className="text-xs text-gray-500 uppercase mb-1 block">Destination</label>
              <div className="flex gap-2">
                <input type="text" value={destination} onChange={e => setDestination(e.target.value)} className="flex-1 bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm" />
                <button onClick={() => setShowPicker(true)} className="px-4 py-3 bg-[#0f1f3a] border border-[#1a3a5c] rounded-xl text-[#3bb5ff]">Browse</button>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2"><input type="checkbox" checked={copyMode} onChange={e => setCopyMode(e.target.checked)} className="accent-[#3bb5ff]" /><span className="text-sm">Copy Mode</span></label>
              <label className="flex items-center gap-2"><input type="checkbox" checked={nameCheck} onChange={e => setNameCheck(e.target.checked)} className="accent-[#3bb5ff]" /><span className="text-sm">Name Check</span></label>
            </div>
          </>
        ) : (
          <>
            <div>
              <label className="text-xs text-gray-500 uppercase mb-1 block">New Name</label>
              <input type="text" value={newName} onChange={e => setNewName(e.target.value)} className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-500 uppercase mb-1 block">Rename Mode</label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: 'D', label: 'Default', desc: 'Nickname if exists' },
                  { id: 'N', label: 'Nickname', desc: 'Only nickname' },
                  { id: 'B', label: 'Original', desc: 'Only original name' },
                  { id: 'A', label: 'All', desc: 'Update both' }
                ].map(m => (
                  <button key={m.id} onClick={() => setNameMode(m.id)} className={`p-3 rounded-xl border text-left transition-all ${nameMode === m.id ? 'bg-[#3bb5ff]/20 border-[#3bb5ff] text-white' : 'bg-[#0f1f3a] border-[#1a3a5c] text-gray-400'}`}>
                    <div className="font-medium">{m.label}</div>
                    <div className="text-[10px] opacity-70">{m.desc}</div>
                  </button>
                ))}
              </div>
            </div>
            <label className="flex items-center gap-2"><input type="checkbox" checked={nameCheck} onChange={e => setNameCheck(e.target.checked)} className="accent-[#3bb5ff]" /><span className="text-sm">Name Check</span></label>
          </>
        )}
        <div className="flex justify-end gap-3 pt-4 border-t border-[#1a3a5c]">
          <button onClick={() => onConfirm(null)} className="px-4 py-2 text-sm text-gray-400">Cancel</button>
          <button onClick={handleSubmit} className="px-6 py-2 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-lg font-bold">Confirm {type}</button>
        </div>
      </div>
    );
  };

  const MakeFolderModalContent = () => {
    const [folderName, setFolderName] = useState('');
    const [parent, setParent] = useState(currentPath);
    const [showPicker, setShowPicker] = useState(false);
    if (showPicker) return <ArchiveFolderPicker selectedDb={selectedDb} onSelect={p => { setParent(p); setShowPicker(false); }} onCancel={() => setShowPicker(false)} initialPath={parent} />;
    return (
      <div className="space-y-4">
        <div className="flex gap-2">
          <input type="text" value={parent} onChange={e => setParent(e.target.value)} className="flex-1 bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm" />
          <button onClick={() => setShowPicker(true)} className="px-4 py-3 bg-[#0f1f3a] border border-[#1a3a5c] rounded-xl text-[#3bb5ff]">Browse</button>
        </div>
        <input type="text" value={folderName} onChange={e => setFolderName(e.target.value)} placeholder="Folder name" maxLength={60} className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm" />
        <button onClick={async () => {
          if (!folderName.trim()) return;
          try {
            await fetch('/api/folders/make', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ db_name: selectedDb, folder_name: folderName.trim(), parent_path: parent || '.', id_based: false }) });
            showToast('Folder created', 'success');
            setModal(null);
            fetchFiles(currentPath);
          } catch (e) { showToast(e.message, 'error'); }
        }} className="w-full py-4 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-2xl font-bold">Create</button>
      </div>
    );
  };

  const UploadForm = () => {
    const [localPaths, setLocalPaths] = useState([]);
    const [showPicker, setShowPicker] = useState(false);
    const [encryption, setEncryption] = useState('automatic');
    const [password, setPassword] = useState('');
    const [randomSeed, setRandomSeed] = useState(false);
    const [zeroKnowledge, setZeroKnowledge] = useState(false);
    const [uploadName, setUploadName] = useState('');
    const [newVersionString, setNewVersionString] = useState('');
    const [strictness, setStrictness] = useState('NA');
    const [chunkSize, setChunkSize] = useState('');
    const [minimize, setMinimize] = useState(false);
    const [nameCheck, setNameCheck] = useState(true);
    const [showPassword, setShowPassword] = useState(false);

    const genPass = () => {
      const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+";
      return Array.from(crypto.getRandomValues(new Uint32Array(24))).map(x => chars[x % chars.length]).join('');
    };

    const startUpload = () => {
      if (localPaths.length === 0) { showToast('Select at least one file/folder', 'error'); return; }
      let finalPassword = password;
      if (encryption === 'not_automatic' && !minimize) {
        if (!password && !randomSeed) { showToast('Provide password or select Random', 'error'); return; }
      }
      if (encryption === 'not_automatic' && randomSeed && !showPassword) {
        const p = genPass();
        setPassword(p);
        setShowPassword(true);
        return;
      }
      localPaths.forEach(path => {
        const enc = minimize && encryption === 'not_automatic' ? 'automatic' : encryption;
        const args = ['upload', path, '-db', selectedDb, '-c', config?.discord?.channel_id || '', '--encryption_mode', enc];
        if (enc === 'not_automatic' && finalPassword) args.push('--password_seed', finalPassword);
        if (uploadName) args.push('--upload_name', uploadName);
        if (newVersionString) args.push('--new_version_string', newVersionString);
        if (strictness !== 'NA') args.push('--strictness_mode', strictness);
        if (chunkSize) args.push('--chunk_size_mb', chunkSize);
        if (minimize) args.push('--minimize', 'yes');
        if (!nameCheck) args.push('--no_name_check');
        args.push('--save_hash', encryption === 'not_automatic' && zeroKnowledge ? 'False' : 'True');
        runCmd(args, path.split(/[/\\]/).pop(), 'upload');
      });
      setBottomSheet(null);
      showToast(`${localPaths.length} upload(s) queued`, 'success');
    };

    if (showPicker) return <RemoteFolderPicker initialPath="" showFiles multiSelect onSelect={p => { setLocalPaths(p); if (p.length > 1) setUploadName(''); setShowPicker(false); }} onCancel={() => setShowPicker(false)} />;
    return (
      <div className="space-y-4">
        <div className="flex gap-2">
          <div className="flex-1 bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm text-gray-400 truncate">{localPaths.length ? localPaths.map(p => p.split(/[/\\]/).pop()).join(', ') : 'No files selected'}</div>
          <button onClick={() => setShowPicker(true)} className="px-4 py-3 bg-[#0f1f3a] border border-[#1a3a5c] rounded-xl text-[#3bb5ff] btn-touch">Browse</button>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-[10px] text-gray-500 uppercase">Encryption</label>
            <select value={encryption} onChange={e => setEncryption(e.target.value)} disabled={minimize} className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm">
              <option value="automatic">Automatic</option>
              <option value="off">Off</option>
              <option value="not_automatic">Password</option>
            </select>
          </div>
          <div>
            <label className="text-[10px] text-gray-500 uppercase">Strictness</label>
            <select value={strictness} onChange={e => setStrictness(e.target.value)} className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm">
              <option value="NA">Not Atomic</option>
              <option value="SA">Soft Atomic</option>
              <option value="HA">Hard Atomic</option>
            </select>
          </div>
        </div>
        {encryption === 'not_automatic' && (
          <div>
            <div className="flex gap-2">
              <input type="password" value={password} onChange={e => setPassword(e.target.value)} disabled={randomSeed} placeholder="Password seed" className="flex-1 bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm" />
              <button onClick={() => setRandomSeed(!randomSeed)} className={`px-4 py-3 rounded-xl text-xs font-bold border ${randomSeed ? 'bg-[#3bb5ff]/20 border-[#3bb5ff] text-white' : 'bg-[#0f1f3a] border-[#1a3a5c] text-gray-400'}`}>Random</button>
            </div>
            {showPassword && (
              <div className="mt-2 p-3 bg-green-900/20 border border-green-500/30 rounded-xl">
                <code className="text-xs text-white break-all">{password}</code>
                <button onClick={() => { navigator.clipboard?.writeText(password); showToast('Copied', 'success'); }} className="ml-2 text-[#3bb5ff]">Copy</button>
              </div>
            )}
          </div>
        )}
        <div className={`grid ${localPaths.length <= 1 ? 'grid-cols-2' : 'grid-cols-1'} gap-3`}>
          {localPaths.length <= 1 && (
            <input type="text" value={uploadName} onChange={e => setUploadName(e.target.value)} placeholder="Custom name" className="bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm" />
          )}
          <input type="text" value={newVersionString} onChange={e => setNewVersionString(e.target.value)} placeholder="Version string" className="bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm" />
        </div>
        <input type="number" step="0.1" value={chunkSize} onChange={e => setChunkSize(e.target.value)} placeholder="Chunk size MB (auto)" className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm" />
        <div className="flex flex-wrap gap-4">
          <label className="flex items-center gap-2"><input type="checkbox" checked={nameCheck} onChange={e => setNameCheck(e.target.checked)} className="accent-[#3bb5ff]" /><span className="text-xs">Name Check</span></label>
          <label className="flex items-center gap-2"><input type="checkbox" checked={minimize} onChange={e => setMinimize(e.target.checked)} className="accent-[#3bb5ff]" /><span className="text-xs">Minimize</span></label>
          {encryption === 'not_automatic' && <label className="flex items-center gap-2"><input type="checkbox" checked={zeroKnowledge} onChange={e => setZeroKnowledge(e.target.checked)} disabled={minimize} className="accent-[#3bb5ff]" /><span className="text-xs">Zero‑Knowledge</span></label>}
        </div>
        <button onClick={startUpload} disabled={localPaths.length === 0 || !selectedDb} className="w-full py-4 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-2xl font-bold btn-touch disabled:opacity-40">Queue Upload</button>
      </div>
    );
  };

  const PasswordPromptModalContent = ({ items: pwdItems, onConfirm }) => {
    const [passwords, setPasswords] = useState({});

    const groupedItems = pwdItems.reduce((acc, item) => {
      const key = item.hash || item.id;
      if (!acc[key]) acc[key] = [];
      acc[key].push(item);
      return acc;
    }, {});

    const handleChange = (groupId, val) => {
      setPasswords(prev => {
        const next = { ...prev };
        groupedItems[groupId].forEach(item => {
          next[item.id] = val;
        });
        return next;
      });
    };

    return (
      <div className="space-y-4">
        {Object.entries(groupedItems).map(([groupId, itemsInGroup]) => (
          <div key={groupId} className="bg-[#0a1628] rounded-xl p-3 border border-[#1a3a5c]">
            <div className="max-h-24 overflow-y-auto mb-2 space-y-1">
              {itemsInGroup.map(item => (
                <div key={item.id} className="text-xs text-gray-400 truncate">{item.name}</div>
              ))}
            </div>
            <input type="password" placeholder="Enter password..." onChange={e => handleChange(groupId, e.target.value)} className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm focus:outline-none focus:border-[#3bb5ff]" />
          </div>
        ))}
        <button onClick={() => onConfirm(passwords)} className="w-full py-3 bg-[#3bb5ff] text-[#060d1a] rounded-xl font-bold">Download</button>
      </div>
    );
  };

  const OpenVolumeModalContent = () => {
    const [viewMode, setViewMode] = useState('browse');
    const [currentPath, setCurrentPath] = useState('');
    const [items, setItems] = useState([]);
    const [selectedPaths, setSelectedPaths] = useState([]);
    const [loading, setLoading] = useState(false);

    const load = async () => {
      setLoading(true);
      try {
        if (viewMode === 'databases') {
          const r = await fetch('/api/dbs');
          const data = await r.json();
          setItems((data.dbs || []).map(db => ({ name: db, path: db, is_dir: false, is_db: true })));
          setCurrentPath('DATABASES folder');
        } else {
          const r = await fetch(`/api/fs/browse?path=${encodeURIComponent(currentPath)}`);
          const data = await r.json();
          setCurrentPath(data.current_path);
          setItems(data.items.map(i => ({ ...i, is_db: i.name.toLowerCase().endsWith('.db') })));
        }
      } catch (e) { showToast('Failed to load', 'error'); }
      setLoading(false);
    };
    useEffect(() => { load(); }, [viewMode, currentPath]);

    const handleImport = async (path) => {
      try {
        await fetch('/api/dbs/import', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ vov_path: path }) });
        showToast('Imported successfully', 'success');
        setModal(null);
        fetchDbs();
      } catch (e) { showToast(e.message, 'error'); }
    };

    const toggleSelect = (path) => setSelectedPaths(prev => prev.includes(path) ? prev.filter(p => p !== path) : [...prev, path]);

    return (
      <div className="space-y-4">
        <div className="flex gap-2 p-1 bg-[#060d1a] rounded-xl border border-[#1a3a5c]">
          {['browse', 'databases'].map(m => (
            <button key={m} onClick={() => setViewMode(m)} className={`flex-1 py-2 rounded-lg text-xs font-bold uppercase ${viewMode === m ? 'bg-[#3bb5ff] text-[#0a1628]' : 'text-gray-400'}`}>{m}</button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setCurrentPath('')} className="p-2 btn-touch text-[#3bb5ff]">{Ico.home}</button>
          <div className="text-xs text-gray-400 truncate flex-1">{currentPath || '/'}</div>
        </div>
        {loading ? <div className="text-center py-8 text-gray-500">Loading...</div> : items.map(item => (
          <div key={item.path} onClick={() => item.is_dir ? setCurrentPath(item.path) : (item.is_db ? toggleSelect(item.path) : (item.is_vov ? handleImport(item.path) : null))} className={`flex items-center gap-3 p-3 rounded-xl border transition-all ${selectedPaths.includes(item.path) ? 'bg-[#3bb5ff]/10 border-[#3bb5ff]' : 'hover:bg-[#0f1f3a] border-[#1a3a5c]'}`}>
            <span className="text-[#3bb5ff]">{item.is_dir ? Ico.folder : item.is_db ? Ico.cube : Ico.file}</span>
            <div className="flex-1 truncate">
              <div className="text-sm text-white truncate">{item.name}</div>
              <div className="text-[10px] text-gray-500 truncate">{item.is_dir ? 'Folder' : (item.is_db ? 'Volume' : 'File')}</div>
            </div>
            {item.is_db && <div className={`w-5 h-5 rounded-full border flex items-center justify-center ${selectedPaths.includes(item.path) ? 'bg-[#3bb5ff] border-[#3bb5ff]' : 'border-gray-600'}`}>{selectedPaths.includes(item.path) && <div className="w-2 h-2 bg-white rounded-full" />}</div>}
          </div>
        ))}
        <button onClick={() => setModal(null)} className="w-full py-3 bg-[#0f1f3a] text-white rounded-xl">Cancel</button>
        <button onClick={() => { selectedPaths.forEach(p => { setExternalVolumes(prev => { const u = [...new Set([...prev, p])]; localStorage.setItem('mob_externalVolumes', JSON.stringify(u)); return u; }); }); fetchDbs(); setModal(null); }} className="w-full py-3 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-xl font-bold">Open {selectedPaths.length} Volume(s)</button>
      </div>
    );
  };

  const SharablesModalContent = () => {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(false);
    const [currentPath, setCurrentPath] = useState('');
    const [viewMode, setViewMode] = useState('sharables');

    const fetchSharables = async () => {
      setLoading(true);
      try {
        const r = await fetch('/api/dbs/list_sharables');
        const data = await r.json();
        setItems(data.items || []);
        setCurrentPath(data.path || 'src/SHARABLES');
      } catch (e) { showToast('Failed to load sharables', 'error'); }
      setLoading(false);
    };

    const fetchDirectory = async (path = '') => {
      setLoading(true);
      try {
        const r = await fetch(`/api/fs/browse?path=${encodeURIComponent(path)}`);
        const data = await r.json();
        setCurrentPath(data.current_path);
        setItems(data.items.map(item => ({ ...item, is_vov: item.name.toLowerCase().endsWith('.vov') })));
      } catch (e) { showToast('Failed to browse directory', 'error'); }
      setLoading(false);
    };

    const goHome = async () => {
      try { const r = await fetch('/api/fs/home'); const d = await r.json(); fetchDirectory(d.path); } catch (e) { fetchDirectory(''); }
    };

    useEffect(() => {
      if (viewMode === 'sharables') fetchSharables();
      else fetchDirectory('');
    }, [viewMode]);

    const handleImport = (path, isEncrypted) => {
      if (isEncrypted) {
        setPasswordModal({ open: true, path, password: '', error: '' });
      } else {
        doImport(path, null);
      }
    };

    const handleItemClick = (item) => {
      if (item.is_dir) fetchDirectory(item.path);
      else if (item.is_vov) handleImport(item.path, item.is_encrypted);
    };

    const tabs = [
      { id: 'browse', label: 'System Browser', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5 flex-shrink-0"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" /></svg> },
      { id: 'sharables', label: 'src/SHARABLES', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5 flex-shrink-0"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z" /></svg> },
    ];

    return (
      <div className="-mx-4 -mt-4">
        <div className="flex gap-1 p-2 bg-[#060d1a] border-b border-[#1a3a5c]">
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setViewMode(t.id)}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-1 rounded-lg text-[9px] font-bold uppercase tracking-wide transition-all btn-touch ${viewMode === t.id ? 'bg-[#3bb5ff] text-[#0a1628]' : 'text-gray-400 hover:text-white hover:bg-[#0f1f3a]'}`}
            >
              {t.icon}
              <span className="truncate">{t.label}</span>
            </button>
          ))}
        </div>
        {viewMode !== 'sharables' && (
          <div className="flex items-center gap-2 px-3 py-2 bg-[#060d1a]/60 border-b border-[#1a3a5c]">
            <button onClick={goHome} className="p-1 btn-touch text-[#3bb5ff] hover:bg-[#1a3a5c] rounded-lg flex-shrink-0">{Ico.home}</button>
            <span className="text-[10px] text-gray-500 font-mono truncate flex-1 opacity-70">{currentPath || '/'}</span>
          </div>
        )}
        <div className="overflow-y-auto px-3 pt-2 pb-1 space-y-1" style={{ maxHeight: '50vh' }}>
          {loading ? (
            <div className="text-center py-12 text-gray-500 text-sm">Loading...</div>
          ) : items.filter(item => item.is_dir || item.is_vov).length === 0 ? (
            <div className="text-center py-12 text-gray-500 italic text-sm">No suitable files found.</div>
          ) : (
            items.filter(item => item.is_dir || item.is_vov).map(item => (
              <div
                key={item.path}
                onClick={() => handleItemClick(item)}
                className={`flex items-center gap-3 p-3 rounded-xl border transition-all cursor-pointer btn-touch ${item.is_vov ? 'hover:bg-[#3bb5ff]/10 border-transparent hover:border-[#3bb5ff]/20' : 'hover:bg-[#0f1f3a] border-transparent'}`}
              >
                <span className="flex-shrink-0">
                  {item.is_dir ? <span className="text-[#3bb5ff]/60">{Ico.folder}</span> : (
                    <div className="relative">
                      <span className="text-[#3bb5ff]">{Ico.cube}</span>
                      {item.is_encrypted && (
                        <span className="absolute -top-1 -right-1 text-[10px]">🔒</span>
                      )}
                    </div>
                  )}
                </span>
                <div className="flex-1 min-w-0">
                  <div className={`text-sm truncate ${item.is_vov ? 'text-gray-200' : 'text-gray-400'}`}>{item.name}</div>
                  <div className="text-[10px] text-gray-500 font-mono opacity-50">
                    {item.is_dir ? 'Directory' : item.is_vov ? 'Vault Opus Volume' : 'File'}
                  </div>
                </div>
                {item.is_vov && (
                  <span className="text-[9px] font-bold text-[#3bb5ff]/60 uppercase tracking-widest px-2 py-1 rounded bg-[#3bb5ff]/5 border border-[#3bb5ff]/10 flex-shrink-0">
                    {item.is_encrypted ? '🔒 Import' : 'Import'}
                  </span>
                )}
                {item.is_dir && <span className="text-gray-600 flex-shrink-0">{Ico.back}</span>}
              </div>
            ))
          )}
        </div>
        <div className="px-3 py-2 border-t border-[#1a3a5c]">
          <p className="text-[10px] text-gray-600 italic text-center">Tap a .vov package to import it into your workspace.</p>
        </div>
      </div>
    );
  };

const RenameVolumeModalContent = ({ db }) => {
    const [newName, setNewName] = useState(db.replace(/\.db$/i, ''));
    const [error, setError] = useState('');
    const [saving, setSaving] = useState(false);
    const handleRename = async () => {
      const trimmed = newName.trim();
      if (!trimmed) { setError('Name cannot be empty'); return; }
      const finalName = trimmed.endsWith('.db') ? trimmed : `${trimmed}.db`;
      if (finalName === db) { setModal(null); return; }
      setSaving(true); setError('');
      try {
        const res = await fetch('/api/dbs/rename', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ old_name: db, new_name: finalName }) });
        if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Rename failed'); }
        setDbs(prev => prev.map(d => d === db ? finalName : d));
        if (selectedDb === db) setSelectedDb(finalName);
        updateRecentVolumes(prev => prev.map(d => d === db ? finalName : d));
        setExternalVolumes(prev => { const u = prev.map(d => d === db ? finalName : d); localStorage.setItem('mob_externalVolumes', JSON.stringify(u)); return u; });
        showToast('Volume renamed', 'success');
        setModal(null);
      } catch (e) { setError(e.message); }
      finally { setSaving(false); }
    };
    return (
      <div className="space-y-4">
        <div>
          <label className="text-[10px] text-gray-500 uppercase mb-1 block">New Volume Name</label>
          <input type="text" value={newName} onChange={e => { setNewName(e.target.value); setError(''); }}
            className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm text-gray-200 focus:border-[#3bb5ff] outline-none" autoFocus />
          {error && <p className="text-xs text-red-400 mt-1">{error}</p>}
          <p className="text-[10px] text-gray-600 mt-1">.db extension added automatically if omitted</p>
        </div>
        <div className="flex gap-3 pt-2">
          <button onClick={() => setModal(null)} className="flex-1 py-3 bg-[#0f1f3a] text-gray-300 rounded-xl border border-[#1a3a5c] btn-touch text-sm">Cancel</button>
          <button onClick={handleRename} disabled={saving} className="flex-1 py-3 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-xl font-bold btn-touch text-sm disabled:opacity-50">
            {saving ? 'Renaming…' : 'Save Name'}
          </button>
        </div>
      </div>
    );
  };

  const NukeModalContent = ({ db }) => {
    const [confirm, setConfirm] = useState('');
    const execute = async () => {
      try {
        await fetch('/api/dbs/nuke', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ db_name: db }) });
        showToast(`Volume ${db} has been wiped`, 'success');
        setModal(null);
        if (selectedDb === db) fetchFiles('.');
      } catch (e) { showToast(e.message, 'error'); }
    };
    return (
      <div className="space-y-4">
        <div className="p-4 bg-red-900/20 border border-red-500/30 rounded-xl">
          <p className="text-sm text-red-400 font-bold">☢️ NUKE VOLUME ☢️</p>
          <p className="text-xs text-gray-300 mt-1">All data in <span className="text-white">{db}</span> will be permanently deleted. The file remains but empty.</p>
        </div>
        <input type="text" value={confirm} onChange={e => setConfirm(e.target.value)} placeholder='Type "NUKE" to confirm' className="w-full bg-[#060d1a] border border-red-900/50 rounded-xl px-4 py-3 text-sm" />
        <button onClick={execute} disabled={confirm !== 'NUKE'} className="w-full py-4 bg-red-600 disabled:opacity-30 text-white rounded-xl font-bold">EXECUTE NUKE</button>
      </div>
    );
  };

  const ItemOptionsMenu = ({ item }) => (
    <div className="space-y-2">
      <button onClick={() => { setBottomSheet(null); setModal({ title: 'New Version', content: <NewVersionUploadModalContent targetItemPath={currentPath === '.' ? item.displayName : `${currentPath}/${item.displayName}`} onUpload={() => { }} /> }); }} className="w-full flex items-center gap-3 px-4 py-3 bg-[#0f1f3a] rounded-xl text-sm text-gray-300 btn-touch">{Ico.plus} Upload New Version</button>
      <button onClick={() => { setBottomSheet(null); setModal({ title: 'Versions', content: <SeeVersionsModalContent itemPath={currentPath === '.' ? item.displayName : `${currentPath}/${item.displayName}`} onClose={() => setModal(null)} /> }); }} className="w-full flex items-center gap-3 px-4 py-3 bg-[#0f1f3a] rounded-xl text-sm text-gray-300 btn-touch">{Ico.clock} See Versions</button>
      <button onClick={() => { setBottomSheet(null); setModal({ title: 'Download Version', content: <DownloadVersionModalContent itemPath={currentPath === '.' ? item.displayName : `${currentPath}/${item.displayName}`} item={item} onDownload={(args) => { if (args) { const isEncrypted = item && (item.encryption === 'not_automatic' || item.encryption_mode === 'not_automatic'); if (isEncrypted) { setModal({ title: 'Passwords Required', content: <PasswordPromptModalContent items={[{ id: item.itemid, name: item.displayName, hash: item.password_seed_hash || '' }]} onConfirm={(passwords) => { setModal(null); const finalArgs = [...args]; if (Object.keys(passwords).length) { finalArgs.push('--passwords', JSON.stringify(passwords)); } runCmd(finalArgs, item.displayName, 'download'); showToast('Download queued', 'success'); }} /> }); } else { runCmd(args, item.displayName, 'download'); setModal(null); showToast('Download queued', 'success'); } } else setModal(null); }} /> }); }} className="w-full flex items-center gap-3 px-4 py-3 bg-[#0f1f3a] rounded-xl text-sm text-gray-300 btn-touch">{Ico.download} Download Version</button>
      <button onClick={() => { setBottomSheet(null); setModal({ title: 'Move / Copy', content: <ModifyModalContent type="move" item={item} onConfirm={(data) => { if (data) { const args = ['modify', data.type]; if (data.type === 'move') { args.push(data.src, data.dst); if (data.copyMode) args.push('--copy'); if (data.srcIdBased) args.push('--src_id_based'); if (data.dstIdBased) args.push('--dst_id_based'); } else { args.push(data.item, data.newName); if (data.nameMode !== 'D') args.push('--mode', data.nameMode); } args.push('-db', selectedDb); if (data.type !== 'move' && data.idBased) args.push('--id_based'); if (!data.nameCheck) args.push('--no_name_check'); runCmd(args, item.displayName, data.type); setModal(null); showToast(`${data.type} queued`, 'success'); } else setModal(null); }} /> }); }} className="w-full flex items-center gap-3 px-4 py-3 bg-[#0f1f3a] rounded-xl text-sm text-gray-300 btn-touch">{Ico.move} Move / Copy</button>
      <button onClick={() => { setBottomSheet(null); setModal({ title: 'Rename', content: <ModifyModalContent type="rename" item={item} onConfirm={(data) => { if (data) { const args = ['modify', data.type]; args.push(data.item, data.newName); if (data.nameMode !== 'D') args.push('--mode', data.nameMode); args.push('-db', selectedDb); if (data.idBased) args.push('--id_based'); if (!data.nameCheck) args.push('--no_name_check'); runCmd(args, item.displayName, 'rename'); setModal(null); showToast('Rename queued', 'success'); } else setModal(null); }} /> }); }} className="w-full flex items-center gap-3 px-4 py-3 bg-[#0f1f3a] rounded-xl text-sm text-gray-300 btn-touch">{Ico.rename} Rename</button>
      <button onClick={() => { setBottomSheet(null); setModal({ title: 'Delete Item', content: <DeleteModalContent singleItem={item} onConfirm={(opts) => { const a = ['delete']; if (item.itemid) a.push(item.itemid, '--id_based'); else a.push(currentPath === '.' ? item.displayName : `${currentPath}/${item.displayName}`); a.push('-db', selectedDb, '--skip_confirmation', 'yes'); if (opts.type === 'hard') a.push('--hard'); if (opts.scope === 'all') a.push('--all_versions', 'yes'); else if (opts.scope === 'specific' && opts.version) a.push('--version', opts.version); else if (opts.scope === 'range' && opts.startVersion && opts.endVersion) a.push('--st_version', opts.startVersion, '--en_version', opts.endVersion); runCmd(a, item.displayName, 'delete'); setModal(null); clearSelection(); showToast('Delete queued', 'success'); }} onCancel={() => setModal(null)} /> }); }} className="w-full flex items-center gap-3 px-4 py-3 bg-red-900/20 border border-red-900/30 rounded-xl text-sm text-red-400 btn-touch">{Ico.trash} Delete</button>
      <button onClick={() => { setBottomSheet(null); setModal({ title: 'Full Name Metadata', content: <FullNameModalContent item={item} onClose={() => setModal(null)} /> }); }} className="w-full flex items-center gap-3 px-4 py-3 bg-[#0f1f3a] rounded-xl text-sm text-gray-300 btn-touch">{Ico.info} Show Full Name</button>
    </div>
  );

  // -------------------- RENDER --------------------
  const CreateVolumeModalContent = () => {
    const [name, setName] = useState('');
    const [error, setError] = useState('');
    const [creating, setCreating] = useState(false);
    const handleCreate = async () => {
      const trimmed = name.trim();
      if (!trimmed) { setError('Volume name cannot be empty'); return; }
      const finalName = trimmed.endsWith('.db') ? trimmed : `${trimmed}.db`;
      setCreating(true); setError('');
      try {
        const res = await fetch('/api/dbs/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ db_name: finalName })
        });
        if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Failed to create volume'); }
        showToast(`Volume ${finalName} created`, 'success');
        setShowCreateVolume(false);
        setName('');
        fetchDbs();
      } catch (e) { setError(e.message); }
      finally { setCreating(false); }
    };

    return (
      <div className="space-y-4">
        <div>
          <label className="text-[10px] text-gray-500 uppercase mb-1 block">Volume Name</label>
          <input
            type="text"
            value={name}
            onChange={e => { setName(e.target.value); setError(''); }}
            placeholder="e.g. myvault"
            className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm text-gray-200 outline-none focus:border-[#3bb5ff] transition-colors"
            autoFocus
          />
          {error && <p className="text-xs text-red-400 mt-1">{error}</p>}
          <p className="text-[10px] text-gray-600 mt-1">.db extension added automatically if omitted</p>
        </div>
        <div className="flex gap-3 pt-2">
          <button
            onClick={() => { setShowCreateVolume(false); setName(''); setError(''); }}
            className="flex-1 py-3 bg-[#0f1f3a] text-gray-300 rounded-xl border border-[#1a3a5c] btn-touch text-sm"
          >
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={creating || !name.trim()}
            className="flex-1 py-3 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-xl font-bold btn-touch text-sm disabled:opacity-40"
          >
            {creating ? 'Creating...' : 'Create Volume'}
          </button>
        </div>
      </div>
    );
  };

  const VolumeOptionsMenu = ({ db }) => (
    <div className="space-y-2">
      <button onClick={() => { setModal(null); setSelectedDb(db); setTab('explorer'); }} className="w-full flex items-center gap-3 px-4 py-3 bg-[#0f1f3a] rounded-xl text-sm text-gray-300 btn-touch">{Ico.folderOpen} Open</button>
      <button onClick={() => { setModal({ title: 'Rename Volume', content: <RenameVolumeModalContent db={db} /> }); }} className="w-full flex items-center gap-3 px-4 py-3 bg-[#0f1f3a] rounded-xl text-sm text-gray-300 btn-touch">{Ico.rename} Rename</button>
      <button onClick={() => { setModal(null); setDbToShare(db); setShowSharePasswordModal(true); }} className="w-full flex items-center gap-3 px-4 py-3 bg-[#0f1f3a] rounded-xl text-sm text-gray-300 btn-touch">{Ico.share} Package</button>
      <button onClick={() => { setModal(null); setModal({ title: '☢️ NUKE', content: <NukeModalContent db={db} /> }); }} className="w-full flex items-center gap-3 px-4 py-3 bg-red-900/10 border border-red-900/20 rounded-xl text-sm text-red-500 font-bold btn-touch">☢️ NUKE</button>
      <button onClick={() => { setModal({ title: 'Confirm Deletion', content: <DeleteConfirmModal db={db} /> }); }} className="w-full flex items-center gap-3 px-4 py-3 bg-red-900/20 border border-red-900/30 rounded-xl text-sm text-red-400 btn-touch">{Ico.trash} Delete Permanently</button>
    </div>
  );

  const DeleteConfirmModal = ({ db }) => (
    <div className="space-y-4">
      <div className="p-4 bg-red-900/20 border border-red-500/30 rounded-xl">
        <p className="text-sm text-red-400 font-bold">⚠️ PERMANENT DELETE</p>
        <p className="text-xs text-gray-300 mt-1">This will permanently remove <span className="text-white font-mono">{db}</span> from disk. This CANNOT be undone.</p>
      </div>
      <div className="flex gap-3">
        <button onClick={() => setModal(null)} className="flex-1 py-3 bg-[#0f1f3a] text-gray-300 rounded-xl border border-[#1a3a5c] btn-touch">Cancel</button>
        <button onClick={async () => { try { await fetch('/api/dbs/delete', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ db_name: db }) }); fetchDbs(); if (selectedDb === db) setSelectedDb(''); showToast('Deleted', 'success'); setModal(null); } catch (e) { showToast(e.message, 'error'); } }} className="flex-1 py-3 bg-red-600 text-white rounded-xl font-bold btn-touch">Delete</button>
      </div>
    </div>
  );

  const renderExplorer = () => (
    <div className="flex flex-col h-full bg-[#060d1a]">
      <div className="flex items-center gap-1 px-3 py-2 bg-[#0a1628] border-b border-[#1a3a5c] overflow-x-auto">
        <button onClick={() => handleNavigate('.')} className={`px-3 py-1.5 text-[10px] font-bold rounded-lg btn-touch ${currentPath === '.' ? 'bg-[#3bb5ff] text-[#0a1628]' : 'bg-[#0f1f3a] text-gray-400'}`}>ROOT</button>
        {currentPath !== '.' && currentPath.split('/').map((part, i, arr) => (
          <React.Fragment key={i}>
            <span className="text-gray-700">/</span>
            <button onClick={() => handleNavigate(arr.slice(0, i + 1).join('/'))} className={`px-3 py-1.5 text-[10px] font-bold rounded-lg btn-touch ${i === arr.length - 1 ? 'bg-[#3bb5ff]/20 text-[#3bb5ff] border border-[#3bb5ff]/40' : 'bg-[#0f1f3a] text-gray-400'}`}>{part.toUpperCase()}</button>
          </React.Fragment>
        ))}
        {currentVersion && <button onClick={() => { setCurrentVersion(null); fetchFiles(currentPath); }} className="ml-2 px-3 py-1.5 text-[9px] bg-orange-500/20 border border-orange-500/50 rounded-full text-orange-400 font-bold btn-touch animate-pulse">V:{currentVersion} ✕</button>}
      </div>

      <div className="flex gap-2 px-3 py-3 bg-[#0a1628] border-b border-[#1a3a5c] overflow-x-auto">
        <button onClick={() => setBottomSheet({ title: 'Upload', content: <UploadForm /> })} className="p-3 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-xl btn-touch shadow-lg">{Ico.upload}</button>
        <button onClick={() => { if (selectedItems.length) setModal({ title: 'Download', content: <DownloadModalContent onConfirm={(opts) => { executeDownload(selectedItems, opts.strictnessMode); }} onCancel={() => setModal(null)} /> }); }} disabled={!selectedItems.length} className="p-3 bg-[#0f1f3a] border border-[#1a3a5c] text-gray-300 rounded-xl btn-touch disabled:opacity-40">{Ico.download}</button>
        <button onClick={() => { if (selectedItems.length) setModal({ title: 'Delete', content: <DeleteModalContent singleItem={selectedItems.length === 1 ? selectedItems[0] : null} onConfirm={(opts) => { selectedItems.forEach(item => { const a = ['delete']; if (item.itemid) a.push(item.itemid, '--id_based'); else a.push(currentPath === '.' ? item.displayName : `${currentPath}/${item.displayName}`); a.push('-db', selectedDb, '--skip_confirmation', 'yes'); if (opts.type === 'hard') a.push('--hard'); if (opts.scope === 'all') a.push('--all_versions', 'yes'); else if (opts.scope === 'specific' && opts.version) a.push('--version', opts.version); else if (opts.scope === 'range' && opts.startVersion && opts.endVersion) a.push('--st_version', opts.startVersion, '--en_version', opts.endVersion); runCmd(a, item.displayName, 'delete'); }); clearSelection(); setModal(null); showToast('Delete queued', 'success'); }} onCancel={() => setModal(null)} /> }); }} disabled={!selectedItems.length} className="p-3 bg-red-900/20 border border-red-900/40 text-red-400 rounded-xl btn-touch disabled:opacity-40">{Ico.trash}</button>
        <button onClick={() => setModal({ title: 'New Folder', content: <MakeFolderModalContent /> })} className="p-3 bg-[#0f1f3a] border border-[#1a3a5c] text-gray-300 rounded-xl btn-touch">{Ico.newFolder}</button>
        <button onClick={() => setSelectedItems([...items])} disabled={!items.length} className="p-3 bg-[#0f1f3a] border border-[#1a3a5c] text-gray-300 rounded-xl btn-touch disabled:opacity-40">{Ico.selectAll}</button>
        <button onClick={handleRefresh} className="p-3 bg-[#0f1f3a] border border-[#1a3a5c] text-[#3bb5ff] rounded-xl btn-touch">{Ico.version}</button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 pb-32 custom-scrollbar">
        {volumeError ? (
          <div className="flex flex-col items-center justify-center h-full py-20">
            <div className="mb-6 scale-150 text-red-500">{Ico.alert}</div>
            <p className="text-sm font-bold uppercase tracking-widest text-red-400">{volumeError}</p>
            <p className="text-xs text-gray-600 mt-2">Select a valid volume from the Volumes tab</p>
            <button onClick={() => { retryCountRef.current = 0; fetchFiles(currentPath); }} className="mt-4 px-6 py-2 bg-[#0f1f3a] border border-[#1a3a5c] text-[#3bb5ff] rounded-xl text-sm font-bold btn-touch">Retry Connection</button>
          </div>
        ) : isRetrying ? (
          <div className="flex flex-col items-center justify-center h-full py-20">
            <div className="mb-6 animate-spin text-[#3bb5ff]">{Ico.version}</div>
            <p className="text-sm font-bold uppercase tracking-widest text-[#3bb5ff]">Connecting to Volume...</p>
            <p className="text-[10px] text-gray-500 mt-2 uppercase tracking-widest">Attempt {retryCountRef.current} of {maxRetries}</p>
          </div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-600 opacity-40 py-20">
            <div className="mb-6 scale-150">{Ico.folder}</div>
            <p className="text-sm font-bold uppercase tracking-widest">Folder is empty</p>
          </div>
        ) : (
          <div className="grid grid-cols-[repeat(auto-fill,minmax(100px,1fr))] gap-3">
            {items.map((item, idx) => {
              const isSelected = selectedItems.find(i => i.itemid === item.itemid);
              const isFolder = item.type === 'folder';
              return (
                <div key={idx} onClick={() => toggleSelect(item)} onDoubleClick={() => { if (isFolder) { const t = item.db_name || item.name; handleNavigate(currentPath === '.' ? t : `${currentPath}/${t}`); } }} className={`flex flex-col items-center justify-center p-4 rounded-2xl border transition-all btn-touch aspect-square relative ${isSelected ? 'bg-[#3bb5ff]/20 border-[#3bb5ff] shadow-lg scale-[0.98]' : 'bg-[#0a1628]/60 border-[#1a3a5c] hover:border-[#3bb5ff]/40'}`}>
                  {isSelected && <div className="absolute top-2 right-2 w-5 h-5 bg-[#3bb5ff] text-[#0a1628] rounded-full flex items-center justify-center">{Ico.check}</div>}
                  <div className={`mb-2 transition-transform ${isSelected ? 'scale-110' : ''}`}>{isFolder ? Ico.folder : Ico.file}</div>
                  <div className={`text-[10px] font-bold text-center truncate w-full px-1 ${isSelected ? 'text-white' : 'text-gray-400'}`}>{item.displayName}</div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {selectedItems.length === 1 && (
        <div className="fixed bottom-24 left-4 right-4 bg-[#0a1628]/95 backdrop-blur-xl border border-[#3bb5ff]/40 px-6 py-4 rounded-3xl flex items-center justify-between z-40 shadow-2xl">
          <span className="text-xs text-[#3bb5ff] font-black uppercase">1 SELECTED</span>
          <div className="flex gap-4">
            <button onClick={() => setBottomSheet({ title: 'Item Options', content: <ItemOptionsMenu item={selectedItems[0]} /> })} className="p-3 bg-[#3bb5ff]/10 text-[#3bb5ff] rounded-xl btn-touch">{Ico.menu}</button>
            <button onClick={clearSelection} className="p-3 text-gray-500 btn-touch hover:text-white">{Ico.close}</button>
          </div>
        </div>
      )}
    </div>
  );

  // Download execution helper
  const executeDownload = (itemsToDownload, strictnessMode = 'NA') => {
    const needsPassword = (i) => {
      if (i.encryption === 'not_automatic' || i.encryption_mode === 'not_automatic') return true;
      if (i.type === 'folder' && Array.isArray(i.versions)) return i.versions.some(v => v.has_hash || v.encryption === 'not_automatic');
      if (i.password_seed_hash) return true;
      return false;
    };
    const encryptedItems = itemsToDownload.filter(needsPassword);
    if (encryptedItems.length) {
      setModal({ title: 'Passwords Required', content: <PasswordPromptModalContent items={encryptedItems.map(i => ({ id: i.itemid, name: i.displayName, hash: i.password_seed_hash || '' }))} onConfirm={(passwords) => { setModal(null); doDownload(itemsToDownload, passwords, strictnessMode); }} /> });
    } else {
      doDownload(itemsToDownload, {}, strictnessMode);
      setModal(null);
    }
  };
  const doDownload = (itemsToDownload, passwords, strictnessMode) => {
    const downloadFolder = localStorage.getItem('VAULT_OPUS_download_folder') || '/storage/emulated/0/Download';
    itemsToDownload.forEach(item => {
      const itemPath = currentPath === '.' ? item.displayName : `${currentPath}/${item.displayName}`;
      const args = ['download', itemPath, '-db', selectedDb, '--download_folder', downloadFolder];
      if (Object.keys(passwords).length) args.push('--passwords', JSON.stringify(passwords));
      if (strictnessMode !== 'NA') args.push('--strictness_mode', strictnessMode);
      runCmd(args, item.displayName, 'download');
    });
  };

  // Volume tabs
  const renderVolumes = () => (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 bg-[#0a1628] border-b border-[#1a3a5c] flex items-center justify-between">
        <h2 className="text-lg font-bold text-white">Volumes</h2>
        <div className="flex gap-2">
          <button onClick={async () => { await fetchDbs(); showToast('Volume list refreshed', 'success'); }} className="p-2 bg-[#0f1f3a] border border-[#1a3a5c] text-gray-300 rounded-xl btn-touch" title="Refresh Volume List">{Ico.version}</button>
          <button onClick={() => setModal({ title: 'Sharables', content: <SharablesModalContent /> })} className="p-2 bg-[#0f1f3a] border border-[#1a3a5c] text-[#3bb5ff] rounded-xl btn-touch" title="Open Sharables">{Ico.externalLink}</button>
          <button onClick={() => setShowCreateVolume(true)} className="p-2 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-xl btn-touch" title="Create Volume">{Ico.plus}</button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-6">
        {recentVolumes.length > 0 && (
          <section>
            <div className="flex items-center gap-2 mb-3"><span className="text-[#3bb5ff]/50">{Ico.clock}</span><h3 className="text-[10px] uppercase font-bold text-[#3bb5ff]/50">Recent</h3></div>
            <div className="space-y-2">{recentVolumes.map(db => (
              <div key={db} className={`flex items-center justify-between px-4 py-3 rounded-xl border btn-touch ${selectedDb === db ? 'bg-[#3bb5ff]/15 border-[#3bb5ff]' : 'bg-[#0f1f3a]/40 border-[#1a3a5c]'}`}>
                <div
                  onClick={() => { if (selectedDb === db) fetchFiles(currentPath); else setSelectedDb(db); setTab('explorer'); }}
                  className="flex-1 flex items-center gap-3 min-w-0 mr-2 py-1"
                >
                  <span className={selectedDb === db ? 'text-[#3bb5ff]' : 'text-gray-500'}>{Ico.cube}</span>
                  <div className="text-sm font-bold truncate text-white">{db.split(/[\/\\]/).pop().replace('.db', '')}</div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    updateRecentVolumes(prev => prev.filter(d => d !== db));
                    if (selectedDb === db) setSelectedDb('');
                    showToast('Removed', 'success');
                  }}
                  className="p-3 -m-1.5 text-gray-600 hover:text-red-400 rounded-lg transition-colors flex-shrink-0"
                >
                  {Ico.close}
                </button>
              </div>
            ))}</div>
          </section>
        )}
        <section>
          <div className="flex items-center justify-between mb-3"><div className="flex items-center gap-2"><span className="text-[#3bb5ff]/50">{Ico.cube}</span><h3 className="text-[10px] uppercase font-bold text-[#3bb5ff]/50">Available</h3></div><button onClick={() => setModal({ title: 'Add External Volume', content: <RemoteFolderPicker showFiles onSelect={p => { if (p.endsWith('.db')) { setExternalVolumes(prev => { const u = [...new Set([...prev, p])]; localStorage.setItem('mob_externalVolumes', JSON.stringify(u)); return u; }); fetchDbs(); setModal(null); showToast('Volume added', 'success'); } else showToast('Must be .db', 'error'); }} onCancel={() => setModal(null)} /> })} className="text-[10px] text-[#3bb5ff] font-bold btn-touch uppercase">+ External</button></div>
          <div className="space-y-2">{dbs.map(db => (
            <div key={db} className={`flex items-center justify-between px-4 py-3 rounded-xl border btn-touch ${selectedDb === db ? 'bg-[#3bb5ff]/15 border-[#3bb5ff]' : 'bg-[#0f1f3a]/40 border-[#1a3a5c]'}`}>
              <div
                onClick={() => { if (selectedDb === db) fetchFiles(currentPath); else setSelectedDb(db); setTab('explorer'); }}
                className="flex-1 flex items-center gap-3 min-w-0 mr-2 py-1"
              >
                <span className={selectedDb === db ? 'text-[#3bb5ff]' : 'text-gray-500'}>{Ico.cube}</span>
                <span className="text-sm font-bold text-white truncate">{db.split(/[\/\\]/).pop().replace('.db', '')}</span>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setModal({ title: 'Volume Options', content: <VolumeOptionsMenu db={db} /> });
                }}
                className="p-3 -m-1.5 text-gray-500 hover:text-white btn-touch"
              >
                {Ico.menu}
              </button>
            </div>
          ))}</div>
        </section>
        <button onClick={() => setModal({ title: 'Import .vov Package', content: <div className="space-y-3"><RemoteFolderPicker showFiles onSelect={async p => { if (p.endsWith('.vov')) { try { await fetch('/api/dbs/import', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ vov_path: p }) }); fetchDbs(); showToast('Imported', 'success'); setModal(null); } catch (e) { showToast(e.message, 'error'); } } else showToast('Must select .vov', 'error'); }} onCancel={() => setModal(null)} /></div> })} className="w-full py-4 bg-[#0f1f3a] border border-[#1a3a5c] rounded-2xl text-xs text-gray-300 font-bold uppercase btn-touch flex items-center justify-center gap-2">{Ico.import} Import VOV Package</button>
      </div>
    </div>
  );
  const renderQueue = () => (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 bg-[#0a1628] border-b border-[#1a3a5c] flex items-center justify-between"><h2 className="text-lg font-bold text-white">Queue</h2><button onClick={() => setQueue([])} className="text-xs text-gray-400 btn-touch">Clear All</button></div>
      <div className="flex-1 overflow-y-auto p-3 space-y-2">{queue.length === 0 ? <div className="text-center py-20 text-gray-500 text-sm">No active tasks</div> : queue.slice().reverse().map(item => (<div key={item.id} className="flex items-center gap-3 px-3 py-2 bg-[#0a1628] border border-[#1a3a5c] rounded-xl"><div className={`w-2 h-2 rounded-full ${item.status === 'completed' ? 'bg-green-400' : item.status === 'failed' ? 'bg-red-400' : item.status === 'running' ? 'bg-[#3bb5ff] animate-pulse' : 'bg-gray-500'}`} /><div className="flex-1"><div className="text-xs text-gray-200 truncate">{item.name}</div><div className="text-[10px] text-gray-500 capitalize">{item.status}</div></div>{item.progress > 0 && <div className="text-xs text-[#3bb5ff]">{item.progress}%</div>}</div>))}</div>
    </div>
  );

  const renderTerminal = () => (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 bg-[#0a1628] border-b border-[#1a3a5c] flex items-center justify-between"><h2 className="text-lg font-bold text-white">Terminal</h2><button onClick={() => setTerminalOutput('')} className="text-xs text-gray-400 btn-touch">Clear</button></div>
      <div className="flex-1 overflow-y-auto p-3 bg-[#060d1a]"><pre className="text-xs text-green-400 font-mono whitespace-pre-wrap break-all">{terminalOutput || 'No output yet'}</pre></div>
    </div>
  );

  return (
    <div className="flex flex-col h-full safe-top bg-[#060d1a]">
      <header className="flex items-center justify-between px-6 py-4 bg-[#0a1628] border-b border-[#1a3a5c] shadow-lg">
        <div className="flex items-center gap-3">
          <img src="/logo/image.png" alt="Logo" className="w-8 h-8 object-contain drop-shadow-[0_0_8px_rgba(59,181,255,0.4)]" onError={(e) => e.target.style.display = 'none'} />
          <div><h1 className="text-lg font-black text-white tracking-tighter">VAULT OPUS</h1>{selectedDb && <p className="text-[10px] text-[#3bb5ff] font-bold uppercase mt-1">{selectedDb.replace('.db', '')}</p>}</div>
        </div>
        <div className="flex items-center gap-2">
          {connectionStatus === 'disconnected' && <button onClick={connectWS} className="p-2 text-red-500 btn-touch">{Ico.alert}</button>}
        </div>
      </header>

      <div className="flex-1 overflow-hidden relative">
        {tab === 'explorer' && renderExplorer()}
        {tab === 'volumes' && renderVolumes()}
        {tab === 'queue' && renderQueue()}
        {tab === 'terminal' && renderTerminal()}
        {tab === 'settings' && <SettingsTabContent config={config} fetchConfig={fetchConfig} showToast={showToast} />}
      </div>

      <nav className="flex items-center justify-around bg-[#0a1628] border-t border-[#1a3a5c] py-4 safe-bottom shadow-[0_-10px_30px_rgba(0,0,0,0.4)]">
        {[
          { id: 'explorer', label: 'Files', icon: Ico.folder },
          { id: 'volumes', label: 'Volumes', icon: Ico.cube, badge: 0 },
          { id: 'queue', label: 'Queue', icon: Ico.clock, badge: queue.filter(q => q.status === 'running' || q.status === 'queued').length },
          { id: 'terminal', label: 'Terminal', icon: Ico.terminal },
          { id: 'settings', label: 'Settings', icon: Ico.settings }
        ].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} className={`flex flex-col items-center gap-2 px-2 py-1 rounded-3xl btn-touch transition-all ${tab === t.id ? 'text-[#3bb5ff]' : 'text-gray-500'}`}>
            <div className={`p-2 rounded-2xl transition-all ${tab === t.id ? 'bg-[#3bb5ff]/15 shadow-[0_0_15px_rgba(59,181,255,0.2)]' : ''}`}>{t.icon}</div>
            <span className={`text-[9px] font-black uppercase tracking-[0.1em] ${tab === t.id ? 'opacity-100' : 'opacity-40'}`}>{t.label}</span>
            {t.badge > 0 && <span className="absolute top-0 right-0 w-6 h-6 bg-[#3bb5ff] text-[10px] text-[#0a1628] rounded-full flex items-center justify-center font-black border-[3px] border-[#0a1628] shadow-lg">{t.badge}</span>}
          </button>
        ))}
      </nav>

      {bottomSheet && <Sheet open onClose={() => setBottomSheet(null)} title={bottomSheet.title}>{bottomSheet.content}</Sheet>}
      {modal && <Modal open onClose={() => setModal(null)} title={modal.title} wide={modal.wide}>{modal.content}</Modal>}
      {showCreateVolume && (
        <Modal open onClose={() => setShowCreateVolume(false)} title="Create New Volume">
          <CreateVolumeModalContent />
        </Modal>
      )}
      {passwordModal.open && (
        <div className="fixed inset-0 z-[130] flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-[#0a1628] border border-[#1a3a5c] rounded-2xl w-full max-w-md p-6 shadow-2xl">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-red-400">🔒</span>
              <h3 className="text-lg font-bold text-white">Password Protected Package</h3>
            </div>
            {passwordModal.error && <div className="mb-3 p-3 bg-red-900/20 border border-red-500/30 rounded-lg text-red-400 text-sm">{passwordModal.error}</div>}
            <input type="password" value={passwordModal.password} onChange={(e) => setPasswordModal(prev => ({ ...prev, password: e.target.value }))} onKeyDown={(e) => { if (e.key === 'Enter' && passwordModal.password) doImport(passwordModal.path, passwordModal.password); }} placeholder="Enter package password..." className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-4 py-3 text-sm text-white outline-none mb-4" autoFocus />
            <div className="flex gap-3">
              <button onClick={() => setPasswordModal({ open: false, path: '', password: '', error: '' })} className="flex-1 py-3 bg-[#0f1f3a] text-gray-300 rounded-xl font-bold">Cancel</button>
              <button onClick={() => doImport(passwordModal.path, passwordModal.password)} disabled={!passwordModal.password} className="flex-1 py-3 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-xl font-bold disabled:opacity-40">Import</button>
            </div>
          </div>
        </div>
      )}
      {showSharePasswordModal && (
        <Modal open onClose={() => { setShowSharePasswordModal(false); setDbToShare(''); }} title="Share Volume">
          <div className="space-y-4">
            <p className="text-sm text-gray-300">Choose how to package <b>{dbToShare}</b>:</p>
            <button onClick={() => executeShare(null)} className="w-full py-3 bg-[#0f1f3a] border border-[#1a3a5c] text-gray-200 rounded-xl font-bold">📦 Passwordless Package</button>
            <div className="relative">
              <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-[#1a3a5c]"></div></div>
              <div className="relative flex justify-center text-xs"><span className="px-2 bg-[#0a1628] text-gray-500">or</span></div>
            </div>
            <form onSubmit={(e) => { e.preventDefault(); const pwd = e.target.password.value; if (pwd) executeShare(pwd); }} className="space-y-3">
              <input name="password" type="password" placeholder="Enter password..." className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm text-white outline-none focus:border-[#3bb5ff]" autoFocus />
              <button type="submit" className="w-full py-3 bg-gradient-to-r from-red-600 to-red-400 text-white rounded-xl font-bold">🔒 Password-Protected Package</button>
            </form>
          </div>
        </Modal>
      )}
      {toast && <Toast key={toast.key} message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
}