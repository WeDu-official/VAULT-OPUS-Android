import React, { useState, useEffect, useRef } from 'react'

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
  clock: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5"><path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
  terminal: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>,
  rename: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5"><path d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>,
  move: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5"><path d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" /></svg>,
  check: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5"><path d="M5 13l4 4L19 7" /></svg>,
  info: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5"><path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
  newFolder: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M9 13h6m-3-3v6m-5 4h10a2 2 0 002-2V9a2 2 0 00-2-2h-2.586a1 1 0 01-.707-.293l-1.414-1.414a1 1 0 00-.707-.293H7a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>,
  selectAll: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M4 6h16M4 10h16M4 14h16M4 18h16" /></svg>,
  share: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5"><path d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" /></svg>,
  version: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5"><path d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" /></svg>,
  alert: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M12 9v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
  copy: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5"><path d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>,
  folderOpen: <svg viewBox="0 0 20 20" fill="currentColor" className="w-6 h-6 text-[#3bb5ff]"><path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" /></svg>,
  home: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" /></svg>,
  import: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6"><path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>,
}
// ─────────────────── TOAST / ALERT ───────────────────
function Toast({ message, type, onClose }) {
  useEffect(() => { const t = setTimeout(onClose, 3000); return () => clearTimeout(t) }, [])
  const bg = type === 'error' ? 'bg-red-900/80 border-red-500/50' : type === 'success' ? 'bg-green-900/80 border-green-500/50' : 'bg-[#0a1628] border-[#1a3a5c]'
  const icon = type === 'error' ? 'text-red-400' : type === 'success' ? 'text-green-400' : 'text-[#3bb5ff]'
  return (
    <div className={`fixed top-16 left-4 right-4 z-50 ${bg} border rounded-xl px-4 py-3 shadow-2xl flex items-center gap-3 animate-in fade-in`}>
      <span className={icon}>{Ico.alert}</span>
      <span className="text-sm text-gray-200 flex-1">{message}</span>
      <button onClick={onClose} className="text-gray-500 btn-touch p-1">{Ico.close}</button>
    </div>
  )
}

// ─────────────────── BOTTOM SHEET ───────────────────
function Sheet({ open, onClose, title, children }) {
  if (!open) return null
  return (
    <>
      <div className="modal-overlay fixed inset-0 z-40" onClick={onClose} />
      <div className="fixed bottom-0 left-0 right-0 z-50 sheet-enter safe-bottom" style={{ maxHeight: '85vh' }}>
        <div className="bg-[#0a1628] border-t border-[#1a3a5c] rounded-t-2xl shadow-2xl flex flex-col max-h-[85vh]">
          <div className="flex items-center justify-between p-4 border-b border-[#1a3a5c] sticky top-0 bg-[#0a1628] rounded-t-2xl z-10">
            <h3 className="text-lg font-bold text-white">{title}</h3>
            <button onClick={onClose} className="p-2 btn-touch text-gray-400 hover:text-white">{Ico.close}</button>
          </div>
          <div className="overflow-y-auto p-4 flex-1">{children}</div>
        </div>
      </div>
    </>
  )
}

// ─────────────────── MODAL ───────────────────
function Modal({ open, onClose, title, children, wide }) {
  if (!open) return null
  return (
    <>
      <div className="modal-overlay fixed inset-0 z-40" onClick={onClose} />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className={`bg-[#0a1628] border border-[#1a3a5c] rounded-xl shadow-2xl ${wide ? 'w-full max-w-lg' : 'w-full max-w-md'} max-h-[80vh] overflow-y-auto p-4 animate-in fade-in`}>
          <div className="flex items-center justify-between mb-4 border-b border-[#1a3a5c] pb-3">
            <h3 className="text-lg font-bold text-white">{title}</h3>
            <button onClick={onClose} className="p-2 btn-touch text-gray-400 hover:text-white">{Ico.close}</button>
          </div>
          {children}
        </div>
      </div>
    </>
  )
}

