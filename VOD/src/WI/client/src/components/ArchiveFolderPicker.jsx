// ArchiveFolderPicker.jsx (FOR CLIENT/DESKTOP) from the VAULT OPUS PROJECT version 1-beta-release-6-ESEN-2
// ==================== FULL CLIENT/DESKTOP GUI====================
import React, { useState, useEffect } from 'react';
import { Folder, Home, Check, ChevronRight, ChevronLeft } from 'lucide-react';

const ArchiveFolderPicker = ({ selectedDb, onSelect, onCancel, initialPath = '.' }) => {
  const [currentPath, setCurrentPath] = useState(initialPath);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchArchiveDirectory(currentPath);
  }, [currentPath, selectedDb]);

  const fetchArchiveDirectory = async (path) => {
    if (!selectedDb) return;
    setLoading(true);
    setError(null);
    try {
      const url = `http://localhost:8000/api/listfiles?db=${encodeURIComponent(selectedDb)}&path=${encodeURIComponent(path)}&depth=1`;
      const response = await fetch(url);
      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      let folders = [];

      // If we are at root, results contains root folders
      if (path === '.' || path === '') {
        folders = Object.values(data.results || {})
          .filter(item => item.type === 'folder' || (item.itemid && item.itemid.startsWith('d')))
          .map(item => ({
            name: item.name || item.displayName,
            path: item.name || item.displayName,
            itemid: item.itemid
          }));
      } else {
        // results contains the target folder. We want its contents.
        const keys = Object.keys(data.results || {});
        if (keys.length > 0) {
          const targetFolder = data.results[keys[0]];
          if (targetFolder.contents) {
            folders = Object.values(targetFolder.contents)
              .filter(item => item.type === 'folder' || (item.itemid && item.itemid.startsWith('d')))
              .map(item => ({
                name: item.name || item.displayName,
                path: `${path}/${item.name || item.displayName}`,
                itemid: item.itemid
              }));
          }
        }
      }

      setItems(folders);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleItemClick = (item) => {
    setCurrentPath(item.path);
  };

  const handleGoUp = () => {
    if (currentPath === '.' || currentPath === '') return;
    const parts = currentPath.split('/').filter(p => p);
    parts.pop();
    setCurrentPath(parts.length > 0 ? parts.join('/') : '.');
  };

  return (
    <div className="archive-folder-picker flex flex-col h-full w-full bg-[#060d1a] border border-[#1a3a5c] rounded-lg overflow-hidden shadow-2xl">
      {/* Header */}
      <div className="p-2 border-b border-[#1a3a5c] bg-[#0a1628] flex items-center gap-2">
        <button
          type="button"
          onClick={() => setCurrentPath('.')}
          className="p-1.5 hover:bg-[#0f1f3a] active:scale-90 active:bg-[#3bb5ff]/20 rounded text-[#3bb5ff] transition-all duration-100"
          title="Archive Root"
        >
          <Home size={16} />
        </button>
        {currentPath !== '.' && (
          <button
            type="button"
            onClick={handleGoUp}
            className="p-1.5 hover:bg-[#0f1f3a] active:scale-90 active:bg-[#3bb5ff]/20 rounded text-gray-400 transition-all duration-100"
          >
            <ChevronLeft size={16} />
          </button>
        )}
        <div className="flex-1 overflow-hidden">
          <div className="text-xs text-[#3bb5ff] font-mono truncate">{currentPath || '/'}</div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center h-full text-gray-500 text-sm">Loading archive...</div>
        ) : error ? (
          <div className="p-3 text-red-400 text-sm">{error}</div>
        ) : (
          <div className="py-1">
            {items.length === 0 && (
              <div className="p-4 text-center text-gray-600 text-xs italic">
                No folders found in this location
              </div>
            )}
            {items.map((item) => (
              <button
                type="button"
                key={item.itemid || item.path}
                onClick={() => handleItemClick(item)}
                className="w-full text-left flex items-center gap-2 px-3 py-2 text-sm group transition-all duration-100 select-none hover:bg-[#3bb5ff]/10 active:bg-[#3bb5ff]/20 active:scale-[0.98] text-[#3bb5ff] cursor-pointer"
              >
                <Folder size={16} className="text-[#3bb5ff] flex-shrink-0" />
                <span className="truncate flex-1">{item.name}</span>
                <ChevronRight size={14} className="opacity-0 group-hover:opacity-100 text-gray-500" />
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-2 border-t border-[#1a3a5c] bg-[#0a1628] flex justify-between items-center gap-2">
        <button
          type="button"
          onClick={() => onSelect(currentPath)}
          className="flex-1 px-3 py-1.5 text-xs bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] hover:from-[#005a9e] hover:to-[#2aa5ef] active:from-[#004a8e] active:to-[#1a95df] text-white rounded flex items-center justify-center gap-1.5 transition-all duration-100 shadow-lg shadow-[#3bb5ff]/20"
        >
          <Check size={14} />
          Select Current Folder
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="px-3 py-1.5 text-xs bg-[#0f1f3a] hover:bg-[#1a3a5c] active:bg-[#0a1628] text-white rounded transition-all duration-100 border border-[#1a3a5c]"
          >
            Cancel
          </button>
        )}
      </div>
    </div>
  );
};

export default ArchiveFolderPicker;
