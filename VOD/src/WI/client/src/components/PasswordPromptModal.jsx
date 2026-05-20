// PasswordPromptModal.jsx (FOR CLIENT/DESKTOP) from the VAULT OPUS PROJECT version 1-beta-release-6-ESEN-2
// ==================== FULL CLIENT/DESKTOP GUI====================
import React, { useState } from 'react';

export default function PasswordPromptModal({ items, onSubmit, onCancel }) {
  // items is an array of objects: { id: string, name: string, hash: string }
  const [passwords, setPasswords] = useState({});

  // Group items by their hash (or unique item id if they don't have a hash)
  const groupedItems = items.reduce((acc, item) => {
    const key = item.hash || item.id;
    if (!acc[key]) acc[key] = [];
    acc[key].push(item);
    return acc;
  }, {});

  const handleChange = (groupId, value) => {
    setPasswords(prev => {
      const next = { ...prev };
      // Map this password value to all items in the group
      groupedItems[groupId].forEach(item => {
        next[item.id] = value;
      });
      return next;
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(passwords);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-[#0a1628] border border-[#1a3a5c] shadow-2xl rounded-xl w-full max-w-md overflow-hidden animate-fade-in-up">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#1a3a5c] bg-[#060d1a]/50">
          <h3 className="text-lg font-bold text-[#3bb5ff]">Decryption Required</h3>
          <p className="text-sm text-gray-400 mt-1">Please enter the password for the following items:</p>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {Object.entries(groupedItems).map(([groupId, itemsInGroup]) => (
            <div key={groupId} className="space-y-2 bg-[#060d1a]/50 p-4 border border-[#1a3a5c]/50 rounded-lg">
              {/* Scrollable list of files in the group */}
              <div className="max-h-24 overflow-y-auto pr-1 space-y-1 scrollbar-thin">
                {itemsInGroup.map(item => (
                  <div key={item.id} className="text-xs text-gray-300 truncate">
                    • {item.name}
                  </div>
                ))}
              </div>
              <input
                type="password"
                required
                className="w-full px-3 py-2 bg-[#060d1a] border border-[#1a3a5c] rounded-md text-white focus:outline-none focus:border-[#3bb5ff] transition-colors text-sm"
                placeholder="Enter password..."
                onChange={(e) => handleChange(groupId, e.target.value)}
              />
            </div>
          ))}

          {/* Footer */}
          <div className="pt-4 flex justify-end gap-3 border-t border-[#1a3a5c] mt-6">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 bg-transparent border border-gray-600 text-gray-300 rounded-md hover:bg-gray-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-[#3bb5ff] text-[#060d1a] font-medium rounded-md hover:bg-[#2a94d6] transition-colors shadow-[0_0_15px_rgba(59,181,255,0.3)]"
            >
              Confirm
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
