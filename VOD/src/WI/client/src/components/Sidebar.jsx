// Sidebar.jsx (FOR CLIENT/DESKTOP) from the VAULT OPUS PROJECT version 1-beta-release-5
// ==================== FULL CLIENT/DESKTOP GUI====================
import React, { useState, useEffect } from 'react';
import { Database, Plus, Edit2, ChevronRight, X, FolderOpen, History, LayoutGrid, Trash2, Share2, ExternalLink, RefreshCw, Bomb } from 'lucide-react';

export default function Sidebar({ dbs, recentVolumes = [], selectedDb, onSelectDb, onRenameVolume, onDeleteVolume, onRemoveFromList, onShareVolume, onOpenSharables, onRefreshDbs, onClose, onNukeVolume }) {
  const [logoError, setLogoError] = useState(false);
  const [contextMenu, setContextMenu] = useState(null);

  useEffect(() => {
    const handleClickOutside = () => setContextMenu(null);
    window.addEventListener('click', handleClickOutside);
    return () => window.removeEventListener('click', handleClickOutside);
  }, []);

  const handleContextMenu = (e, db) => {
    e.preventDefault();
    setContextMenu({
      x: e.clientX,
      y: e.clientY,
      db
    });
  };

  const renderDbItem = (db) => (
    <li key={db}>
      <button
        onClick={() => onSelectDb(db)}
        onContextMenu={(e) => handleContextMenu(e, db)}
        className={`w-full text-left px-3 py-2 rounded-md transition-all duration-200 text-sm group relative ${selectedDb === db
          ? 'bg-[#3bb5ff]/15 text-[#3bb5ff] border border-[#3bb5ff]/30 font-medium shadow-[0_0_15px_-3px_rgba(59,181,255,0.2)]'
          : 'text-gray-400 hover:bg-[#0f1f3a] hover:text-gray-200 border border-transparent'
          }`}
      >
        <div className="flex items-center gap-2">
          <Database size={14} className={selectedDb === db ? 'text-[#3bb5ff]' : 'text-gray-500'} />
          <span className="truncate flex-1">{db.replace(/\.db$/i, '')}</span>
          {selectedDb === db && <ChevronRight size={12} className="text-[#3bb5ff]/50" />}
        </div>
      </button>
    </li>
  );

  return (
    <aside className="w-72 bg-[#0a1628] border-r border-[#1a3a5c] flex flex-col h-full shadow-lg z-20 relative animate-in slide-in-from-left duration-300">
      {/* Header */}
      <div className="p-5 border-b border-[#1a3a5c] relative group">
        <div className="flex items-center gap-4">
          {!logoError ? (
            <div className="w-14 h-14 rounded-xl bg-[#060d1a] border border-[#1a3a5c] flex items-center justify-center overflow-hidden">
              <img src="/logo/image.png" className="w-full h-full object-contain" onError={() => setLogoError(true)} />
            </div>
          ) : (
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-[#3bb5ff] to-[#006fbe] flex items-center justify-center flex-shrink-0">
              <Database size={28} className="text-white" />
            </div>
          )}
          <div className="flex flex-col">
            <h1 className="text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-[#3bb5ff] to-[#ffffff] leading-tight">
              VAULT OPUS
            </h1>
            <p className="text-[10px] text-[#3bb5ff]/60 uppercase tracking-widest mt-0.5">WEB VERSION</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 hover:bg-red-500/10 hover:text-red-400 rounded-lg transition-all text-gray-500 opacity-0 group-hover:opacity-100 active:scale-90"
          title="Hide Sidebar"
        >
          <X size={18} />
        </button>
      </div>

      {/* Action Buttons */}
      <div className="p-3 border-b border-[#1a3a5c] grid grid-cols-2 gap-2">
        <button
          onClick={() => {
            const event = new CustomEvent('create-volume');
            window.dispatchEvent(event);
          }}
          className="flex flex-col items-center justify-center gap-1 py-2 bg-[#0f1f3a] hover:bg-[#1a3a5c] border border-[#1a3a5c] border-dashed rounded-lg text-[#3bb5ff] text-[10px] font-medium transition-all duration-200 active:scale-95 group"
          title="Create New Volume"
        >
          <Plus size={14} className="group-hover:rotate-90 transition-transform duration-200" />
          New
        </button>
        <button
          onClick={onOpenSharables}
          className="flex flex-col items-center justify-center gap-1 py-2 bg-[#0f1f3a] hover:bg-[#1a3a5c] border border-[#1a3a5c] border-dashed rounded-lg text-[#3bb5ff] text-[10px] font-medium transition-all duration-200 active:scale-95 group"
          title="Open Sharables Folder"
        >
          <ExternalLink size={14} />
          Sharables
        </button>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-6">
        {/* Recent Volumes Category */}
        {recentVolumes.length > 0 && (
          <section>
            <div className="flex items-center gap-2 px-3 mb-2">
              <History size={12} className="text-[#3bb5ff]/50" />
              <h2 className="text-[10px] uppercase text-[#3bb5ff]/50 font-bold tracking-widest">Recent Volumes</h2>
            </div>
            <ul className="space-y-1">
              {recentVolumes.map(db => renderDbItem(db))}
            </ul>
          </section>
        )}

        {/* Available Volumes Category */}
        <section>
          <div className="flex items-center justify-between gap-2 px-3 mb-2">
            <div className="flex items-center gap-2">
              <LayoutGrid size={12} className="text-[#3bb5ff]/50" />
              <h2 className="text-[10px] uppercase text-[#3bb5ff]/50 font-bold tracking-widest">Available Volumes</h2>
            </div>
            <button
              onClick={(e) => {
                e.currentTarget.classList.add('animate-spin');
                onRefreshDbs();
                setTimeout(() => {
                  const btn = document.querySelector('.refresh-btn');
                  if (btn) btn.classList.remove('animate-spin');
                }, 1000);
              }}
              className="refresh-btn p-1 hover:bg-[#3bb5ff]/10 text-[#3bb5ff]/50 hover:text-[#3bb5ff] rounded transition-all active:scale-90"
              title="Refresh Volume List"
            >
              <RefreshCw size={12} />
            </button>
          </div>
          <ul className="space-y-1">
            {dbs.length > 0 ? (
              dbs.map(db => renderDbItem(db))
            ) : (
              <li className="text-[10px] text-gray-600 px-3 py-4 italic text-center border border-dashed border-[#1a3a5c] rounded-lg">
                No databases found in DATABASES folder.
              </li>
            )}
          </ul>
        </section>
      </div>

      {/* Context Menu */}
      {contextMenu && (
        <div
          className="fixed z-[100] bg-[#0a1628] border border-[#1a3a5c] rounded-lg shadow-2xl py-1 w-40 animate-in fade-in zoom-in-95 duration-100"
          style={{ top: contextMenu.y, left: contextMenu.x }}
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={() => {
              onRenameVolume(contextMenu.db);
              setContextMenu(null);
            }}
            className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-gray-300 hover:bg-[#3bb5ff]/10 hover:text-[#3bb5ff] transition-colors"
          >
            <Edit2 size={12} />
            Rename
          </button>
          <button
            onClick={() => {
              onShareVolume(contextMenu.db);
              setContextMenu(null);
            }}
            className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-[#3bb5ff] hover:bg-[#3bb5ff]/10 transition-colors border-y border-[#1a3a5c]/30"
          >
            <Share2 size={12} />
            Share Volume
          </button>
          <button
            onClick={() => {
              onRemoveFromList(contextMenu.db);
              setContextMenu(null);
            }}
            className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-gray-300 hover:bg-[#3bb5ff]/10 hover:text-[#3bb5ff] transition-colors"
          >
            <X size={12} />
            Remove from List
          </button>
          {/* NUKE VOLUME BUTTON */}
          <button
            onClick={() => {
              onNukeVolume(contextMenu.db);
              setContextMenu(null);
            }}
            className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-orange-400 hover:bg-orange-500/10 transition-colors border-y border-[#1a3a5c]/30"
            title="Wipe all data from this volume (keeps the file)"
          >
            <Bomb size={12} />
            Nuke Volume
          </button>
          <button
            onClick={() => {
              onDeleteVolume(contextMenu.db);
              setContextMenu(null);
            }}
            className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-red-400 hover:bg-red-500/10 transition-colors border-t border-[#1a3a5c]/30"
          >
            <Trash2 size={12} />
            Delete
          </button>
        </div>
      )}
    </aside>
  );
}