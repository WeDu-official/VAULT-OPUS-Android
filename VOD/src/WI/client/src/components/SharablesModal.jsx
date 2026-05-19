// SharablesModal.jsx (FOR CLIENT/DESKTOP) from the VAULT OPUS PROJECT version 1-beta-release-5
// ==================== FULL CLIENT/DESKTOP GUI====================
import React, { useState, useEffect } from 'react';
import { X, Package, Loader2, Folder, ChevronRight, Search, Home, Database, Download, FileText } from 'lucide-react';

export default function SharablesModal({ isOpen, onClose, onImportPackage }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentPath, setCurrentPath] = useState('');
  const [viewMode, setViewMode] = useState('sharables'); // 'sharables', 'browse', 'downloads'

  useEffect(() => {
    if (isOpen) {
      if (viewMode === 'sharables') {
        fetchSharables();
      } else if (viewMode === 'downloads') {
        const downloadPath = localStorage.getItem('VAULT_OPUS_download_folder') || './downloads';
        fetchDirectory(downloadPath);
      } else {
        fetchDirectory('');
      }
    }
  }, [isOpen, viewMode]);

  const fetchSharables = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/dbs/list_sharables');
      const data = await response.json();
      setItems(data.items || []);
      setCurrentPath(data.path || 'src/SHARABLES');
    } catch (error) {
      console.error('Error fetching sharables:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDirectory = async (path = '') => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/fs/browse?path=${encodeURIComponent(path)}`);
      const data = await response.json();
      setCurrentPath(data.current_path);
      setItems(data.items.map(item => ({
        ...item,
        is_vov: item.name.toLowerCase().endsWith('.vov')
      })));
    } catch (error) {
      console.error('Error browsing directory:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleItemClick = (item) => {
    if (item.is_dir) {
      fetchDirectory(item.path);
    } else if (item.is_vov) {
      handleImport(item.path);
    }
  };

  const handleImport = async (path) => {
    try {
      setLoading(true);
      await onImportPackage(path);
      onClose();
    } catch (error) {
      console.error('Import failed:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[120] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-[#0a1628] border border-[#1a3a5c] rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200 flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="p-6 border-b border-[#1a3a5c] shrink-0">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-[#3bb5ff]/10 rounded-lg text-[#3bb5ff]">
                <Package className="w-5 h-5" />
              </div>
              <h2 className="text-xl font-semibold text-white">Sharables Explorer</h2>
            </div>
            <button onClick={onClose} className="p-1 hover:bg-[#0f1f3a] rounded-full transition-colors text-gray-400">
              <X className="w-6 h-6" />
            </button>
          </div>

          <div className="flex gap-2 p-1 bg-[#060d1a] rounded-xl border border-[#1a3a5c]">
            <button
              onClick={() => setViewMode('browse')}
              className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-[10px] font-bold transition-all ${viewMode === 'browse' ? 'bg-[#3bb5ff] text-[#0a1628]' : 'text-gray-400 hover:text-white hover:bg-[#0f1f3a]'}`}
            >
              <Search className="w-3.5 h-3.5" />
              System Browser
            </button>
            <button
              onClick={() => setViewMode('sharables')}
              className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-[10px] font-bold transition-all ${viewMode === 'sharables' ? 'bg-[#3bb5ff] text-[#0a1628]' : 'text-gray-400 hover:text-white hover:bg-[#0f1f3a]'}`}
            >
              <Package className="w-3.5 h-3.5" />
              src/SHARABLES Folder
            </button>
            <button
              onClick={() => setViewMode('downloads')}
              className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-[10px] font-bold transition-all ${viewMode === 'downloads' ? 'bg-[#3bb5ff] text-[#0a1628]' : 'text-gray-400 hover:text-white hover:bg-[#0f1f3a]'}`}
            >
              <Download className="w-3.5 h-3.5" />
              Downloads
            </button>
          </div>
        </div>

        {/* Path Breadcrumb for Browser */}
        {viewMode !== 'sharables' && (
          <div className="px-6 py-2 bg-[#060d1a]/50 border-b border-[#1a3a5c] flex items-center gap-3 shrink-0">
            <button onClick={() => fetchDirectory('')} className="p-1 hover:bg-[#1a3a5c] rounded text-[#3bb5ff]">
              <Home className="w-3.5 h-3.5" />
            </button>
            <div className="flex-1 overflow-hidden">
              <div className="text-[10px] text-gray-500 truncate font-mono opacity-60">
                {currentPath}
              </div>
            </div>
          </div>
        )}

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 text-gray-500 gap-3">
              <Loader2 className="w-8 h-8 animate-spin text-[#3bb5ff]" />
              <p className="text-sm font-mono tracking-wider opacity-60">Scanning Files...</p>
            </div>
          ) : items.length === 0 ? (
            <div className="text-center py-20 text-gray-500 italic flex flex-col items-center gap-4">
              <Package className="w-12 h-12 opacity-20" />
              <p>No suitable files found in this location.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-1">
              {items.filter(item => item.is_dir || item.is_vov).map((item) => (
                <div
                  key={item.path}
                  onClick={() => handleItemClick(item)}
                  className={`flex items-center gap-3 p-3 rounded-xl transition-all duration-150 group cursor-pointer
                    ${item.is_vov ? 'hover:bg-[#3bb5ff]/10 border border-transparent hover:border-[#3bb5ff]/20' : 'hover:bg-[#0f1f3a] border border-transparent'}`}
                >
                  <div className="shrink-0">
                    {item.is_dir ? (
                      <Folder className="w-5 h-5 text-[#3bb5ff]/60" />
                    ) : item.is_vov ? (
                      <Package className="w-5 h-5 text-[#3bb5ff]" />
                    ) : (
                      <FileText className="w-5 h-5 text-gray-700" />
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className={`text-sm truncate ${item.is_vov ? 'text-gray-200 group-hover:text-white' : 'text-gray-400'}`}>
                      {item.name}
                    </div>
                    <div className="text-[10px] text-gray-500 truncate font-mono opacity-50">
                      {item.is_dir ? 'Directory' : item.is_vov ? 'Vault Opus Volume' : 'Incompatible File'}
                    </div>
                  </div>

                  {item.is_vov && (
                    <div className="text-[10px] font-bold text-[#3bb5ff]/40 group-hover:text-[#3bb5ff] transition-colors uppercase tracking-widest px-2 py-1 rounded bg-[#3bb5ff]/5 border border-[#3bb5ff]/10">
                      Import
                    </div>
                  )}
                  {item.is_dir && <ChevronRight className="w-4 h-4 text-gray-700 group-hover:text-[#3bb5ff] transition-colors" />}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 bg-[#060d1a]/50 border-t border-[#1a3a5c] text-center">
          <p className="text-[10px] text-gray-500 italic">
            Browse and select a .vov package to import it into your workspace.
          </p>
        </div>
      </div>
    </div>
  );
}