// ─────────────────── REMOTE FOLDER PICKER (MOBILE) ───────────────────
const RemoteFolderPicker = ({ initialPath, onSelect, onCancel, showFiles = false, multiSelect = false }) => {
  const [currentPath, setCurrentPath] = useState(initialPath || '');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedPaths, setSelectedPaths] = useState([]);

  useEffect(() => { fetchDirectory(initialPath); }, [initialPath]);

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

  const handleItemClick = (item) => {
    if (item.name === '..') { fetchDirectory(item.path); return; }
    if (item.is_dir) { fetchDirectory(item.path); }
    else if (showFiles) {
      if (multiSelect) {
        setSelectedPaths(prev => prev.includes(item.path) ? prev.filter(p => p !== item.path) : [...prev, item.path]);
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
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {loading ? <p className="text-center p-8 text-gray-500 animate-pulse">Scanning...</p> : error ? <p className="text-red-400 p-4 text-center">{error}</p> : items.map(item => {
          const isSel = selectedPaths.includes(item.path);
          return (
            <button key={item.path} onClick={() => handleItemClick(item)} className={`w-full flex items-center gap-4 px-4 py-4 rounded-2xl border btn-touch transition-all ${isSel ? 'bg-[#3bb5ff]/20 border-[#3bb5ff] text-white' : item.is_dir ? 'text-[#3bb5ff] bg-[#0f1f3a]/40 border-[#1a3a5c]' : 'text-gray-300 bg-[#060d1a] border-[#1a3a5c]'}`}>
              <span className={isSel ? 'text-white' : item.is_dir ? 'text-[#3bb5ff]' : 'text-gray-500'}>
                {isSel ? Ico.check : item.is_dir ? Ico.folder : Ico.file}
              </span>
              <span className="text-sm font-medium truncate flex-1 text-left">{item.name === '..' ? 'Parent Directory' : item.name}</span>
              {multiSelect && !item.is_dir && item.name !== '..' && (
                <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${isSel ? 'bg-[#3bb5ff] border-[#3bb5ff]' : 'border-gray-600'}`}>
                  {isSel && <div className="w-2 h-2 bg-white rounded-full" />}
                </div>
              )}
            </button>
          )
        })}
      </div>
      <div className="p-4 bg-[#0a1628] border-t border-[#1a3a5c] flex gap-3">
        {multiSelect ? (
          <button onClick={() => onSelect(selectedPaths)} disabled={selectedPaths.length === 0} className="flex-1 py-4 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-2xl font-bold btn-touch shadow-lg shadow-[#3bb5ff]/20 disabled:opacity-40 uppercase tracking-widest text-xs">Confirm ({selectedPaths.length})</button>
        ) : !showFiles ? (
          <button onClick={() => onSelect(currentPath)} className="flex-1 py-4 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-2xl font-bold btn-touch shadow-lg shadow-[#3bb5ff]/20 uppercase tracking-widest text-xs">Select Folder</button>
        ) : null}
        <button onClick={onCancel} className="px-8 py-4 bg-[#0f1f3a] text-white rounded-2xl border border-[#1a3a5c] btn-touch font-bold uppercase tracking-widest text-xs">Cancel</button>
      </div>
    </div>
  );
};


// ─────────────────── CONFIG EDITOR (MOBILE) ───────────────────
const ConfigField = ({ label, value, path, onChange }) => {
  if (typeof value === 'boolean') {
    return (
      <label className="flex items-center justify-between p-4 bg-[#060d1a] border border-[#1a3a5c] rounded-xl cursor-pointer active:bg-[#0f1f3a] transition-all">
        <span className="text-sm text-gray-300">{label}</span>
        <input
          type="checkbox"
          checked={value}
          onChange={(e) => onChange(path, e.target.checked)}
          className="w-5 h-5 accent-[#3bb5ff]"
        />
      </label>
    );
  }

  if (typeof value === 'number' || typeof value === 'string') {
    const isSecret = label.toLowerCase().includes('token') || label.toLowerCase().includes('salt');
    return (
      <div className="space-y-1.5">
        <label className="text-[10px] text-[#3bb5ff]/70 uppercase tracking-widest font-bold ml-1">{label}</label>
        <input
          type={isSecret ? "password" : (typeof value === 'number' ? "number" : "text")}
          value={value}
          onChange={(e) => onChange(path, typeof value === 'number' ? parseFloat(e.target.value) : e.target.value)}
          className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-4 py-3 text-sm focus:border-[#3bb5ff] outline-none text-gray-200"
          placeholder={`Enter ${label}...`}
        />
      </div>
    );
  }
  return null;
};

const ConfigSection = ({ title, data, path = [], onChange }) => {
  return (
    <div className="space-y-4 mb-6">
      <div className="flex items-center gap-2 pb-2 border-b border-[#1a3a5c]">
        <h3 className="text-xs font-bold text-[#3bb5ff] uppercase tracking-wider">{title}</h3>
      </div>
      <div className="space-y-4">
        {Object.entries(data).map(([key, val]) => {
          if (val !== null && typeof val === 'object' && !Array.isArray(val)) {
            return (
              <div key={key} className="pl-2 border-l border-[#1a3a5c]/50">
                <ConfigSection title={key} data={val} path={[...path, key]} onChange={onChange} />
              </div>
            );
          }
          return (
            <ConfigField
              key={key}
              label={key.replace(/_/g, ' ')}
              value={val}
              path={[...path, key]}
              onChange={onChange}
            />
          );
        })}
      </div>
    </div>
  );
};

// ─────────────────── ARCHIVE FOLDER PICKER ───────────────────
function ArchiveFolderPicker({ selectedDb, onSelect, onCancel }) {
  const [path, setPath] = useState('.')
  const [folders, setFolders] = useState([])
  const [loading, setLoading] = useState(false)
  useEffect(() => { if (selectedDb) { setLoading(true); fetch(`/api/listfiles?db=${encodeURIComponent(selectedDb)}&path=${encodeURIComponent(path)}&depth=1`).then(r => r.json()).then(d => { let f = []; if (path === '.' || path === '') { f = Object.values(d.results || {}).filter(i => i.type === 'folder').map(i => ({ name: i.name, path: i.name })) } else { const k = Object.keys(d.results || {}); if (k.length) { const t = d.results[k[0]]; if (t.contents) f = Object.values(t.contents).filter(i => i.type === 'folder').map(i => ({ name: i.name, path: `${path}/${i.name}` })) } } setFolders(f); setLoading(false) }).catch(() => setLoading(false)) } }, [selectedDb, path])
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <button onClick={() => setPath('.')} className="btn-touch text-[#3bb5ff] p-1">{Ico.home}</button>
        {path !== '.' && <button onClick={() => { const p = path.split('/'); p.pop(); setPath(p.length ? p.join('/') : '.') }} className="btn-touch text-gray-400 p-1">{Ico.back}</button>}
        <span className="text-xs text-gray-300 font-mono truncate flex-1">{path}</span>
      </div>
      <div className="max-h-48 overflow-y-auto space-y-1">
        {loading ? <p className="text-xs text-gray-500">Loading...</p> : folders.length === 0 ? <p className="text-xs text-gray-500 italic">No subfolders</p> : folders.map(f => (
          <button key={f.path} onClick={() => setPath(f.path)} className="w-full flex items-center gap-2 px-3 py-2 bg-[#0f1f3a] rounded-lg text-sm text-[#3bb5ff] btn-touch">{Ico.folderOpen}{f.name}</button>
        ))}
      </div>
      <button onClick={() => { if (onSelect) onSelect(path); else if (onCancel) onCancel(path) }} className="w-full py-3 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-xl font-bold btn-touch">Select "{path}"</button>
    </div>
  )
}

// ─────────────────── SETTINGS TAB COMPONENT (EXTRACTED TO FIX HOOKS RULES) ───────────────────
function SettingsTab({ config, fetchConfig, connectionStatus, connectWS, showToast }) {
  const [localConfig, setLocalConfig] = useState(null);
  const [downloadFolder, setDownloadFolder] = useState(localStorage.getItem('VAULT_OPUS_download_folder') || './downloads');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (config) {
      setLocalConfig(JSON.parse(JSON.stringify(config)));
      setError(null);
    } else {
      fetchConfig().catch(() => setError('Failed to load configuration'));
    }
  }, [config]);

  const handleFieldChange = (path, value) => {
    setLocalConfig(prev => {
      const updateNested = (obj, pathParts, val) => {
        const [first, ...rest] = pathParts;
        if (rest.length === 0) return { ...obj, [first]: val };
        return { ...obj, [first]: updateNested(obj[first] || {}, rest, val) };
      };
      return updateNested(prev, path, value);
    });
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(localConfig)
      });
      localStorage.setItem('VAULT_OPUS_download_folder', downloadFolder);
      showToast('Settings saved', 'success');
      await fetchConfig();
    } catch (e) { showToast('Failed to save', 'error'); }
    setSaving(false);
  };

  return (
    <div className="flex flex-col h-full bg-[#060d1a] relative w-full overflow-hidden">
      <div className="px-6 py-4 bg-[#0a1628] border-b border-[#1a3a5c] flex items-center justify-between sticky top-0 z-20">
        <h2 className="text-xl font-black text-white tracking-tight">Settings</h2>
        {connectionStatus === 'disconnected' && (
          <button onClick={connectWS} className="px-4 py-2 bg-red-500/20 border border-red-500/50 text-red-500 text-[10px] font-black rounded-full animate-pulse uppercase tracking-widest">Reconnect</button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 pb-40">
        {error ? (
          <div className="flex flex-col items-center justify-center py-20 text-center space-y-4">
            <div className="text-red-500 scale-150">{Ico.alert}</div>
            <p className="text-gray-400 text-sm font-bold uppercase tracking-widest">{error}</p>
            <button onClick={fetchConfig} className="px-8 py-4 bg-[#0f1f3a] border border-[#1a3a5c] text-[#3bb5ff] rounded-2xl font-black btn-touch uppercase text-[10px] tracking-widest">Retry Load</button>
          </div>
        ) : !localConfig ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-10 h-10 border-4 border-[#3bb5ff]/20 border-t-[#3bb5ff] rounded-full animate-spin mb-4" />
            <p className="text-[#3bb5ff] text-[10px] font-black uppercase tracking-[0.2em] animate-pulse">Syncing Config</p>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="space-y-4 mb-8 bg-[#0a1628] p-6 rounded-3xl border border-[#1a3a5c] shadow-xl">
              <div className="flex items-center gap-2 pb-3 border-b border-[#1a3a5c]">
                <h3 className="text-[10px] font-black text-[#3bb5ff] uppercase tracking-[0.2em]">Interface</h3>
              </div>
              <div className="space-y-1.5 pt-2">
                <label className="text-[10px] text-gray-500 uppercase tracking-widest font-black ml-1">Download Destination</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={downloadFolder}
                    onChange={(e) => setDownloadFolder(e.target.value)}
                    className="flex-1 bg-[#060d1a] border border-[#1a3a5c] rounded-2xl px-4 py-4 text-sm focus:border-[#3bb5ff] outline-none text-gray-200"
                    placeholder="./downloads"
                  />
                  <button className="p-4 bg-[#0f1f3a] border border-[#1a3a5c] rounded-2xl text-[#3bb5ff] btn-touch">{Ico.folderOpen}</button>
                </div>
              </div>
            </div>

            {Object.entries(localConfig).map(([section, data]) => (
              <div key={section} className="bg-[#0a1628] p-6 rounded-3xl border border-[#1a3a5c] shadow-xl">
                <ConfigSection
                  title={section}
                  data={data}
                  onChange={handleFieldChange}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {localConfig && (
        <div className="fixed bottom-24 left-6 right-6 z-30">
          <button
            onClick={saveSettings}
            disabled={saving}
            className="w-full py-5 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-3xl font-black btn-touch shadow-2xl shadow-[#3bb5ff]/30 uppercase tracking-[0.2em] text-xs"
          >
            {saving ? 'Syncing...' : 'Commit Settings'}
          </button>
        </div>
      )}
    </div>
  );
}

// ─────────────────── APP ───────────────────
export default function App() {
  const [tab, setTab] = useState('explorer')
  const [dbs, setDbs] = useState([])
  const [selectedDb, setSelectedDb] = useState(localStorage.getItem('mob_selectedDb') || '')
  const [tree, setTree] = useState(null)
  const [currentPath, setCurrentPath] = useState('.')
  const [currentVersion, setCurrentVersion] = useState(null)
  const [selectedItems, setSelectedItems] = useState([])
  const [ws, setWs] = useState(null)
  const [terminalOutput, setTerminalOutput] = useState('')
  const [queue, setQueue] = useState([])
  const [config, setConfig] = useState(null)
  const [promptData, setPromptData] = useState(null)
  const [bottomSheet, setBottomSheet] = useState(null)
  const [modal, setModal] = useState(null)
  const [showCreateVolume, setShowCreateVolume] = useState(false)
  const [externalVolumes, setExternalVolumes] = useState(() => {
    const saved = localStorage.getItem('mob_externalVolumes');
    return saved ? JSON.parse(saved) : [];
  });
  const [recentVolumes, setRecentVolumes] = useState(() => {
    const saved = localStorage.getItem('mob_recentVolumes');
    return saved ? JSON.parse(saved) : [];
  });
  const [newDbName, setNewDbName] = useState('')
  const [toast, setToast] = useState(null)
  const lastClickIdxRef = useRef(null)

  const showToast = (msg, type = 'info') => setToast({ message: msg, type, key: Date.now() })

  // WebSocket
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);

  const connectWS = () => {
    if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);

    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    // Fix: Always target port 8000 for backend if on localhost or PC IP, 
    // unless the app is being served by the backend itself (usually port 8000)
    let host = window.location.host;
    if (window.location.port === '5173') {
      host = window.location.hostname + ':8000';
    }

    setConnectionStatus('connecting');
    const socket = new WebSocket(`${proto}//${host}/ws/cli`)

    socket.onopen = () => {
      setWs(socket);
      setConnectionStatus('connected');
      reconnectAttemptsRef.current = 0;
      setTerminalOutput(p => p + '\n[Connected]\n');
    };

    socket.onmessage = e => {
      const msg = JSON.parse(e.data)
      const tid = msg.task_id
      if (msg.type === 'stdout' || msg.type === 'stderr') setTerminalOutput(p => p + msg.data)
      else if (msg.type === 'status') setQueue(q => q.map(i => i.id === tid ? { ...i, status: msg.data.includes('Queued') ? 'queued' : 'running' } : i))
      else if (msg.type === 'prompt') setPromptData({ text: msg.prompt, isPassword: msg.is_password, taskId: tid })
      else if (msg.type === 'exit') {
        setTerminalOutput(p => p + `\n[Exit ${msg.code}]\n`)
        setQueue(q => q.map(i => i.id === tid ? { ...i, status: msg.code === 0 ? 'completed' : 'failed', progress: msg.code === 0 ? 100 : i.progress } : i))
        if (msg.code === 0) showToast('Operation completed', 'success')
        else showToast('Operation failed', 'error')
        fetchFiles(currentPath)
      }
    }

    socket.onclose = () => {
      setWs(null);
      setConnectionStatus('disconnected');
      setTerminalOutput(p => p + '\n[Disconnected]\n');

      // Retry logic: up to 3 times, then stop as per original request, 
      // but user later said "until it's connected". 
      // I'll implement a 3-retry limit with a manual option, 
      // or just keep retrying if that's what "until it's connected" means.
      // Given the conflicting requests, I'll do 3 auto-retries and then show a "Reconnect" button.
      if (reconnectAttemptsRef.current < 3) {
        reconnectAttemptsRef.current += 1;
        reconnectTimeoutRef.current = setTimeout(connectWS, 3000);
      }
    }

    socket.onerror = () => {
      socket.close();
    };
  };

  useEffect(() => {
    connectWS();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (ws) ws.close(); // Crucial: close the socket on unmount
    }
  }, [])

  const sendWS = (action, args, task_id) => { if (ws?.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ action, args, task_id })) }
  const addQueue = (name, type) => { const id = `${type}-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`; setQueue(q => [...q, { id, name, status: 'queued', progress: 0 }]); return id }
  const runCmd = (args, name, type) => { const id = addQueue(name, type); sendWS('run', args, id) }

  const fetchDbs = async () => {
    try {
      const r = await fetch('/api/dbs');
      const data = await r.json();
      const availableDbs = data.dbs || [];

      setDbs(prev => {
        const all = [...availableDbs];
        externalVolumes.forEach(ext => {
          if (!all.includes(ext)) all.push(ext);
        });
        return all;
      });
    } catch (e) {
      showToast('Failed to fetch volumes', 'error')
    }
  }
  const fetchConfig = async () => { try { const r = await fetch('/api/config'); setConfig(await r.json()) } catch (e) { } }
  const fetchFiles = async (path, version) => {
    if (!selectedDb) return
    try {
      let url = `/api/listfiles?db=${encodeURIComponent(selectedDb)}&path=${encodeURIComponent(path)}`
      if (version) url += `&version=${encodeURIComponent(version)}`
      const r = await fetch(url); setTree(await r.json())
    } catch (e) { showToast('Failed to fetch files', 'error') }
  }

  useEffect(() => { fetchDbs(); fetchConfig() }, [])
  useEffect(() => {
    if (selectedDb) {
      localStorage.setItem('mob_selectedDb', selectedDb);

      // Update recent volumes
      setRecentVolumes(prev => {
        const updated = [selectedDb, ...prev.filter(db => db !== selectedDb)].slice(0, 10);
        localStorage.setItem('mob_recentVolumes', JSON.stringify(updated));
        return updated;
      });

      setCurrentVersion(null);
      fetchFiles(currentPath);
    }
  }, [selectedDb])

  const handleNavigate = (path) => { setCurrentPath(path); setSelectedItems([]); fetchFiles(path, currentVersion) }

  let items = []
  if (tree?.results) {
    const keys = Object.keys(tree.results)
    if (currentPath !== '.' && keys.length === 1) {
      const s = tree.results[keys[0]]
      if (s.type === 'folder' && s.contents) items = Object.values(s.contents).map(i => ({ ...i, displayName: i.name || i.db_name || 'Unknown', type: i.type || (i.itemid?.startsWith('d') ? 'folder' : 'file') }))
      else items = keys.map(k => ({ ...tree.results[k], itemid: k, displayName: tree.results[k].name || tree.results[k].db_name || 'Unknown', type: tree.results[k].type || (tree.results[k].itemid?.startsWith('d') ? 'folder' : 'file') }))
    } else items = keys.map(k => ({ ...tree.results[k], itemid: k, displayName: tree.results[k].name || tree.results[k].db_name || 'Unknown', type: tree.results[k].type || (tree.results[k].itemid?.startsWith('d') ? 'folder' : 'file') }))
  }

  const handleItemClick = (item, e) => {
    if (e?.metaKey || e?.ctrlKey) setSelectedItems(p => p.find(i => i.itemid === item.itemid) ? p.filter(i => i.itemid !== item.itemid) : [...p, item])
    else if (e?.shiftKey && lastClickIdxRef.current !== null) {
      const ci = items.findIndex(i => i.itemid === item.itemid)
      if (ci !== -1) { const s = Math.min(lastClickIdxRef.current, ci), en = Math.max(lastClickIdxRef.current, ci); const r = items.slice(s, en + 1); setSelectedItems(p => { const n = [...p]; r.forEach(x => { if (!n.find(i => i.itemid === x.itemid)) n.push(x) }); return n }) }
    } else { setSelectedItems(p => p.find(i => i.itemid === item.itemid) && p.length === 1 ? [] : [item]); lastClickIdxRef.current = items.findIndex(i => i.itemid === item.itemid) }
  }
  const handleItemDoubleClick = (item) => { if (item.type === 'folder') { const t = item.db_name || item.name; handleNavigate(currentPath === '.' ? t : `${currentPath}/${t}`) } }

  const renderExplorer = () => (
    <div className="flex flex-col h-full bg-[#060d1a]">
      <div className="flex items-center gap-1 px-3 py-2 bg-[#0a1628] border-b border-[#1a3a5c] overflow-x-auto no-scrollbar shadow-md">
        <button onClick={() => handleNavigate('.')} className={`px-3 py-1.5 text-[10px] font-bold rounded-lg btn-touch whitespace-nowrap transition-all ${currentPath === '.' ? 'bg-[#3bb5ff] text-[#0a1628]' : 'bg-[#0f1f3a] text-gray-400 border border-[#1a3a5c]'}`}>ROOT</button>
        {currentPath !== '.' && currentPath.split('/').map((part, i, arr) => (
          <React.Fragment key={i}>
            <span className="text-gray-700 font-bold text-[10px]">/</span>
            <button onClick={() => handleNavigate(arr.slice(0, i + 1).join('/'))} className={`px-3 py-1.5 text-[10px] font-bold rounded-lg btn-touch whitespace-nowrap transition-all ${i === arr.length - 1 ? 'bg-[#3bb5ff]/20 text-[#3bb5ff] border border-[#3bb5ff]/40' : 'bg-[#0f1f3a] text-gray-400'}`}>{part.toUpperCase()}</button>
          </React.Fragment>
        ))}
        {currentVersion && (
          <button onClick={() => { setCurrentVersion(null); fetchFiles(currentPath) }} className="ml-2 px-3 py-1.5 text-[9px] bg-orange-500/20 border border-orange-500/50 rounded-full text-orange-400 font-black btn-touch animate-pulse whitespace-nowrap">V: {currentVersion} ✕</button>
        )}
      </div>

      <div className="flex gap-2 px-3 py-3 bg-[#0a1628] border-b border-[#1a3a5c] overflow-x-auto no-scrollbar shadow-inner items-center">
        <button onClick={() => setBottomSheet({ title: 'Upload Files', content: <UploadForm /> })} className="flex items-center justify-center p-3 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-xl btn-touch shadow-lg shadow-[#3bb5ff]/20 min-w-[52px]">
          {React.cloneElement(Ico.upload, { className: 'w-8 h-8' })}
        </button>
        <button onClick={() => { if (selectedItems.length) setBottomSheet({ title: 'Download Options', content: <DownloadForm /> }) }} disabled={!selectedItems.length} className="flex items-center justify-center p-3 bg-[#0f1f3a] border border-[#1a3a5c] text-gray-300 rounded-xl btn-touch disabled:opacity-40 min-w-[52px]">
          {React.cloneElement(Ico.download, { className: 'w-8 h-8' })}
        </button>
        <button onClick={() => { if (selectedItems.length) setBottomSheet({ title: 'Delete Items', content: <DeleteForm /> }) }} disabled={!selectedItems.length} className="flex items-center justify-center p-3 bg-red-900/20 border border-red-900/40 text-red-400 rounded-xl btn-touch disabled:opacity-40 min-w-[52px]">
          {React.cloneElement(Ico.trash, { className: 'w-8 h-8' })}
        </button>
        <button onClick={() => setBottomSheet({ title: 'New Folder', content: <MakeFolderForm /> })} className="flex items-center justify-center p-3 bg-[#0f1f3a] border border-[#1a3a5c] text-gray-300 rounded-xl btn-touch min-w-[52px]">
          {React.cloneElement(Ico.newFolder, { className: 'w-8 h-8' })}
        </button>
        <button onClick={() => { setSelectedItems([...items]); lastClickIdxRef.current = null }} disabled={!items.length} className="flex items-center justify-center p-3 bg-[#0f1f3a] border border-[#1a3a5c] text-gray-300 rounded-xl btn-touch disabled:opacity-40 min-w-[52px]">
          {React.cloneElement(Ico.selectAll, { className: 'w-8 h-8' })}
        </button>
        <button onClick={() => { if (selectedItems.length) setBottomSheet({ title: 'Item Options', content: <ItemOptionsMenu /> }) }} disabled={!selectedItems.length} className="flex items-center justify-center p-3 bg-[#0f1f3a] border border-[#1a3a5c] text-gray-300 rounded-xl btn-touch disabled:opacity-40 min-w-[52px]">
          {React.cloneElement(Ico.menu, { className: 'w-8 h-8' })}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 pb-32 custom-scrollbar">
        {items.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-600 opacity-40 py-20">
            <div className="mb-6 scale-150">{Ico.folder}</div>
            <p className="text-sm font-bold uppercase tracking-widest">Folder is empty</p>
            <p className="text-[10px] mt-2 font-mono">TAP UPLOAD TO ADD CONTENT</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            {items.map((item, idx) => {
              const isSelected = selectedItems.find(i => i.itemid === item.itemid)
              const isFolder = item.type === 'folder'
              return (
                <div key={idx} onClick={() => handleItemClick(item)} onDoubleClick={() => handleItemDoubleClick(item)}
                  className={`flex flex-col items-center justify-center p-6 rounded-3xl border transition-all duration-200 btn-touch aspect-square relative
                    ${isSelected ? 'bg-[#3bb5ff]/20 border-[#3bb5ff] shadow-lg shadow-[#3bb5ff]/10 scale-[0.98]' : 'bg-[#0a1628]/60 border-[#1a3a5c] hover:border-[#3bb5ff]/40'}`}>
                  {isSelected && <div className="absolute top-3 right-3 w-6 h-6 bg-[#3bb5ff] text-[#0a1628] rounded-full flex items-center justify-center border-2 border-[#0a1628] z-10">{Ico.check}</div>}
                  <div className={`mb-3 transition-transform ${isSelected ? 'scale-110' : ''}`}>
                    {isFolder ? React.cloneElement(Ico.folder, { className: 'w-16 h-16' }) : React.cloneElement(Ico.file, { className: 'w-16 h-16' })}
                  </div>
                  <div className={`text-xs font-bold text-center truncate w-full px-2 ${isSelected ? 'text-white' : 'text-gray-400'}`}>{item.displayName}</div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {selectedItems.length > 0 && (
        <div className="fixed bottom-24 left-4 right-4 bg-[#0a1628]/95 backdrop-blur-xl border border-[#3bb5ff]/40 px-6 py-4 rounded-3xl flex items-center justify-between z-40 shadow-2xl animate-in slide-in-from-bottom-4 duration-300">
          <div>
            <span className="text-xs text-[#3bb5ff] font-black uppercase tracking-widest">{selectedItems.length} SELECTED</span>
          </div>
          <div className="flex gap-4">
            <button onClick={() => setBottomSheet({ title: 'Download Options', content: <DownloadForm /> })} className="p-3 bg-[#3bb5ff]/10 text-[#3bb5ff] rounded-xl btn-touch border border-[#3bb5ff]/20">{Ico.download}</button>
            <button onClick={() => setBottomSheet({ title: 'Delete Items', content: <DeleteForm /> })} className="p-3 bg-red-900/20 text-red-400 rounded-xl btn-touch border border-red-500/30">{Ico.trash}</button>
            <button onClick={() => setBottomSheet({ title: 'Item Options', content: <ItemOptionsMenu /> })} className="p-3 bg-[#0f1f3a] text-gray-300 rounded-xl btn-touch border border-[#1a3a5c]">{Ico.menu}</button>
            <button onClick={() => setSelectedItems([])} className="p-3 text-gray-500 btn-touch hover:text-white">{Ico.close}</button>
          </div>
        </div>
      )}
    </div>
  )


  // ─────────────────── VOLUMES TAB ───────────────────
  const renderVolumes = () => (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 bg-[#0a1628] border-b border-[#1a3a5c] flex items-center justify-between shadow-sm">
        <h2 className="text-lg font-bold text-white">Volumes</h2>
        <div className="flex gap-2">
          <button onClick={() => setBottomSheet({ title: 'Sharables Explorer', content: <SharablesView /> })} className="p-2 bg-[#0f1f3a] border border-[#1a3a5c] text-gray-300 rounded-xl btn-touch" title="Sharables">{Ico.share}</button>
          <button onClick={() => { setNewDbName(''); setShowCreateVolume(true) }} className="p-2 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-xl btn-touch shadow-lg shadow-[#3bb5ff]/20" title="New Volume">{Ico.plus}</button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-6">
        {/* Recent Volumes */}
        {recentVolumes.length > 0 && (
          <section>
            <div className="flex items-center gap-2 px-1 mb-3">
              <span className="text-[#3bb5ff]/50">{Ico.clock}</span>
              <h3 className="text-[10px] uppercase font-bold text-[#3bb5ff]/50 tracking-widest">Recent</h3>
            </div>
            <div className="space-y-2">
              {recentVolumes.map(db => (
                <div key={'recent-' + db} onClick={() => { setSelectedDb(db); setTab('explorer') }}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl border btn-touch transition-all ${selectedDb === db ? 'bg-[#3bb5ff]/15 border-[#3bb5ff] shadow-[0_0_15px_rgba(59,181,255,0.1)]' : 'bg-[#0f1f3a]/40 border-[#1a3a5c]'}`}>
                  <span className={selectedDb === db ? 'text-[#3bb5ff]' : 'text-gray-500'}>{Ico.cube}</span>
                  <div className="flex-1 min-w-0">
                    <div className={`text-sm font-bold truncate ${selectedDb === db ? 'text-white' : 'text-gray-300'}`}>{db.replace('.db', '')}</div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* All Volumes */}
        <section>
          <div className="flex items-center justify-between px-1 mb-3">
            <div className="flex items-center gap-2">
              <span className="text-[#3bb5ff]/50">{Ico.cube}</span>
              <h3 className="text-[10px] uppercase font-bold text-[#3bb5ff]/50 tracking-widest">Available</h3>
            </div>
            <div className="flex gap-2">
              <button onClick={() => setBottomSheet({ title: 'Add External Volume', content: <RemoteFolderPicker showFiles onSelect={p => { if (p.endsWith('.db')) { setExternalVolumes(prev => { const n = [...new Set([...prev, p])]; localStorage.setItem('mob_externalVolumes', JSON.stringify(n)); return n; }); fetchDbs(); setBottomSheet(null); showToast('Added volume', 'success'); } else { showToast('Must be a .db file', 'error'); } }} onCancel={() => setBottomSheet(null)} /> })} className="text-[10px] text-[#3bb5ff] font-bold btn-touch uppercase">+ Add External</button>
            </div>
          </div>

          {dbs.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-8 bg-[#0f1f3a]/20 border border-dashed border-[#1a3a5c] rounded-2xl text-gray-500">
              <p className="text-xs">No volumes found</p>
            </div>
          ) : (
            <div className="space-y-2">
              {dbs.map(db => (
                <div key={db} onClick={() => { setSelectedDb(db); setTab('explorer') }}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl border btn-touch transition-all ${selectedDb === db ? 'bg-[#3bb5ff]/15 border-[#3bb5ff] shadow-[0_0_15px_rgba(59,181,255,0.1)]' : 'bg-[#0f1f3a]/40 border-[#1a3a5c]'}`}>
                  <span className={selectedDb === db ? 'text-[#3bb5ff]' : 'text-gray-500'}>{Ico.cube}</span>
                  <div className="flex-1 min-w-0">
                    <div className={`text-sm font-bold truncate ${selectedDb === db ? 'text-white' : 'text-gray-300'}`}>{db.replace('.db', '')}</div>
                    <div className="text-[10px] text-gray-500 truncate">{db}</div>
                  </div>
                  <button onClick={e => { e.stopPropagation(); setBottomSheet({ title: 'Volume Options', content: <VolumeOptions db={db} /> }) }} className="p-2 text-gray-500 hover:text-white transition-colors">{Ico.menu}</button>
                </div>
              ))}
            </div>
          )}
        </section>

        <button onClick={() => setModal({ title: 'Import Package (.vov)', content: <ImportForm /> })} className="w-full py-4 bg-[#0f1f3a] border border-[#1a3a5c] rounded-2xl text-xs text-gray-300 font-bold uppercase tracking-widest btn-touch flex items-center justify-center gap-2">
          {Ico.import} Import VOV Package
        </button>
      </div>
    </div>
  )


  // ─────────────────── QUEUE ───────────────────
  const renderQueue = () => (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 bg-[#0a1628] border-b border-[#1a3a5c] flex items-center justify-between">
        <h2 className="text-lg font-bold text-white">Queue</h2>
        <button onClick={() => setQueue([])} className="text-xs text-gray-400 btn-touch">Clear All</button>
      </div>
      <div className="flex-1 overflow-y-auto p-3">
        {queue.length === 0 ? <div className="flex items-center justify-center h-full text-gray-500 text-sm">No active tasks</div> : (
          <div className="space-y-2">
            {[...queue].reverse().map(item => (
              <div key={item.id} className="flex items-center gap-3 px-3 py-2 bg-[#0a1628] border border-[#1a3a5c] rounded-xl">
                <div className={`w-2 h-2 rounded-full ${item.status === 'completed' ? 'bg-green-400' : item.status === 'failed' ? 'bg-red-400' : item.status === 'running' ? 'bg-[#3bb5ff] animate-pulse' : 'bg-gray-500'}`} />
                <div className="flex-1 min-w-0"><div className="text-xs text-gray-200 truncate">{item.name}</div><div className="text-[10px] text-gray-500 capitalize">{item.status}</div></div>
                {item.progress > 0 && <div className="text-xs text-[#3bb5ff]">{item.progress}%</div>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )

  // ─────────────────── TERMINAL ───────────────────
  const renderTerminal = () => (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 bg-[#0a1628] border-b border-[#1a3a5c] flex items-center justify-between">
        <h2 className="text-lg font-bold text-white">Terminal</h2>
        <button onClick={() => setTerminalOutput('')} className="text-xs text-gray-400 btn-touch">Clear</button>
      </div>
      <div className="flex-1 overflow-y-auto p-3 bg-[#060d1a]">
        <pre className="text-xs text-green-400 font-mono whitespace-pre-wrap break-all">{terminalOutput || 'No output yet'}</pre>
      </div>
    </div>
  )

  // ─────────────────── FORMS ───────────────────
  const UploadForm = () => {
    const [localPaths, setLocalPaths] = useState([])
    const [encryption, setEncryption] = useState('automatic')
    const [password, setPassword] = useState('')
    const [randomSeed, setRandomSeed] = useState(false)
    const [zeroKnowledge, setZeroKnowledge] = useState(false)
    const [uploadName, setUploadName] = useState('')
    const [newVersionString, setNewVersionString] = useState('')
    const [strictness, setStrictness] = useState('NA')
    const [chunkSize, setChunkSize] = useState('')
    const [minimize, setMinimize] = useState(false)
    const [nameCheck, setNameCheck] = useState(true)
    const [showPassword, setShowPassword] = useState(false)

    const genPass = () => {
      const c = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+";
      return Array.from(crypto.getRandomValues(new Uint32Array(24))).map(x => c[x % c.length]).join('')
    }

    const startUpload = () => {
      if (localPaths.length === 0) { showToast('Select at least one file', 'error'); return }

      let finalPassword = password;
      if (encryption === 'not_automatic' && randomSeed && !showPassword) {
        const p = genPass();
        setPassword(p);
        setShowPassword(true);
        return;
      }

      localPaths.forEach(path => {
        const enc = minimize && encryption === 'not_automatic' ? 'automatic' : encryption
        const args = ['upload', path, '-db', selectedDb, '-c', config?.discord?.channel_id || '', '--encryption_mode', enc]

        if (enc === 'not_automatic') {
          if (!finalPassword && !randomSeed) { showToast('Password required', 'error'); return }
          args.push('--password_seed', finalPassword)
        }

        if (uploadName) args.push('--upload_name', uploadName)
        if (newVersionString) args.push('--new_version_string', newVersionString)
        if (strictness !== 'NA') args.push('--strictness_mode', strictness)
        if (chunkSize) args.push('--chunk_size_mb', chunkSize)
        if (minimize) args.push('--minimize', 'yes')
        if (!nameCheck) args.push('--no_name_check')
        args.push('--save_hash', encryption === 'not_automatic' && zeroKnowledge ? 'False' : 'True')

        runCmd(args, path.split(/[/\\]/).pop(), 'upload')
      });

      setBottomSheet(null)
      showToast(`${localPaths.length} upload(s) queued`, 'success')
    }

    return (
      <div className="space-y-5 pb-6">
        <div>
          <label className="text-[11px] text-[#3bb5ff] uppercase tracking-widest font-bold mb-2 block">Source Files ({localPaths.length})</label>
          <div className="flex gap-2">
            <div className="flex-1 bg-[#060d1a] border border-[#1a3a5c] rounded-2xl px-4 py-4 text-sm text-gray-400 italic truncate overflow-hidden">
              {localPaths.length > 0 ? localPaths.map(p => p.split(/[/\\]/).pop()).join(', ') : 'No files selected'}
            </div>
            <button onClick={() => setBottomSheet({ title: 'Browse Files', content: <RemoteFolderPicker initialPath="" showFiles multiSelect onSelect={p => { setLocalPaths(p); setBottomSheet(null); }} onCancel={() => setBottomSheet(null)} /> })} className="p-4 bg-[#0f1f3a] border border-[#1a3a5c] rounded-2xl text-[#3bb5ff] btn-touch shadow-lg">{Ico.folderOpen}</button>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-[11px] text-[#3bb5ff] uppercase tracking-widest font-bold mb-2 block">Encryption</label>
            <select value={encryption} onChange={e => setEncryption(e.target.value)} disabled={minimize} className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-2xl px-4 py-4 text-sm text-gray-200 outline-none focus:border-[#3bb5ff]">
              <option value="automatic">Automatic</option>
              <option value="off">Off</option>
              <option value="not_automatic">Password</option>
            </select>
          </div>
          <div>
            <label className="text-[11px] text-[#3bb5ff] uppercase tracking-widest font-bold mb-2 block">Strictness</label>
            <select value={strictness} onChange={e => setStrictness(e.target.value)} className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-2xl px-4 py-4 text-sm text-gray-200 outline-none focus:border-[#3bb5ff]">
              <option value="NA">Not Atomic</option>
              <option value="SA">Soft Atomic</option>
              <option value="HA">Hard Atomic</option>
            </select>
          </div>
        </div>


        {encryption === 'not_automatic' && (
          <div className="animate-in slide-in-from-top-2 duration-200">
            <label className="text-[10px] text-[#3bb5ff]/70 uppercase tracking-widest font-bold mb-1 block">Password Seed</label>
            <div className="flex gap-2">
              <input type="password" value={password} onChange={e => setPassword(e.target.value)} disabled={randomSeed} className="flex-1 bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm text-gray-200" />
              <button onClick={() => setRandomSeed(!randomSeed)} className={`px-4 py-3 rounded-xl text-xs font-bold border btn-touch transition-all ${randomSeed ? 'bg-[#3bb5ff]/20 border-[#3bb5ff] text-white' : 'bg-[#0f1f3a] border-[#1a3a5c] text-gray-400'}`}>Random</button>
            </div>
            {showPassword && (
              <div className="mt-3 bg-green-900/20 border border-green-500/30 rounded-xl p-3 animate-in zoom-in-95">
                <p className="text-[10px] text-green-400 uppercase font-bold mb-1">Generated Password (SAVE THIS!)</p>
                <div className="flex items-center justify-between gap-2">
                  <code className="text-xs text-white font-mono break-all">{password}</code>
                  <button onClick={() => { navigator.clipboard?.writeText(password); showToast('Copied!', 'success') }} className="p-2 text-[#3bb5ff] btn-touch">{Ico.copy}</button>
                </div>
              </div>
            )}
          </div>
        )}

        <div className="h-[1px] bg-[#1a3a5c] my-1" />

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-1 block">Custom Name</label>
            <input type="text" value={uploadName} onChange={e => setUploadName(e.target.value)} placeholder="Optional" maxLength={60} className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm text-gray-200" />
          </div>
          <div>
            <label className="text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-1 block">Version Str</label>
            <input type="text" value={newVersionString} onChange={e => setNewVersionString(e.target.value)} placeholder="e.g. 1.0.0" className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm text-gray-200" />
          </div>
        </div>

        <div>
          <label className="text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-1 block">Chunk Size (MB)</label>
          <input type="number" step="0.1" min="1" max="50" value={chunkSize} onChange={e => setChunkSize(e.target.value)} placeholder="Auto (5-10MB)" className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm text-gray-200" />
        </div>

        <div className="flex flex-wrap gap-4 pt-2">
          <label className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" checked={nameCheck} onChange={e => setNameCheck(e.target.checked)} className="w-5 h-5 accent-[#3bb5ff]" />
            <span className="text-xs text-gray-300 font-medium">Name Check</span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" checked={minimize} onChange={e => setMinimize(e.target.checked)} className="w-5 h-5 accent-[#3bb5ff]" />
            <span className="text-xs text-gray-300 font-medium">Minimize</span>
          </label>
          {encryption === 'not_automatic' && (
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" checked={zeroKnowledge} onChange={e => setZeroKnowledge(e.target.checked)} disabled={minimize} className="w-5 h-5 accent-[#3bb5ff]" />
              <span className="text-xs text-gray-300 font-medium">Zero-Knowledge</span>
            </label>
          )}
        </div>

        <button onClick={startUpload} disabled={localPaths.length === 0 || !selectedDb} className="w-full py-5 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-2xl font-black btn-touch shadow-lg shadow-[#3bb5ff]/30 uppercase tracking-widest text-xs mt-2 disabled:opacity-40">
          {showPassword ? 'Confirm & Queue' : `Queue ${localPaths.length} Upload(s)`}
        </button>
      </div>
    )
  }



  const DownloadForm = () => {
    const [strictness, setStrictness] = useState('NA')
    const [allVersions, setAllVersions] = useState(false)
    return (
      <div className="space-y-4">
        <p className="text-sm text-gray-400">Download {selectedItems.length} item(s)</p>
        <div><label className="text-xs text-gray-500 uppercase mb-1 block">Strictness</label><select value={strictness} onChange={e => setStrictness(e.target.value)} className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-lg px-3 py-2 text-sm text-gray-200"><option value="NA">Not Atomic</option><option value="SA">Soft Atomic</option><option value="HA">Hard Atomic</option></select></div>
        <label className="flex items-center gap-2"><input type="checkbox" checked={allVersions} onChange={e => setAllVersions(e.target.checked)} className="accent-[#3bb5ff]" /><span className="text-sm text-gray-400">All versions</span></label>
        <button onClick={() => { selectedItems.forEach(item => { const p = currentPath === '.' ? item.displayName : `${currentPath}/${item.displayName}`; const a = ['download', p, '-db', selectedDb]; if (allVersions) a.push('--all_versions', 'yes'); if (strictness !== 'NA') a.push('--strictness_mode', strictness); runCmd(a, item.displayName, 'download') }); setBottomSheet(null); showToast('Download queued', 'success') }} className="w-full py-3 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-xl font-bold btn-touch">Download</button>
      </div>
    )
  }

  const DeleteForm = () => {
    const [type, setType] = useState('soft')
    const [scope, setScope] = useState('latest')
    const [ver, setVer] = useState('')
    const [startVer, setStartVer] = useState('')
    const [endVer, setEndVer] = useState('')

    return (
      <div className="space-y-4">
        <p className="text-sm text-gray-400">Delete {selectedItems.length} item(s). This cannot be undone.</p>

        <div>
          <label className="text-xs text-gray-500 uppercase mb-1 block">Delete Type</label>
          <div className="flex gap-2">
            <button onClick={() => setType('soft')} className={`flex-1 py-2 rounded-lg text-xs border btn-touch ${type === 'soft' ? 'bg-[#3bb5ff]/10 border-[#3bb5ff] text-white' : 'bg-[#0f1f3a] border-[#1a3a5c] text-gray-400'}`}>Soft (Metadata Only)</button>
            <button onClick={() => setType('hard')} className={`flex-1 py-2 rounded-lg text-xs border btn-touch ${type === 'hard' ? 'bg-red-900/20 border-red-500 text-red-400' : 'bg-[#0f1f3a] border-[#1a3a5c] text-gray-400'}`}>Hard (Disk Wipe)</button>
          </div>
        </div>

        <div>
          <label className="text-xs text-gray-500 uppercase mb-1 block">Version Scope</label>
          <div className="grid grid-cols-2 gap-2">
            {['latest', 'all', 'specific', 'range'].map(s => (
              <button key={s} onClick={() => setScope(s)} className={`py-2 rounded-lg text-xs border btn-touch capitalize ${scope === s ? 'bg-[#3bb5ff]/10 border-[#3bb5ff] text-white' : 'bg-[#0f1f3a] border-[#1a3a5c] text-gray-400'}`}>{s}</button>
            ))}
          </div>
        </div>

        {scope === 'specific' && (
          <input type="text" value={ver} onChange={e => setVer(e.target.value)} placeholder="Version (e.g. 0.0.0.1)" className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-lg px-3 py-2 text-sm text-gray-200" />
        )}

        {scope === 'range' && (
          <div className="flex gap-2">
            <input type="text" value={startVer} onChange={e => setStartVer(e.target.value)} placeholder="Start Version" className="flex-1 bg-[#060d1a] border border-[#1a3a5c] rounded-lg px-3 py-2 text-sm text-gray-200" />
            <input type="text" value={endVer} onChange={e => setEndVer(e.target.value)} placeholder="End Version" className="flex-1 bg-[#060d1a] border border-[#1a3a5c] rounded-lg px-3 py-2 text-sm text-gray-200" />
          </div>
        )}

        <button onClick={() => {
          selectedItems.forEach(item => {
            const a = ['delete'];
            if (item.itemid) a.push(item.itemid, '--id_based');
            else a.push(currentPath === '.' ? item.displayName : `${currentPath}/${item.displayName}`);
            a.push('-db', selectedDb, '--skip_confirmation', 'yes');
            if (type === 'hard') a.push('--hard');
            if (scope === 'all') a.push('--all_versions', 'yes');
            else if (scope === 'specific' && ver) a.push('--version', ver);
            else if (scope === 'range' && startVer && endVer) a.push('--start_version', startVer, '--end_version', endVer);
            runCmd(a, item.displayName, 'delete')
          });
          setBottomSheet(null);
          setSelectedItems([]);
          showToast('Delete queued', 'success')
        }} className="w-full py-4 bg-red-900/40 border border-red-900/60 text-red-300 rounded-xl font-bold btn-touch mt-2">Confirm Delete</button>
      </div>
    )
  }

  const MoveCopyForm = ({ type }) => {
    const [dest, setDest] = useState('.')
    const execute = () => {
      selectedItems.forEach(item => {
        const a = [type === 'move' ? 'move' : 'copy', '-db', selectedDb]
        if (item.itemid) a.push(item.itemid, '--id_based')
        else a.push(currentPath === '.' ? item.displayName : `${currentPath}/${item.displayName}`)
        a.push(dest)
        runCmd(a, item.displayName, type)
      })
      setBottomSheet(null); setSelectedItems([])
    }
    return (
      <div className="space-y-4">
        <div><label className="text-xs text-gray-500 uppercase mb-1 block">Destination</label><div className="flex gap-2"><input type="text" value={dest} onChange={e => setDest(e.target.value)} placeholder="Path or . for root" className="flex-1 bg-[#060d1a] border border-[#1a3a5c] rounded-lg px-3 py-2 text-sm text-gray-200" /><button onClick={() => setBottomSheet({ title: 'Folders', content: <ArchiveFolderPicker selectedDb={selectedDb} onSelect={p => { setDest(p); setBottomSheet({ title: 'Move / Copy', content: <MoveCopyForm type={type} /> }) }} onCancel={() => setBottomSheet({ title: 'Move / Copy', content: <MoveCopyForm type={type} /> })} /> })} className="px-3 py-2 bg-[#0f1f3a] border border-[#1a3a5c] rounded-lg text-xs text-gray-300 btn-touch">{Ico.folderOpen}</button></div></div>
        <button onClick={execute} className="w-full py-3 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-xl font-bold btn-touch uppercase">{type}</button>
      </div>
    )
  }

  const ItemOptionsMenu = ({ item = selectedItems[0] }) => {
    if (!item) return <div className="p-4 text-gray-500">No item selected</div>;
    return (
      <div className="space-y-2">
        <button onClick={() => { setBottomSheet(null); setModal({ title: 'Item Details', content: <FullNameInfo item={item} /> }) }} className="w-full flex items-center gap-3 px-4 py-3 bg-[#0f1f3a] rounded-xl text-sm text-gray-300 btn-touch">{Ico.info} Full Details</button>
        <button onClick={() => { setBottomSheet(null); setModal({ title: 'Upload New Version', content: <NewVersionForm item={item} /> }) }} className="w-full flex items-center gap-3 px-4 py-3 bg-[#0f1f3a] rounded-xl text-sm text-gray-300 btn-touch">{Ico.plus} Upload New Version</button>
        <button onClick={() => { setBottomSheet(null); setModal({ title: 'Rename Item', content: <RenameItemForm item={item} /> }) }} className="w-full flex items-center gap-3 px-4 py-3 bg-[#0f1f3a] rounded-xl text-sm text-gray-300 btn-touch">{Ico.rename} Rename Item</button>
        <button onClick={() => { setBottomSheet(null); setBottomSheet({ title: `Move / Copy`, content: <MoveCopyForm type="move" /> }) }} className="w-full flex items-center gap-3 px-4 py-3 bg-[#0f1f3a] rounded-xl text-sm text-gray-300 btn-touch">{Ico.move} Move / Copy</button>
        <button onClick={() => { setBottomSheet(null); handleSeeVersions() }} className="w-full flex items-center gap-3 px-4 py-3 bg-[#0f1f3a] rounded-xl text-sm text-gray-300 btn-touch">{Ico.clock} See Versions</button>
        <button onClick={() => { setBottomSheet(null); handleDownloadVersion() }} className="w-full flex items-center gap-3 px-4 py-3 bg-[#0f1f3a] rounded-xl text-sm text-gray-300 btn-touch">{Ico.download} Download Version</button>
        <div className="h-[1px] bg-[#1a3a5c] my-1" />
        <button onClick={() => { setBottomSheet(null); setBottomSheet({ title: 'Delete Confirmation', content: <DeleteForm /> }) }} className="w-full flex items-center gap-3 px-4 py-3 bg-red-900/10 border border-red-900/20 rounded-xl text-sm text-red-400 btn-touch">{Ico.trash} Delete</button>
      </div>
    );
  };

  const RenameItemForm = ({ item }) => {
    const [name, setName] = useState(item.displayName)
    const execute = () => {
      const a = ['modify', '--rename', name, '-db', selectedDb]
      if (item.itemid) a.push(item.itemid, '--id_based')
      else a.push(currentPath === '.' ? item.displayName : `${currentPath}/${item.displayName}`)
      runCmd(a, item.displayName, 'rename')
      setModal(null)
    }
    return (
      <div className="space-y-3">
        <label className="text-xs text-gray-500 uppercase">New Name</label>
        <input type="text" value={name} onChange={e => setName(e.target.value)} className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-[#3bb5ff]" />
        <button onClick={execute} className="w-full py-4 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-xl font-bold btn-touch shadow-lg shadow-[#3bb5ff]/20">Confirm Rename</button>
      </div>
    )
  }

  const NewVersionForm = ({ item }) => {
    const [localPath, setLocalPath] = useState('')
    const [mode, setMode] = useState('addition')
    const [encryption, setEncryption] = useState('automatic')
    const [password, setPassword] = useState('')
    const [randomSeed, setRandomSeed] = useState(false)
    const [zeroKnowledge, setZeroKnowledge] = useState(false)
    const [newVersionString, setNewVersionString] = useState('')
    const [uploadName, setUploadName] = useState('')
    const [strictness, setStrictness] = useState('NA')
    const [chunkSize, setChunkSize] = useState('')
    const [minimize, setMinimize] = useState(false)
    const [nameCheck, setNameCheck] = useState(true)
    const [sourceVersion, setSourceVersion] = useState('')
    const [availableVersions, setAvailableVersions] = useState([])
    const [isLoadingVersions, setIsLoadingVersions] = useState(false)
    const [showPassword, setShowPassword] = useState(false)

    useEffect(() => {
      const path = currentPath === '.' ? item.displayName : `${currentPath}/${item.displayName}`
      setIsLoadingVersions(true)
      fetch(`/api/listfiles?db=${encodeURIComponent(selectedDb)}&path=${encodeURIComponent(path)}`)
        .then(r => r.json())
        .then(d => {
          let itemid = null
          if (d.results) { const k = Object.keys(d.results); if (k.length) itemid = k[0] }
          if (itemid) return fetch(`/api/listfiles?db=${encodeURIComponent(selectedDb)}&itemid=${encodeURIComponent(itemid)}`).then(r => r.json())
          throw new Error('No ID')
        })
        .then(vd => {
          const v = vd?.results ? Object.keys(vd.results).filter(k => k.includes('.')) : []
          setAvailableVersions(v.sort().reverse())
          if (v.length > 0) setSourceVersion(v[0])
        })
        .catch(() => { })
        .finally(() => setIsLoadingVersions(false))
    }, [])

    const execute = () => {
      if (!localPath) { showToast('Select a source path', 'error'); return }

      let finalPassword = password;
      if (encryption === 'not_automatic' && randomSeed && !showPassword) {
        const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+";
        const p = Array.from(crypto.getRandomValues(new Uint32Array(24))).map(x => chars[x % chars.length]).join('')
        setPassword(p);
        setShowPassword(true);
        return;
      }

      const target = item.itemid || (currentPath === '.' ? item.displayName : `${currentPath}/${item.displayName}`)
      const args = ['upload', localPath, '-db', selectedDb, '-c', config?.discord?.channel_id || '', '--target_item_path', target, '--upload_mode', 'new_version']

      const enc = minimize && encryption === 'not_automatic' ? 'automatic' : encryption
      args.push('--encryption_mode', enc)

      if (enc === 'not_automatic') {
        if (!finalPassword && !randomSeed) { showToast('Password required', 'error'); return }
        args.push('--password_seed', finalPassword)
      }

      if (mode === 'addition') args.push('--addition')
      if (sourceVersion) args.push('--source_version', sourceVersion)
      if (uploadName) args.push('--upload_name', uploadName)
      if (newVersionString) args.push('--new_version_string', newVersionString)
      if (strictness !== 'NA') args.push('--strictness_mode', strictness)
      if (chunkSize) args.push('--chunk_size_mb', chunkSize)
      if (minimize) args.push('--minimize', 'yes')
      if (!nameCheck) args.push('--no_name_check')
      args.push('--save_hash', encryption === 'not_automatic' && zeroKnowledge ? 'False' : 'True')
      if (item.itemid) args.push('--id_based')

      runCmd(args, `Update: ${item.displayName}`, 'upload')
      setModal(null)
      showToast('Update queued', 'success')
    }

    return (
      <div className="space-y-4 pb-4">
        <div className="bg-[#3bb5ff]/10 border border-[#3bb5ff]/30 p-3 rounded-xl">
          <p className="text-[10px] text-[#3bb5ff] uppercase font-bold mb-1">Targeting</p>
          <p className="text-xs text-white truncate font-mono">{item.displayName}</p>
        </div>

        <div>
          <label className="text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-1 block">Local Source File</label>
          <div className="flex gap-2">
            <input type="text" value={localPath} onChange={e => setLocalPath(e.target.value)} placeholder="/path/to/new/version" className="flex-1 bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm text-gray-200 outline-none focus:border-[#3bb5ff]" />
            <button onClick={() => setBottomSheet({ title: 'Browse Files', content: <RemoteFolderPicker initialPath={localPath} showFiles onSelect={p => { setLocalPath(p); setBottomSheet(null); }} onCancel={() => setBottomSheet(null)} /> })} className="p-3 bg-[#0f1f3a] border border-[#1a3a5c] rounded-xl text-[#3bb5ff] btn-touch">{Ico.folderOpen}</button>
          </div>
        </div>

        <div className="bg-[#0f1f3a] p-3 rounded-xl border border-[#1a3a5c] space-y-3">
          <label className="text-[10px] text-[#3bb5ff] uppercase tracking-widest font-bold block">Update Strategy</label>
          <div className="flex gap-2">
            <button onClick={() => setMode('independent')} className={`flex-1 py-3 rounded-xl text-xs font-bold border btn-touch transition-all ${mode === 'independent' ? 'bg-[#3bb5ff]/20 border-[#3bb5ff] text-white' : 'bg-[#060d1a] border-[#1a3a5c] text-gray-500'}`}>Independent</button>
            <button onClick={() => setMode('addition')} className={`flex-1 py-3 rounded-xl text-xs font-bold border btn-touch transition-all ${mode === 'addition' ? 'bg-[#3bb5ff]/20 border-[#3bb5ff] text-white' : 'bg-[#060d1a] border-[#1a3a5c] text-gray-500'}`}>Addition</button>
          </div>
          {mode === 'addition' && (
            <div className="animate-in slide-in-from-top-1 duration-200">
              <label className="text-[9px] text-gray-500 uppercase mb-1 block">Previous Version (Source)</label>
              {isLoadingVersions ? <p className="text-[10px] text-gray-600 animate-pulse">Fetching versions...</p> : (
                <select value={sourceVersion} onChange={e => setSourceVersion(e.target.value)} className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-lg px-2 py-2 text-xs text-white outline-none">
                  {availableVersions.map(v => <option key={v} value={v}>{v}</option>)}
                  {availableVersions.length === 0 && <option value="">Latest (Auto)</option>}
                </select>
              )}
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-1 block">Encryption</label>
            <select value={encryption} onChange={e => setEncryption(e.target.value)} disabled={minimize} className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm text-gray-200 outline-none">
              <option value="automatic">Automatic</option>
              <option value="off">Off</option>
              <option value="not_automatic">Password</option>
            </select>
          </div>
          <div>
            <label className="text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-1 block">Strictness</label>
            <select value={strictness} onChange={e => setStrictness(e.target.value)} className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm text-gray-200 outline-none">
              <option value="NA">Not Atomic</option>
              <option value="SA">Soft Atomic</option>
              <option value="HA">Hard Atomic</option>
            </select>
          </div>
        </div>

        {encryption === 'not_automatic' && (
          <div className="animate-in slide-in-from-top-2 duration-200">
            <div className="flex gap-2">
              <input type="password" value={password} onChange={e => setPassword(e.target.value)} disabled={randomSeed} placeholder="Password Seed" className="flex-1 bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm text-gray-200" />
              <button onClick={() => setRandomSeed(!randomSeed)} className={`px-4 py-3 rounded-xl text-xs font-bold border btn-touch transition-all ${randomSeed ? 'bg-[#3bb5ff]/20 border-[#3bb5ff] text-white' : 'bg-[#0f1f3a] border-[#1a3a5c] text-gray-400'}`}>Random</button>
            </div>
            {showPassword && (
              <div className="mt-3 bg-green-900/20 border border-green-500/30 rounded-xl p-3">
                <div className="flex items-center justify-between gap-2">
                  <code className="text-xs text-white font-mono break-all">{password}</code>
                  <button onClick={() => { navigator.clipboard?.writeText(password); showToast('Copied!', 'success') }} className="p-2 text-[#3bb5ff] btn-touch">{Ico.copy}</button>
                </div>
              </div>
            )}
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-1 block">Version Str</label>
            <input type="text" value={newVersionString} onChange={e => setNewVersionString(e.target.value)} placeholder="e.g. 2.0" className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm text-gray-200" />
          </div>
          <div>
            <label className="text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-1 block">Chunk Size</label>
            <input type="number" step="0.1" value={chunkSize} onChange={e => setChunkSize(e.target.value)} placeholder="Auto" className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-3 py-3 text-sm text-gray-200" />
          </div>
        </div>

        <div className="flex flex-wrap gap-4 pt-2">
          <label className="flex items-center gap-3 cursor-pointer"><input type="checkbox" checked={nameCheck} onChange={e => setNameCheck(e.target.checked)} className="w-5 h-5 accent-[#3bb5ff]" /><span className="text-xs text-gray-300 font-medium">Name Check</span></label>
          <label className="flex items-center gap-3 cursor-pointer"><input type="checkbox" checked={minimize} onChange={e => setMinimize(e.target.checked)} className="w-5 h-5 accent-[#3bb5ff]" /><span className="text-xs text-gray-300 font-medium">Minimize</span></label>
        </div>

        <button onClick={execute} className="w-full py-4 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-2xl font-bold btn-touch shadow-lg shadow-[#3bb5ff]/20 uppercase tracking-widest text-xs">
          {showPassword ? 'Confirm & Start' : 'Start Update'}
        </button>
      </div>
    )
  }


  const MakeFolderForm = () => {
    const [name, setName] = useState('')
    const [parent, setParent] = useState(currentPath)
    const [showPicker, setShowPicker] = useState(false)
    return (
      <div className="space-y-4">
        {showPicker ? <ArchiveFolderPicker selectedDb={selectedDb} onSelect={p => { setParent(p); setShowPicker(false) }} onCancel={() => setShowPicker(false)} /> : (
          <>
            <div><label className="text-xs text-gray-500 uppercase mb-1 block">Parent</label><div className="flex gap-2"><input type="text" value={parent} onChange={e => setParent(e.target.value)} className="flex-1 bg-[#060d1a] border border-[#1a3a5c] rounded-lg px-3 py-2 text-sm text-gray-200" /><button onClick={() => setShowPicker(true)} className="px-3 py-2 bg-[#0f1f3a] border border-[#1a3a5c] rounded-lg text-xs text-gray-300 btn-touch">{Ico.folderOpen}</button></div></div>
            <div><label className="text-xs text-gray-500 uppercase mb-1 block">Folder Name</label><input type="text" value={name} onChange={e => setName(e.target.value)} placeholder="Name" maxLength={60} autoFocus className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-lg px-3 py-2 text-sm text-gray-200" /></div>
            <button onClick={() => { if (name.trim()) { runCmd(['modify', 'makefolder', name.trim(), '-db', selectedDb, '--parent', parent], name, 'makefolder'); setBottomSheet(null); showToast('Folder created', 'success') } }} disabled={!name.trim()} className="w-full py-3 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-xl font-bold btn-touch disabled:opacity-40">Create</button>
          </>
        )}
      </div>
    )
  }

  const VolumeOptions = ({ db }) => {
    const isExternal = db.includes('/') || db.includes('\\');

    return (
      <div className="space-y-2">
        <button onClick={() => { setSelectedDb(db); setBottomSheet(null); setTab('explorer') }} className="w-full flex items-center gap-3 px-4 py-3 bg-[#0f1f3a] rounded-xl text-sm text-gray-300 btn-touch">{Ico.folderOpen} Open</button>
        <button onClick={() => { setBottomSheet(null); setModal({ title: 'Rename Volume', content: <RenameVolumeForm db={db} /> }) }} className="w-full flex items-center gap-3 px-4 py-3 bg-[#0f1f3a] rounded-xl text-sm text-gray-300 btn-touch">{Ico.rename} Rename</button>
        <button onClick={async () => { try { await fetch('/api/dbs/share', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ db_name: db }) }); showToast('Volume packaged!', 'success'); setBottomSheet(null) } catch (e) { showToast(e.message, 'error') } }} className="w-full flex items-center gap-3 px-4 py-3 bg-[#0f1f3a] rounded-xl text-sm text-gray-300 btn-touch">{Ico.share} Share / Package</button>

        <div className="h-[1px] bg-[#1a3a5c] my-2" />

        <button onClick={() => { setBottomSheet(null); setModal({ title: '☢️ NUKE VOLUME', content: <NukeConfirmation db={db} /> }) }} className="w-full flex items-center gap-3 px-4 py-3 bg-red-900/10 rounded-xl text-sm text-red-500 font-bold border border-red-900/20 btn-touch">☢️ NUKE Content</button>

        {isExternal ? (
          <button onClick={() => {
            setExternalVolumes(prev => {
              const updated = prev.filter(p => p !== db);
              localStorage.setItem('mob_externalVolumes', JSON.stringify(updated));
              return updated;
            });
            setDbs(prev => prev.filter(p => p !== db));
            if (selectedDb === db) setSelectedDb('');
            setBottomSheet(null);
            showToast('Removed from list', 'success');
          }} className="w-full flex items-center gap-3 px-4 py-3 bg-[#0f1f3a] rounded-xl text-sm text-gray-300 btn-touch">{Ico.close} Remove from List</button>
        ) : null}

        <button onClick={async () => {
          if (!window.confirm(`Permanently delete ${db} from disk?`)) return;
          try {
            await fetch('/api/dbs/delete', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ db_name: db }) });
            fetchDbs();
            if (selectedDb === db) setSelectedDb('');
            showToast('Volume deleted', 'success');
            setBottomSheet(null)
          } catch (e) { showToast(e.message, 'error') }
        }} className="w-full flex items-center gap-3 px-4 py-3 bg-red-900/20 rounded-xl text-sm text-red-400 btn-touch">{Ico.trash} Delete Permanently</button>
      </div>
    )
  }

  const NukeConfirmation = ({ db }) => {
    const [confirm, setConfirm] = useState('')
    const executeNuke = async () => {
      try {
        const res = await fetch('/api/dbs/nuke', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ db_name: db })
        });
        if (!res.ok) throw new Error('Nuke failed');
        const data = await res.json();
        showToast(`Volume wiped! ${data.db_entries_deleted} entries destroyed.`, 'success');
        setModal(null);
        if (selectedDb === db) fetchFiles('.');
      } catch (e) { showToast(e.message, 'error'); }
    }
    return (
      <div className="space-y-4">
        <div className="p-4 bg-red-900/20 border border-red-500/30 rounded-xl">
          <p className="text-xs text-red-400 font-bold uppercase mb-2">Warning: Nuclear Option</p>
          <p className="text-sm text-gray-300">This will destroy ALL entries in <span className="text-white font-mono">{db}</span>. The file will remain but will be empty.</p>
        </div>
        <input type="text" value={confirm} onChange={e => setConfirm(e.target.value)} placeholder="Type 'NUKE' to confirm" className="w-full bg-[#060d1a] border border-red-900/50 rounded-xl px-4 py-3 text-sm text-white focus:border-red-500 outline-none" />
        <button onClick={executeNuke} disabled={confirm !== 'NUKE'} className="w-full py-4 bg-red-600 disabled:opacity-30 text-white rounded-xl font-bold btn-touch shadow-lg shadow-red-600/20">EXECUTE NUKE</button>
      </div>
    )
  }

  const SharablesView = () => {
    const [viewMode, setViewMode] = useState('sharables') // 'sharables', 'browse', 'downloads'
    const [items, setItems] = useState([])
    const [loading, setLoading] = useState(true)
    const [currentPath, setCurrentPath] = useState('')

    const importVov = async (path) => {
      try {
        await fetch('/api/dbs/import', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ vov_path: path }) })
        fetchDbs()
        showToast('Imported successfully', 'success')
        setBottomSheet(null)
      } catch (e) { showToast('Import failed', 'error') }
    }

    const load = async () => {
      setLoading(true)
      try {
        if (viewMode === 'sharables') {
          const r = await fetch('/api/dbs/list_sharables')
          const data = await r.json()
          setItems(data.items || [])
          setCurrentPath(data.path || 'src/SHARABLES')
        } else if (viewMode === 'downloads') {
          const path = localStorage.getItem('VAULT_OPUS_download_folder') || './downloads'
          const r = await fetch(`/api/fs/browse?path=${encodeURIComponent(path)}`)
          const data = await r.json()
          setItems(data.items.map(i => ({ ...i, is_vov: i.name.toLowerCase().endsWith('.vov') })))
          setCurrentPath(data.current_path)
        } else {
          const r = await fetch(`/api/fs/browse`)
          const data = await r.json()
          setItems(data.items.map(i => ({ ...i, is_vov: i.name.toLowerCase().endsWith('.vov') })))
          setCurrentPath(data.current_path)
        }
      } catch (e) { showToast('Failed to load items', 'error') }
      setLoading(false)
    }

    useEffect(() => { load() }, [viewMode])

    const handleBrowseSelect = (path) => {
      if (path.toLowerCase().endsWith('.vov')) importVov(path)
      else showToast('Must select a .vov file', 'error')
    }

    return (
      <div className="flex flex-col h-[70vh]">
        <div className="flex gap-1 p-1 bg-[#060d1a] border border-[#1a3a5c] rounded-xl mb-4">
          {['sharables', 'browse', 'downloads'].map(m => (
            <button key={m} onClick={() => setViewMode(m)} className={`flex-1 py-2 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all ${viewMode === m ? 'bg-[#3bb5ff] text-[#0a1628]' : 'text-gray-500'}`}>{m}</button>
          ))}
        </div>

        {viewMode === 'sharables' ? (
          <div className="flex-1 overflow-y-auto space-y-2">
            {loading ? <p className="text-center p-8 text-gray-500">Loading sharables...</p> : items.length === 0 ? <p className="text-center p-8 text-gray-500 italic">No packages found</p> : items.map(item => (
              <div key={item.path} className="flex items-center justify-between p-3 bg-[#0f1f3a] rounded-xl border border-[#1a3a5c]">
                <div className="flex items-center gap-3 overflow-hidden">
                  <span className="text-[#3bb5ff]">{item.is_dir ? Ico.folder : Ico.cube}</span>
                  <div className="truncate"><div className="text-sm text-gray-200 truncate">{item.name}</div></div>
                </div>
                {item.is_vov && <button onClick={() => importVov(item.path)} className="px-3 py-1 bg-[#3bb5ff]/20 text-[#3bb5ff] text-xs font-bold rounded-lg btn-touch">Import</button>}
              </div>
            ))}
            <button onClick={() => fetch('/api/dbs/open_sharables', { method: 'POST' })} className="w-full py-3 bg-[#0f1f3a] text-gray-300 text-xs rounded-xl border border-[#1a3a5c] btn-touch mt-4 flex items-center justify-center gap-2">{Ico.share} Open Folder on Host</button>
          </div>
        ) : (
          <div className="flex-1 flex flex-col min-h-0">
            <RemoteFolderPicker
              initialPath={currentPath}
              showFiles
              onSelect={handleBrowseSelect}
              onCancel={() => setBottomSheet(null)}
            />
          </div>
        )}
      </div>
    )
  }


  const RenameVolumeForm = ({ db }) => {
    const [name, setName] = useState(db.replace('.db', ''))
    return <div className="space-y-4"><input type="text" value={name} onChange={e => setName(e.target.value)} autoFocus className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-lg px-3 py-2 text-sm text-gray-200" /><button onClick={async () => { try { await fetch('/api/dbs/rename', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ old_name: db, new_name: name }) }); fetchDbs(); showToast('Volume renamed', 'success'); setModal(null) } catch (e) { showToast(e.message, 'error') } }} disabled={!name.trim()} className="w-full py-3 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-xl font-bold btn-touch disabled:opacity-40">Rename</button></div>
  }

  const ImportForm = () => {
    const [vovPath, setVovPath] = useState('')
    return <div className="space-y-4"><p className="text-sm text-gray-400">Import a .vov package file</p><input type="text" value={vovPath} onChange={e => setVovPath(e.target.value)} placeholder="/path/to/package.vov" className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-lg px-3 py-2 text-sm text-gray-200" /><button onClick={async () => { try { await fetch('/api/dbs/import', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ vov_path: vovPath }) }); fetchDbs(); showToast('Package imported!', 'success'); setModal(null) } catch (e) { showToast(e.message, 'error') } }} disabled={!vovPath.trim()} className="w-full py-3 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-xl font-bold btn-touch disabled:opacity-40">Import</button></div>
  }

  const FullNameInfo = ({ item }) => (
    <div className="space-y-4">
      <div className="space-y-1">
        <span className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">Display Name</span>
        <p className="text-sm text-white bg-[#060d1a] p-3 rounded-lg border border-[#1a3a5c] break-all">{item.displayName}</p>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <span className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">Item ID</span>
          <p className="text-xs text-[#3bb5ff] font-mono bg-[#060d1a] p-2 rounded-lg border border-[#1a3a5c] truncate">{item.itemid || 'N/A'}</p>
        </div>
        <div className="space-y-1">
          <span className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">Type</span>
          <p className="text-xs text-white bg-[#060d1a] p-2 rounded-lg border border-[#1a3a5c] capitalize">{item.type}</p>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <span className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">Encryption</span>
          <p className="text-xs text-white bg-[#060d1a] p-2 rounded-lg border border-[#1a3a5c] capitalize">{item.encryption_mode || 'off'}</p>
        </div>
        <div className="space-y-1">
          <span className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">Version</span>
          <p className="text-xs text-[#3bb5ff] bg-[#060d1a] p-2 rounded-lg border border-[#1a3a5c] font-bold">v{item.version || '0.0.0.1'}</p>
        </div>
      </div>
      <div className="space-y-1">
        <span className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">Timestamp</span>
        <p className="text-xs text-gray-300 bg-[#060d1a] p-3 rounded-lg border border-[#1a3a5c]">{item.upload_timestamp || 'N/A'}</p>
      </div>
      <div className="space-y-1">
        <span className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">Parts</span>
        <p className="text-xs text-gray-300 bg-[#060d1a] p-3 rounded-lg border border-[#1a3a5c]">{item.total_parts ? `${item.total_parts} part(s)` : 'N/A'}</p>
      </div>
      <button onClick={() => setModal(null)} className="w-full py-3.5 bg-[#0f1f3a] text-white rounded-xl font-bold btn-touch mt-2 border border-[#1a3a5c]">Close</button>
    </div>
  )

  // ─────────────────── VERSION VIEW ───────────────────
  const handleSeeVersions = () => {
    if (!selectedItems[0]) return
    const item = selectedItems[0]; const path = currentPath === '.' ? item.displayName : `${currentPath}/${item.displayName}`
    setModal({ title: 'Versions', wide: true, content: <VersionsView path={path} /> })
  }
  const handleDownloadVersion = () => {
    if (!selectedItems[0]) return
    const item = selectedItems[0]; const path = currentPath === '.' ? item.displayName : `${currentPath}/${item.displayName}`
    setModal({ title: 'Download Version', content: <DownloadVersionView path={path} /> })
  }

  const VersionsView = ({ path }) => {
    const [versions, setVersions] = useState([])
    const [error, setError] = useState('')
    useEffect(() => {
      fetch(`/api/listfiles?db=${encodeURIComponent(selectedDb)}&path=${encodeURIComponent(path)}`).then(r => r.json()).then(d => {
        let itemid = null
        if (d.results) { const k = Object.keys(d.results); if (k.length) itemid = k[0]; if (!itemid && d.results[k[0]]?.itemid) itemid = d.results[k[0]].itemid }
        if (itemid) return fetch(`/api/listfiles?db=${encodeURIComponent(selectedDb)}&itemid=${encodeURIComponent(itemid)}`).then(r => r.json())
        throw new Error('No itemid found')
      }).then(vd => { if (vd?.error) throw new Error(vd.error); const v = vd?.results ? Object.keys(vd.results).filter(k => k.includes('.')).map(k => ({ version: k, ...vd.results[k] })) : []; setVersions(v); if (!v.length) setError('No versions found') }).catch(e => setError(e.message))
    }, [path])
    return (
      <div className="space-y-2">
        {error ? <p className="text-sm text-red-400">{error}</p> : versions.map(v => (
          <div key={v.version} className="flex items-center justify-between px-3 py-2 bg-[#0f1f3a] rounded-lg"><span className="text-sm text-gray-200">v{v.version}</span><span className="text-xs text-gray-500">{v.upload_timestamp?.split('T')[0] || ''}</span></div>
        ))}
        <button onClick={() => setModal(null)} className="text-sm text-[#3bb5ff] text-center w-full btn-touch mt-2">Close</button>
      </div>
    )
  }

  const DownloadVersionView = ({ path }) => {
    const [ver, setVer] = useState('')
    return <div className="space-y-4"><input type="text" value={ver} onChange={e => setVer(e.target.value)} placeholder="Version (e.g. 0.0.0.1)" className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-lg px-3 py-2 text-sm text-gray-200" /><button onClick={() => { if (ver) { runCmd(['download', path, '-db', selectedDb, '--version', ver], path, 'download'); setModal(null); showToast('Download queued', 'success') } }} disabled={!ver} className="w-full py-3 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-xl font-bold btn-touch disabled:opacity-40">Download</button></div>
  }

  // ─────────────────── MAIN RENDER ───────────────────
  return (
    <div className="flex flex-col h-full safe-top bg-[#060d1a]">
      <header className="flex items-center justify-between px-6 py-4 bg-[#0a1628] border-b border-[#1a3a5c] shadow-lg z-30">
        <div className="flex items-center gap-3">
          <div className="relative">
            <img src="/logo/image.png" alt="Logo" className="w-8 h-8 object-contain drop-shadow-[0_0_8px_rgba(59,181,255,0.4)]" />
            <div className={`absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full border-2 border-[#0a1628] ${connectionStatus === 'connected' ? 'bg-green-500' : connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' : 'bg-red-500'}`} />
          </div>
          <div>
            <h1 className="text-lg font-black text-white tracking-tighter leading-none">VAULT_OPUS</h1>
            {selectedDb && <p className="text-[10px] text-[#3bb5ff] font-bold uppercase tracking-widest mt-1 opacity-80">{selectedDb.replace('.db', '')}</p>}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {connectionStatus === 'disconnected' && (
            <button onClick={connectWS} className="p-2 text-red-500 btn-touch" title="Reconnect">{Ico.alert}</button>
          )}
          {promptData && <button onClick={() => setModal({ title: 'Input Required', content: <PromptForm /> })} className="px-4 py-2 text-xs bg-yellow-500/20 border border-yellow-500/40 text-yellow-400 rounded-2xl animate-pulse btn-touch font-bold uppercase tracking-widest">Action</button>}
        </div>
      </header>

      <div className="flex-1 overflow-hidden relative">
        {tab === 'explorer' && renderExplorer()}
        {tab === 'volumes' && renderVolumes()}
        {tab === 'queue' && renderQueue()}
        {tab === 'terminal' && renderTerminal()}
        {tab === 'settings' && <SettingsTab config={config} fetchConfig={fetchConfig} connectionStatus={connectionStatus} connectWS={connectWS} showToast={showToast} />}
      </div>

      <nav className="flex items-center justify-around bg-[#0a1628] border-t border-[#1a3a5c] py-4 safe-bottom z-30 shadow-[0_-10px_30px_rgba(0,0,0,0.4)]">
        {[
          { id: 'explorer', label: 'Files', icon: Ico.folder },
          { id: 'volumes', label: 'Volumes', icon: Ico.cube },
          { id: 'queue', label: 'Queue', icon: Ico.clock, badge: queue.filter(q => q.status === 'running' || q.status === 'queued').length },
          { id: 'terminal', label: 'Terminal', icon: Ico.terminal },
          { id: 'settings', label: 'Settings', icon: Ico.settings }
        ].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} className={`flex flex-col items-center gap-2 px-2 py-1 rounded-3xl btn-touch relative transition-all active:scale-90 ${tab === t.id ? 'text-[#3bb5ff]' : 'text-gray-500'}`}>
            <div className={`p-2 rounded-2xl transition-all duration-300 ${tab === t.id ? 'bg-[#3bb5ff]/15 shadow-[0_0_15px_rgba(59,181,255,0.2)]' : 'bg-transparent'}`}>
              {React.cloneElement(t.icon, { className: 'w-8 h-8' })}
            </div>
            <span className={`text-[9px] font-black uppercase tracking-[0.1em] ${tab === t.id ? 'opacity-100' : 'opacity-40'}`}>{t.label}</span>
            {t.badge > 0 && <span className="absolute top-0 right-0 w-6 h-6 bg-[#3bb5ff] text-[10px] text-[#0a1628] rounded-full flex items-center justify-center font-black border-[3px] border-[#0a1628] shadow-lg">{t.badge}</span>}
          </button>
        ))}
      </nav>



      {bottomSheet && <Sheet open onClose={() => setBottomSheet(null)} title={bottomSheet.title}>{bottomSheet.content}</Sheet>}
      {modal && <Modal open onClose={() => setModal(null)} title={modal.title} wide={modal.wide}>{modal.content}</Modal>}

      {showCreateVolume && (
        <Modal open onClose={() => setShowCreateVolume(false)} title="Create Volume">
          <div className="space-y-4">
            <input type="text" value={newDbName} onChange={e => setNewDbName(e.target.value)} placeholder="Volume name" autoFocus className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-lg px-3 py-2 text-sm text-gray-200" />
            <button onClick={async () => { try { await fetch('/api/dbs/create', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ db_name: newDbName }) }); fetchDbs(); setShowCreateVolume(false); setSelectedDb(newDbName); setTab('explorer') } catch (e) { showToast(e.message, 'error') } }} disabled={!newDbName.trim()} className="w-full py-3 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-xl font-bold btn-touch disabled:opacity-40">Create</button>
          </div>
        </Modal>
      )}

      {toast && <Toast key={toast.key} message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

      {promptData && <PromptForm />}
    </div>
  )
  function PromptForm() {
    const [val, setVal] = useState('')
    return <Modal open onClose={() => setPromptData(null)} title={promptData?.text || 'Input Required'}><div className="space-y-4"><p className="text-sm text-gray-400">{promptData?.text}</p><input type={promptData?.isPassword ? 'password' : 'text'} value={val} onChange={e => setVal(e.target.value)} autoFocus className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-lg px-3 py-2 text-sm text-gray-200" /><button onClick={() => { sendWS('input', { data: val, task_id: promptData.taskId }); setPromptData(null) }} className="w-full py-3 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] text-white rounded-xl font-bold btn-touch">Submit</button></div></Modal>
  }
}