// FolderPicker.jsx (FOR CLIENT/DESKTOP) from the VAULT OPUS PROJECT version 1-beta-release-6-ESEN-2
// ==================== FULL CLIENT/DESKTOP GUI====================
import React, { useState, useEffect, useRef } from 'react';
import { Folder, Home, Check, FileText } from 'lucide-react';

const FolderPicker = ({ initialPath, onSelect, onCancel, showFiles = false, multiple = false }) => {
  const [currentPath, setCurrentPath] = useState(initialPath || '');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedItems, setSelectedItems] = useState(new Set());
  const lastClickIdxRef = useRef(null);

  useEffect(() => {
    fetchDirectory(initialPath);
  }, [initialPath]);

  const fetchDirectory = async (path) => {
    setLoading(true);
    setError(null);
    try {
      const url = path
        ? `http://localhost:8000/api/fs/browse?path=${encodeURIComponent(path)}`
        : `http://localhost:8000/api/fs/browse`;

      const response = await fetch(url);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to fetch directory');
      }

      const data = await response.json();
      setCurrentPath(data.current_path);
      // If showFiles is false, only display directories (folders + the ".." entry)
      const filtered = showFiles
        ? data.items
        : data.items.filter(item => item.is_dir);
      setItems(filtered);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGoHome = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/fs/home');
      const data = await response.json();
      fetchDirectory(data.path);
    } catch (err) {
      setError('Failed to find home directory');
    }
  };

  const handleItemClick = (item) => {
    if (item.name === '..') {
      fetchDirectory(item.path);
      return;
    }

    if (multiple) {
      const newSelected = new Set(selectedItems);
      if (newSelected.has(item.path)) {
        newSelected.delete(item.path);
      } else {
        newSelected.add(item.path);
      }
      setSelectedItems(newSelected);
      lastClickIdxRef.current = items.findIndex(i => i.path === item.path);
    } else {
      // Single click = select the item
      if (showFiles && !item.is_dir) {
        // If showing files and clicking a file, select it and confirm
        onSelect(item.path);
      } else {
        // Click on folder = select it (don't navigate)
        const newSelected = new Set([item.path]);
        setSelectedItems(newSelected);
        lastClickIdxRef.current = items.findIndex(i => i.path === item.path);
      }
    }
  };

  const handleItemDoubleClick = (item) => {
    if (item.name === '..') {
      fetchDirectory(item.path);
      return;
    }
    // Double click on folder = navigate into it
    if (item.is_dir) {
      // Clear selection and navigate
      setSelectedItems(new Set());
      fetchDirectory(item.path);
    } else if (showFiles) {
      // Double click on file = confirm selection
      onSelect(item.path);
    }
  };

  const handleConfirmSelect = () => {
    if (multiple) {
      if (selectedItems.size > 0) {
        onSelect(Array.from(selectedItems));
      } else {
        // If nothing selected, select current folder
        onSelect([currentPath]);
      }
    } else {
      if (selectedItems.size > 0) {
        onSelect(Array.from(selectedItems)[0]);
      } else {
        onSelect(currentPath);
      }
    }
  };

  return (
    <div className="folder-picker flex flex-col h-full w-full bg-[#060d1a] border border-[#1a3a5c] rounded-lg overflow-hidden shadow-2xl">
      {/* Header */}
      <div className="p-2 border-b border-[#1a3a5c] bg-[#0a1628] flex items-center gap-2">
        <button
          onClick={handleGoHome}
          className="p-1.5 hover:bg-[#0f1f3a] active:scale-90 active:bg-[#3bb5ff]/20 rounded text-gray-400 transition-all duration-100"
          title="Home"
        >
          <Home size={16} />
        </button>
        <div className="flex-1 overflow-hidden">
          <div className="text-xs text-gray-500 font-mono truncate">{currentPath || '/'}</div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center h-full text-gray-500 text-sm">Loading...</div>
        ) : error ? (
          <div className="p-3 text-red-400 text-sm">{error}</div>
        ) : (
          <div className="py-1">
            {items.map((item) => (
              <div
                key={item.path}
                onClick={() => handleItemClick(item)}
                onDoubleClick={() => handleItemDoubleClick(item)}
                className={`flex items-center gap-2 px-3 py-2 text-sm group transition-all duration-100 select-none cursor-pointer
                  ${selectedItems.has(item.path) ? 'bg-[#3bb5ff]/10 border-l-2 border-[#3bb5ff]' : 'hover:bg-[#0f1f3a] active:bg-[#1a3a5c] active:scale-[0.98] text-gray-300'}
                  ${item.is_dir ? 'text-[#3bb5ff]' : 'text-gray-300'}
                `}
              >
                {multiple && item.name !== '..' && (
                  <div className={`w-4 h-4 border rounded flex items-center justify-center transition-all duration-100 
                    ${selectedItems.has(item.path)
                      ? 'bg-[#3bb5ff] border-[#3bb5ff] text-white'
                      : 'border-[#1a3a5c] group-hover:border-[#3bb5ff]/50'
                    }`}
                  >
                    {selectedItems.has(item.path) && <Check size={12} strokeWidth={3} />}
                  </div>
                )}
                {item.is_dir ? (
                  <Folder
                    size={16}
                    className={item.name === '..' ? 'text-gray-500' : 'text-[#3bb5ff] flex-shrink-0'}
                  />
                ) : (
                  <FileText size={16} className={`flex-shrink-0 ${showFiles ? 'text-gray-400 group-hover:text-[#3bb5ff]' : 'text-gray-600'}`} />
                )}
                <span className="truncate flex-1">
                  {item.name === '..' ? 'Back (..)' : item.name}
                </span>
                {item.is_dir && item.name !== '..' && (
                  <span className="ml-auto text-[10px] text-gray-600 group-hover:text-gray-400 transition-all px-1">
                    double-click to open
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-2 border-t border-[#1a3a5c] bg-[#0a1628] flex justify-between items-center gap-2">
        <button
          onClick={handleConfirmSelect}
          className="flex-1 px-3 py-1.5 text-xs bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] hover:from-[#005a9e] hover:to-[#2aa5ef] active:from-[#004a8e] active:to-[#1a95df] text-white rounded flex items-center justify-center gap-1.5 transition-all duration-100 shadow-lg shadow-[#3bb5ff]/20 whitespace-nowrap"
        >
          <Check size={14} />
          {multiple && selectedItems.size > 0
            ? `Select ${selectedItems.size} items`
            : (selectedItems.size > 0 ? 'Select Item' : 'Select Current Folder')
          }
        </button>
        <button
          onClick={onCancel}
          className="px-3 py-1.5 text-xs bg-[#0f1f3a] hover:bg-[#1a3a5c] active:bg-[#0a1628] text-white rounded transition-all duration-100 whitespace-nowrap border border-[#1a3a5c]"
        >
          Cancel
        </button>
      </div>
    </div>
  );
};

export default FolderPicker;