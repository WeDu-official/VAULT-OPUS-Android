//OpenVolumeModal.jsx
import React, { useState, useEffect } from 'react';
import { X, Database, CheckSquare, Square, Search, Loader2, FolderOpen, ChevronRight, Folder, File, Home, ArrowLeft, Package } from 'lucide-react';

export default function OpenVolumeModal({ isOpen, onClose, onOpenVolumes, onImportPackage }) {
  const [currentPath, setCurrentPath] = useState('');
  const [items, setItems] = useState([]);
  const [selectedPaths, setSelectedPaths] = useState([]);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState('browse'); // 'browse' or 'databases'

  useEffect(() => {
    if (isOpen) {
      if (viewMode === 'databases') {
        fetchDatabases();
      } else {
        fetchDirectory(currentPath);
      }
      setSelectedPaths([]);
    }
  }, [isOpen, viewMode]);

  const fetchDatabases = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/dbs');
      const data = await response.json();
      const dbs = Array.isArray(data.dbs) ? data.dbs : [];
      setItems(dbs.map(db => ({ name: db, path: db, is_dir: false, is_db: true })));
    } catch (error) {
      console.error('Error fetching databases:', error);
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
        is_db: item.name.toLowerCase().endsWith('.db'),
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
    } else if (item.is_db) {
      toggleSelect(item.path);
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

  const toggleSelect = (path) => {
    if (selectedPaths.includes(path)) {
      setSelectedPaths(selectedPaths.filter(p => p !== path));
    } else {
      setSelectedPaths([...selectedPaths, path]);
    }
  };

  const handleOpen = () => {
    if (selectedPaths.length > 0) {
      onOpenVolumes(selectedPaths);
      onClose();
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
                <FolderOpen className="w-5 h-5" />
              </div>
              <h2 className="text-xl font-semibold text-white">Open Volume</h2>
            </div>
            <button onClick={onClose} className="p-1 hover:bg-[#0f1f3a] rounded-full transition-colors text-gray-400">
              <X className="w-6 h-6" />
            </button>
          </div>

          <div className="flex gap-2 p-1 bg-[#060d1a] rounded-xl border border-[#1a3a5c]">
            <button
              onClick={() => setViewMode('browse')}
              className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-bold transition-all ${viewMode === 'browse' ? 'bg-[#3bb5ff] text-[#0a1628]' : 'text-gray-400 hover:text-white hover:bg-[#0f1f3a]'}`}
            >
              <Search className="w-3.5 h-3.5" />
              System Browser
            </button>
            <button
              onClick={() => setViewMode('databases')}
              className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-bold transition-all ${viewMode === 'databases' ? 'bg-[#3bb5ff] text-[#0a1628]' : 'text-gray-400 hover:text-white hover:bg-[#0f1f3a]'}`}
            >
              <Database className="w-3.5 h-3.5" />
              DATABASES Folder
            </button>
          </div>
        </div>

        {/* Browser Navigation */}
        {viewMode === 'browse' && (
          <div className="px-6 py-3 bg-[#060d1a]/50 border-b border-[#1a3a5c] flex items-center gap-3 shrink-0">
            <button 
              onClick={() => fetchDirectory('')}
              className="p-1.5 hover:bg-[#1a3a5c] rounded text-[#3bb5ff]"
              title="Home"
            >
              <Home className="w-4 h-4" />
            </button>
            <div className="flex-1 overflow-hidden">
              <div className="flex items-center gap-1 text-xs text-gray-500 overflow-x-auto no-scrollbar whitespace-nowrap">
                {currentPath.split(/[/\\]/).filter(p => p).map((part, idx, arr) => (
                  <React.Fragment key={idx}>
                    <span className="hover:text-white cursor-pointer" onClick={() => {
                      const newPath = currentPath.split(/[/\\]/).slice(0, idx + 2).join('/');
                      fetchDirectory(newPath);
                    }}>{part}</span>
                    {idx < arr.length - 1 && <ChevronRight className="w-3 h-3 opacity-30" />}
                  </React.Fragment>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 text-gray-500 gap-3">
              <Loader2 className="w-8 h-8 animate-spin text-[#3bb5ff]" />
              <p className="text-sm font-mono tracking-wider opacity-60">Scanning File System...</p>
            </div>
          ) : items.length === 0 ? (
            <div className="text-center py-20 text-gray-500 italic flex flex-col items-center gap-4">
              <Folder className="w-12 h-12 opacity-20" />
              <p>No suitable files found in this location.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-1">
              {items.map((item) => {
                const isSelected = selectedPaths.includes(item.path);
                const isSelectable = !item.is_dir && item.is_db;
                
                return (
                  <div
                    key={item.path}
                    onClick={() => handleItemClick(item)}
                    className={`flex items-center gap-3 p-3 rounded-xl transition-all duration-150 group cursor-pointer
                      ${isSelected ? 'bg-[#3bb5ff]/10 border border-[#3bb5ff]/30 shadow-[0_0_15px_-5px_rgba(59,181,255,0.2)]' : 'hover:bg-[#0f1f3a] border border-transparent'}`}
                  >
                    <div className="shrink-0">
                      {item.is_dir ? (
                        <Folder className="w-5 h-5 text-[#3bb5ff]/60" />
                      ) : item.is_db ? (
                        isSelected ? <CheckSquare className="w-5 h-5 text-[#3bb5ff]" /> : <Database className="w-5 h-5 text-gray-600 group-hover:text-gray-400" />
                      ) : item.is_vov ? (
                        <Package className="w-5 h-5 text-[#3bb5ff]" />
                      ) : (
                        <File className="w-5 h-5 text-gray-700" />
                      )}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className={`text-sm truncate ${isSelected ? 'text-white font-medium' : 'text-gray-300'}`}>
                        {item.name}
                      </div>
                      <div className="text-[10px] text-gray-500 truncate font-mono opacity-50 group-hover:opacity-100 transition-opacity">
                        {item.path}
                      </div>
                    </div>

                    {item.is_dir && (
                      <ChevronRight className="w-4 h-4 text-gray-700 group-hover:text-[#3bb5ff] transition-colors" />
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 bg-[#060d1a]/50 border-t border-[#1a3a5c] shrink-0">
          <div className="flex items-center justify-between mb-4 px-1">
            <span className="text-xs text-gray-500 font-mono">
              {selectedPaths.length} <span className="opacity-50">Volume(s) Selected</span>
            </span>
            {selectedPaths.length > 0 && (
              <button 
                onClick={() => setSelectedPaths([])}
                className="text-xs text-red-400 hover:text-red-300 font-medium transition-colors"
              >
                Reset Selection
              </button>
            )}
          </div>
          <button
            onClick={handleOpen}
            disabled={selectedPaths.length === 0}
            className="w-full py-4 bg-gradient-to-r from-[#3bb5ff] to-[#006fbe] hover:from-[#4cc0ff] hover:to-[#007ed8] disabled:from-gray-800 disabled:to-gray-900 disabled:opacity-50 text-white rounded-xl font-bold transition-all duration-200 active:scale-[0.98] shadow-lg shadow-[#3bb5ff]/10 uppercase tracking-widest text-xs"
          >
            Load into Workspace
          </button>
        </div>
      </div>
    </div>
  );
}
