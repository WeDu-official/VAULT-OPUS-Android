// FileExplorer.jsx
import React, { useState, useEffect, useRef } from 'react';
import { RefreshCw } from 'lucide-react';

const PathNavigation = ({ currentPath, onNavigate, selectedDb }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(currentPath);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => {
    setEditValue(currentPath);
  }, [currentPath]);

  const fetchSuggestions = async (path) => {
    setLoading(true);
    try {
      const parts = path.split('/').filter(p => p);
      let parentPath = '.';
      let searchPrefix = '';
      if (parts.length > 0) {
        searchPrefix = parts[parts.length - 1];
        parentPath = parts.slice(0, -1).join('/') || '.';
      } else {
        searchPrefix = '';
        parentPath = '.';
      }
      const response = await fetch(`http://localhost:8000/api/listfiles?db=${encodeURIComponent(selectedDb || '')}&path=${encodeURIComponent(parentPath)}`);
      const data = await response.json();
      if (data.results) {
        const folders = Object.values(data.results)
          .filter(item => {
            const type = item.type || (item.itemid && item.itemid.startsWith('d') ? 'folder' : 'file');
            return type === 'folder';
          })
          .filter(folder => folder.name.toLowerCase().startsWith(searchPrefix.toLowerCase()))
          .map(folder => {
            const newParts = parts.slice(0, -1);
            const pathToken = folder.db_name || folder.name;
            newParts.push(pathToken);
            return { path: newParts.join('/') || '.', name: folder.name };
          });
        setSuggestions(folders);
        setShowSuggestions(folders.length > 0 && searchPrefix.length > 0);
      } else {
        setSuggestions([]);
        setShowSuggestions(false);
      }
    } catch (err) {
      console.error('Failed to fetch suggestions:', err);
      setSuggestions([]);
      setShowSuggestions(false);
    } finally { setLoading(false); }
  };

  const handleEditStart = () => { setIsEditing(true); setEditValue(currentPath); setShowSuggestions(false); };
  const handleEditChange = (e) => {
    const value = e.target.value; setEditValue(value);
    if (value.length > 0) fetchSuggestions(value);
    else { setSuggestions([]); setShowSuggestions(false); }
  };
  const handleEditBlur = () => { setTimeout(() => { setIsEditing(false); setShowSuggestions(false); }, 200); };
  const handleEditKeyPress = (e) => {
    if (e.key === 'Enter') { onNavigate(editValue); setIsEditing(false); setShowSuggestions(false); }
    else if (e.key === 'Escape') { setEditValue(currentPath); setIsEditing(false); setShowSuggestions(false); }
  };
  const handleSuggestionClick = (suggestedPath) => { setEditValue(suggestedPath); onNavigate(suggestedPath); setIsEditing(false); setShowSuggestions(false); };
  const handleQuickNav = (newPath) => { onNavigate(newPath); };

  if (isEditing) {
    return (
      <div className="flex-1 flex items-center relative">
        <div className="flex items-center gap-1 text-[#3bb5ff]/50 text-xs mr-2">path:</div>
        <input ref={inputRef} type="text" value={editValue} onChange={handleEditChange} onBlur={handleEditBlur} onKeyDown={handleEditKeyPress}
          className="flex-1 bg-[#060d1a] border border-[#3bb5ff] rounded px-2 py-1 text-xs text-[#3bb5ff] font-mono focus:outline-none focus:ring-1 focus:ring-[#3bb5ff]" placeholder="Enter path" autoFocus />
        {loading && <div className="ml-2 text-xs text-gray-500">loading...</div>}
        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute top-full left-0 mt-1 w-full bg-[#060d1a] border border-[#1a3a5c] rounded shadow-lg z-50 max-h-40 overflow-y-auto">
            {suggestions.map((sug, idx) => (
              <div key={idx} onClick={() => handleSuggestionClick(sug.path)}
                className="px-3 py-1.5 text-xs text-gray-300 hover:bg-[#3bb5ff]/10 cursor-pointer border-b border-[#1a3a5c] last:border-b-0 flex items-center gap-2">
                <svg className="w-3 h-3 text-[#3bb5ff] flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"></path></svg>
                <span>{sug.name}</span><span className="text-gray-500 ml-auto">→ {sug.path}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="flex-1 flex items-center gap-2">
      <div className="text-[#3bb5ff]/50 text-xs mr-2">path:</div>
      <div onClick={handleEditStart} className="flex-1 bg-[#060d1a] border border-[#1a3a5c] rounded px-2 py-1 text-xs text-gray-300 font-mono cursor-text hover:border-[#3bb5ff]/50 truncate" title="Click to edit path">{currentPath || '.'}</div>
      <div className="flex items-center gap-1">
        <button onClick={() => handleQuickNav('.')} className="px-2 py-0.5 text-[10px] bg-[#0f1f3a] hover:bg-[#1a3a5c] text-gray-400 rounded transition-colors border border-[#1a3a5c]" title="Root">root</button>
        {currentPath !== '.' && (
          <button onClick={() => { const parts = currentPath.split('/').filter(p => p); parts.pop(); handleQuickNav(parts.length > 0 ? parts.join('/') : '.'); }}
            className="px-2 py-0.5 text-[10px] bg-[#0f1f3a] hover:bg-[#1a3a5c] text-gray-400 rounded transition-colors border border-[#1a3a5c]" title="Go up">up</button>
        )}
      </div>
    </div>
  );
};

export default function FileExplorer({ tree, currentPath, onNavigate, selectedItems, onSelect, onNewVersionRequest, onSeeVersions, onDownloadVersion, onDeleteVersionsRequest, onShowFullName, onRefresh, selectedDb, currentVersion, onExitVersionView, onMoveRequest, onRenameRequest, onMakeFolder }) {

  let items = [];
  if (tree && tree.results) {
    const results = tree.results;
    const resultKeys = Object.keys(results);
    if (currentPath !== '.' && resultKeys.length === 1) {
      const singleResult = results[resultKeys[0]];
      if (singleResult.type === 'folder' && singleResult.contents) {
        items = Object.values(singleResult.contents).map(item => ({
          ...item, displayName: item.name || item.db_name || "Unknown", type: item.type || (item.itemid && item.itemid.startsWith('d') ? 'folder' : 'file')
        }));
      } else {
        items = resultKeys.map(key => {
          const item = results[key];
          return { ...item, itemid: key, displayName: item.name || item.db_name || "Unknown", type: item.type || (item.itemid && item.itemid.startsWith('d') ? 'folder' : 'file') };
        });
      }
    } else {
      items = resultKeys.map(key => {
        const item = results[key];
        return { ...item, itemid: key, displayName: item.name || item.db_name || "Unknown", type: item.type || (item.itemid && item.itemid.startsWith('d') ? 'folder' : 'file') };
      });
    }
  }

  const [contextMenu, setContextMenu] = useState(null);
  const [backgroundMenu, setBackgroundMenu] = useState(null);
  const lastClickIdxRef = useRef(null);

  const handleItemClick = (item, e) => {
    if (e.metaKey || e.ctrlKey) {
      // Toggle individual item
      if (selectedItems.find(i => i.itemid === item.itemid)) {
        onSelect(selectedItems.filter(i => i.itemid !== item.itemid));
      } else {
        onSelect([...selectedItems, item]);
      }
      lastClickIdxRef.current = items.findIndex(i => i.itemid === item.itemid);
    } else if (e.shiftKey && lastClickIdxRef.current !== null) {
      // Shift-click range selection
      const clickIdx = items.findIndex(i => i.itemid === item.itemid);
      if (clickIdx !== -1) {
        const start = Math.min(lastClickIdxRef.current, clickIdx);
        const end = Math.max(lastClickIdxRef.current, clickIdx);
        const range = items.slice(start, end + 1);
        // Merge with existing selection (add range items, keep others)
        const newSelection = [...selectedItems];
        range.forEach(r => {
          if (!newSelection.find(i => i.itemid === r.itemid)) {
            newSelection.push(r);
          }
        });
        onSelect(newSelection);
      }
    } else {
      // Normal click: if item is already selected, unselect it. Otherwise select just this item.
      if (selectedItems.find(i => i.itemid === item.itemid) && selectedItems.length === 1) {
        onSelect([]);
      } else if (selectedItems.find(i => i.itemid === item.itemid) && selectedItems.length > 1) {
        // Multiple selected, clicking one of them -> select only that one
        onSelect([item]);
      } else {
        onSelect([item]);
      }
      lastClickIdxRef.current = items.findIndex(i => i.itemid === item.itemid);
    }
  };

  const handleItemDoubleClick = (item) => {
    if (item.type === 'folder') {
      const folderPathToken = item.db_name || item.name;
      const newPath = currentPath === '.' ? folderPathToken : `${currentPath}/${folderPathToken}`;
      onNavigate(newPath);
    }
  };

  const handleContextMenu = (e, item) => {
    e.preventDefault();
    e.stopPropagation();
    setBackgroundMenu(null);
    const isSelected = selectedItems.find(i => i.itemid === item.itemid);
    if (!isSelected) {
      onSelect([item]);
      lastClickIdxRef.current = items.findIndex(i => i.itemid === item.itemid);
    }
    setContextMenu({ x: e.clientX, y: e.clientY, item: item });
  };

  const handleBackgroundContextMenu = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setContextMenu(null);
    setBackgroundMenu({ x: e.clientX, y: e.clientY });
  };

  const handleSelectAll = () => {
    onSelect([...items]);
    setBackgroundMenu(null);
  };

  const handleMakeFolderFromBG = () => {
    setBackgroundMenu(null);
    if (onMakeFolder) onMakeFolder();
  };

  const handleNewVersion = () => {
    if (contextMenu && onNewVersionRequest) {
      const item = contextMenu.item;
      const itemPath = currentPath === '.' ? item.displayName : `${currentPath}/${item.displayName}`;
      onNewVersionRequest(itemPath);
    }
    setContextMenu(null);
  };
  const handleSeeVersions = () => {
    if (contextMenu && onSeeVersions) {
      const item = contextMenu.item;
      const itemPath = currentPath === '.' ? item.displayName : `${currentPath}/${item.displayName}`;
      onSeeVersions(itemPath);
    }
    setContextMenu(null);
  };
  const handleDownloadVersion = () => {
    if (contextMenu && onDownloadVersion) {
      const item = contextMenu.item;
      const itemPath = currentPath === '.' ? item.displayName : `${currentPath}/${item.displayName}`;
      onDownloadVersion(itemPath, item);  // ← pass both path AND item
    }
    setContextMenu(null);
  };
  const handleDeleteVersions = () => { if (contextMenu && onDeleteVersionsRequest) onDeleteVersionsRequest(); setContextMenu(null); };
  const handleMove = () => { if (contextMenu && onMoveRequest) onMoveRequest(contextMenu.item); setContextMenu(null); };
  const handleRename = () => { if (contextMenu && onRenameRequest) onRenameRequest(contextMenu.item); setContextMenu(null); };
  const handleShowFullName = () => { if (contextMenu && onShowFullName) onShowFullName(contextMenu.item); setContextMenu(null); };

  const navigateUp = () => {
    if (currentPath === '.') return;
    const parts = currentPath.split('/');
    parts.pop();
    onNavigate(parts.length > 0 ? parts.join('/') : '.');
  };

  if (!tree) {
    return <div className="flex items-center justify-center h-full text-gray-500">Select a volume to view files</div>;
  }

  if (tree.error) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-red-400 bg-red-900/10 rounded-lg border border-red-900/20 p-8">
        <h3 className="text-lg font-bold mb-2">Error</h3>
        <p className="text-sm opacity-80">{tree.error}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full relative">
      <div className="flex items-center gap-3 mb-6 bg-[#0a1628] p-3 rounded-lg border border-[#1a3a5c] shadow-sm">
        <button onClick={navigateUp} disabled={currentPath === '.'}
          className="p-1.5 hover:bg-[#0f1f3a] rounded transition-all duration-150 disabled:opacity-30 icon-btn btn-click active:scale-90" title="Go up">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
        </button>
        <PathNavigation currentPath={currentPath} onNavigate={onNavigate} selectedDb={selectedDb} />

        {currentVersion && (
          <div className="flex items-center gap-2 px-3 py-1 bg-[#3bb5ff]/20 border border-[#3bb5ff]/50 rounded-full animate-pulse shadow-[0_0_10px_rgba(59,181,255,0.2)]">
            <svg className="w-3.5 h-3.5 text-[#3bb5ff]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            <span className="text-[10px] font-bold text-[#3bb5ff] uppercase tracking-tighter whitespace-nowrap">Version {currentVersion}</span>
            <button onClick={onExitVersionView} className="ml-1 p-0.5 hover:bg-[#3bb5ff]/30 rounded-full text-[#3bb5ff] transition-colors" title="Exit Version View">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>
          </div>
        )}

        <button onClick={onRefresh} className="p-1.5 hover:bg-[#0f1f3a] rounded transition-all duration-150 text-[#3bb5ff] hover:text-[#3bb5ff]/80 active:scale-90" title="Refresh view">
          <RefreshCw className="w-5 h-5" />
        </button>
      </div>

      {/* Items grid with background context menu */}
      {items.length === 0 ? (
        <div className="flex flex-col items-center justify-center flex-1 text-gray-500 opacity-50" onContextMenu={handleBackgroundContextMenu}>
          <svg className="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 01-2 2z"></path></svg>
          <p>This folder is empty. Right-click here for options.</p>
        </div>
      ) : (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(150px,1fr))] gap-4 pb-20 content-start" onContextMenu={handleBackgroundContextMenu}>
          {items.map((item, idx) => {
            const isSelected = selectedItems.find(i => i.itemid === item.itemid);
            const isFolder = item.type === 'folder';
            return (
              <div key={idx}
                onClick={(e) => handleItemClick(item, e)}
                onDoubleClick={() => handleItemDoubleClick(item)}
                onContextMenu={(e) => handleContextMenu(e, item)}
                className={`flex flex-col items-center justify-center p-4 rounded-xl cursor-pointer transition-all duration-200 border select-none interactive-press group aspect-[4/3]
                  ${isSelected ? 'bg-[#3bb5ff]/10 border-[#3bb5ff] shadow-[0_0_15px_rgba(59,181,255,0.15)]' : 'bg-[#0a1628] border-[#1a3a5c] hover:bg-[#0f1f3a] hover:border-[#2a5a8c]'}
                  ${isFolder ? 'folder-hover' : ''}`}
              >
                <div className="w-12 h-12 mb-2 flex items-center justify-center transition-transform duration-200 group-hover:scale-110">
                  {isFolder ? (
                    <svg className="w-full h-full text-[#3bb5ff] drop-shadow-md" fill="currentColor" viewBox="0 0 20 20"><path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"></path></svg>
                  ) : (
                    <svg className="w-full h-full text-gray-400 drop-shadow-md group-hover:text-gray-300 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path></svg>
                  )}
                </div>
                <div className="text-sm font-medium text-center truncate w-full group-hover:text-white transition-colors text-gray-300">{item.displayName}</div>
              </div>
            );
          })}
        </div>
      )}

      {/* Item Context Menu */}
      {contextMenu && selectedItems.length === 1 && (
        <div className="fixed z-50 bg-[#0a1628] border border-[#1a3a5c] rounded-lg shadow-xl py-1 min-w-[200px] animate-in fade-in slide-in-from-top-1"
          style={{ left: Math.min(contextMenu.x, window.innerWidth - 220), top: Math.min(contextMenu.y, window.innerHeight - 200) }}>
          <button onClick={handleNewVersion} className="w-full px-3 py-1.5 text-left text-xs text-gray-300 hover:bg-[#3bb5ff]/10 hover:text-white flex items-center gap-2 transition-colors border-b border-[#1a3a5c]">
            <svg className="w-3.5 h-3.5 text-[#3bb5ff]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4-4m0 0L8 8m4-4v12"></path></svg>
            Upload New Version
          </button>
          <button onClick={handleSeeVersions} className="w-full px-3 py-1.5 text-left text-xs text-gray-300 hover:bg-[#3bb5ff]/10 hover:text-white flex items-center gap-2 transition-colors border-b border-[#1a3a5c]">
            <svg className="w-3.5 h-3.5 text-[#3bb5ff]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            See Versions
          </button>
          <button onClick={handleDownloadVersion} className="w-full px-3 py-1.5 text-left text-xs text-gray-300 hover:bg-[#3bb5ff]/10 hover:text-white flex items-center gap-2 transition-colors border-b border-[#1a3a5c]">
            <svg className="w-3.5 h-3.5 text-[#3bb5ff]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4-4m0 0L8 8m4-4v12"></path></svg>
            Download Version
          </button>
          <button onClick={handleMove} className="w-full px-3 py-1.5 text-left text-xs text-gray-300 hover:bg-[#3bb5ff]/10 hover:text-white flex items-center gap-2 transition-colors border-b border-[#1a3a5c]">
            <svg className="w-3.5 h-3.5 text-[#3bb5ff]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path></svg>
            Move / Copy Item
          </button>
          <button onClick={handleRename} className="w-full px-3 py-1.5 text-left text-xs text-gray-300 hover:bg-[#3bb5ff]/10 hover:text-white flex items-center gap-2 transition-colors border-b border-[#1a3a5c]">
            <svg className="w-3.5 h-3.5 text-[#3bb5ff]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
            Rename Item
          </button>
          <button onClick={handleDeleteVersions} className="w-full px-3 py-1.5 text-left text-xs text-red-400 hover:bg-red-500/10 hover:text-red-300 flex items-center gap-2 transition-colors">
            <svg className="w-3.5 h-3.5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
            Delete versions
          </button>
          <button onClick={handleShowFullName} className="w-full px-3 py-1.5 text-left text-xs text-gray-300 hover:bg-[#3bb5ff]/10 hover:text-white flex items-center gap-2 transition-colors border-t border-[#1a3a5c]">
            <svg className="w-3.5 h-3.5 text-[#3bb5ff]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            Show Full Name
          </button>
        </div>
      )}

      {/* Background Context Menu */}
      {backgroundMenu && (
        <div className="fixed z-50 bg-[#0a1628] border border-[#1a3a5c] rounded-lg shadow-xl py-1 min-w-[180px] animate-in fade-in slide-in-from-top-1"
          style={{ left: Math.min(backgroundMenu.x, window.innerWidth - 200), top: Math.min(backgroundMenu.y, window.innerHeight - 150) }}>
          <button onClick={handleMakeFolderFromBG} className="w-full px-3 py-1.5 text-left text-xs text-gray-300 hover:bg-[#3bb5ff]/10 hover:text-white flex items-center gap-2 transition-colors border-b border-[#1a3a5c]">
            <svg className="w-3.5 h-3.5 text-[#3bb5ff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 13h6m-3-3v6m-5 4h10a2 2 0 002-2V9a2 2 0 00-2-2h-2.586a1 1 0 01-.707-.293l-1.414-1.414a1 1 0 00-.707-.293H7a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            New Folder
          </button>
          <button onClick={handleSelectAll} className="w-full px-3 py-1.5 text-left text-xs text-gray-300 hover:bg-[#3bb5ff]/10 hover:text-white flex items-center gap-2 transition-colors">
            <svg className="w-3.5 h-3.5 text-[#3bb5ff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
            </svg>
            Select All ({items.length} items)
          </button>
        </div>
      )}

      {/* Click outside to close menus */}
      {(contextMenu || backgroundMenu) && (
        <div className="fixed inset-0 z-40" onClick={() => { setContextMenu(null); setBackgroundMenu(null); }} />
      )}
    </div>
  );
}