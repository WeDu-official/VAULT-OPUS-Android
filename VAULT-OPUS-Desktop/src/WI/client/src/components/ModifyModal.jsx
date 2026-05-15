//ModifyModal.jsx
import React, { useState } from 'react';
import ArchiveFolderPicker from './ArchiveFolderPicker';

export default function ModifyModal({ type, item, onConfirm, onCancel, selectedDb }) {
  const [destination, setDestination] = useState('.');
  const [newName, setNewName] = useState(item?.displayName || '');
  const [copyMode, setCopyMode] = useState(false);
  const [nameMode, setNameMode] = useState('D');
  const [nameCheck, setNameCheck] = useState(true);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (type === 'move') {
      onConfirm({
        type: 'move',
        src: item.itemid || (item.parentPath ? `${item.parentPath}/${item.displayName}` : item.displayName),
        dst: destination,
        copyMode,
        nameCheck,
        idBased: !!item.itemid,
        // Source is ID-based when item has itemid, destination is always path-based
        srcIdBased: !!item.itemid,
        dstIdBased: false
      });
    } else {
      onConfirm({
        type: 'rename',
        item: item.itemid || (item.parentPath ? `${item.parentPath}/${item.displayName}` : item.displayName),
        newName,
        nameMode,
        nameCheck,
        idBased: !!item.itemid
      });
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
      <div className="bg-[#0a1628] border border-[#1a3a5c] rounded-xl shadow-2xl p-6 w-full max-w-lg animate-in zoom-in-95 duration-200">
        <div className="flex items-center gap-3 mb-6 text-[#3bb5ff]">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            {type === 'move' ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            )}
          </svg>
          <h3 className="text-xl font-bold text-white capitalize">{type} Item</h3>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Source Item</label>
            <div className="bg-[#060d1a] border border-[#1a3a5c] rounded-lg px-4 py-2 text-gray-300 text-sm truncate">
              {item.displayName} {item.itemid && <span className="text-[#3bb5ff]/50 font-mono ml-2">({item.itemid})</span>}
            </div>
          </div>

          {type === 'move' ? (
            <>
              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Target Destination</label>
                <div className="max-h-[300px] overflow-hidden border border-[#1a3a5c] rounded-lg bg-[#060d1a]">
                   <ArchiveFolderPicker 
                    selectedDb={selectedDb} 
                    onSelect={(path) => setDestination(path)} 
                    initialPath={destination}
                  />
                </div>
                <p className="mt-2 text-[10px] text-gray-500">Selected: <span className="text-[#3bb5ff] font-mono">{destination}</span></p>
              </div>

              <div className="flex items-center gap-6">
                <label className="flex items-center gap-2 cursor-pointer group">
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={copyMode}
                      onChange={(e) => setCopyMode(e.target.checked)}
                      className="sr-only"
                    />
                    <div className={`w-10 h-5 rounded-full transition-colors ${copyMode ? 'bg-[#3bb5ff]' : 'bg-[#1a3a5c]'}`}></div>
                    <div className={`absolute top-1 left-1 w-3 h-3 bg-white rounded-full transition-transform ${copyMode ? 'translate-x-5' : 'translate-x-0'}`}></div>
                  </div>
                  <span className="text-sm text-gray-300 group-hover:text-white transition-colors">Copy Mode</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer group">
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={nameCheck}
                      onChange={(e) => setNameCheck(e.target.checked)}
                      className="sr-only"
                    />
                    <div className={`w-10 h-5 rounded-full transition-colors ${nameCheck ? 'bg-[#3bb5ff]' : 'bg-[#1a3a5c]'}`}></div>
                    <div className={`absolute top-1 left-1 w-3 h-3 bg-white rounded-full transition-transform ${nameCheck ? 'translate-x-5' : 'translate-x-0'}`}></div>
                  </div>
                  <span className="text-sm text-gray-300 group-hover:text-white transition-colors">Name Check</span>
                </label>
              </div>
            </>
          ) : (
            <>
              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">New Name</label>
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full bg-[#060d1a] border border-[#1a3a5c] focus:border-[#3bb5ff] rounded-lg px-4 py-2.5 text-gray-200 outline-none transition-colors"
                  placeholder="Enter new name"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Rename Mode</label>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { id: 'D', label: 'Default', desc: 'Nickname if exists, else both' },
                    { id: 'N', label: 'Nickname', desc: 'Only if item is nicknamed' },
                    { id: 'B', label: 'Original', desc: 'Only original filename' },
                    { id: 'A', label: 'All', desc: 'Update both names' },
                  ].map((mode) => (
                    <button
                      key={mode.id}
                      type="button"
                      onClick={() => setNameMode(mode.id)}
                      className={`p-3 text-left rounded-lg border transition-all duration-150 ${
                        nameMode === mode.id
                          ? 'bg-[#3bb5ff]/10 border-[#3bb5ff] text-white shadow-[0_0_10px_rgba(59,181,255,0.1)]'
                          : 'bg-[#0f1f3a] border-[#1a3a5c] text-gray-400 hover:border-[#3bb5ff]/50'
                      }`}
                    >
                      <div className="text-sm font-bold">{mode.label}</div>
                      <div className="text-[10px] opacity-60 leading-tight">{mode.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              <label className="flex items-center gap-2 cursor-pointer group pt-2">
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={nameCheck}
                    onChange={(e) => setNameCheck(e.target.checked)}
                    className="sr-only"
                  />
                  <div className={`w-10 h-5 rounded-full transition-colors ${nameCheck ? 'bg-[#3bb5ff]' : 'bg-[#1a3a5c]'}`}></div>
                  <div className={`absolute top-1 left-1 w-3 h-3 bg-white rounded-full transition-transform ${nameCheck ? 'translate-x-5' : 'translate-x-0'}`}></div>
                </div>
                <span className="text-sm text-gray-300 group-hover:text-white transition-colors">Name Check</span>
              </label>
            </>
          )}

          <div className="flex justify-end gap-3 pt-4 border-t border-[#1a3a5c]">
            <button
              type="button"
              onClick={onCancel}
              className="px-6 py-2 text-sm font-medium text-gray-400 hover:text-white transition-all active:scale-95"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-8 py-2 text-sm bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] hover:from-[#005a9e] hover:to-[#2aa5ef] text-white rounded-lg transition-all active:scale-95 shadow-lg font-bold"
            >
              Confirm {type}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
