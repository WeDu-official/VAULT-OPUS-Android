// SettingsModal.jsx (FOR CLIENT/DESKTOP) from the VAULT OPUS PROJECT version 1-beta-release-6-ESEN-2
// ==================== FULL CLIENT/DESKTOP GUI====================
import React, { useState, useEffect } from 'react';
import FolderPicker from './FolderPicker';
import { Settings, Save, X, ChevronRight, Globe, Shield, Upload, Download, Database, Terminal, FolderOpen } from 'lucide-react';

// ---------- Type Casting Helper for Config Settings ----------
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

const ConfigField = ({ label, value, path, onChange, isBoolean }) => {
  if (isBoolean) {
    const isChecked = value === 'true' || value === true;
    return (
      <label className="flex items-center justify-between p-3 bg-[#060d1a] border border-[#1a3a5c] rounded-xl cursor-pointer hover:border-[#3bb5ff]/30 transition-all group">
        <span className="text-sm text-gray-300 group-hover:text-white transition-colors">{label}</span>
        <input
          type="checkbox"
          checked={isChecked}
          onChange={(e) => onChange(path, e.target.checked)}
          className="w-4 h-4 accent-[#3bb5ff]"
        />
      </label>
    );
  }

  return (
    <div className="space-y-2">
      <label className="text-[10px] text-[#3bb5ff]/70 uppercase tracking-widest font-bold ml-1">{label}</label>
      <input
        type="text"
        value={value ?? ''}
        onChange={(e) => onChange(path, e.target.value)}
        className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-4 py-2.5 text-sm focus:border-[#3bb5ff] focus:ring-1 focus:ring-[#3bb5ff]/20 outline-none transition-all text-gray-200 placeholder-gray-600"
        placeholder={`Enter ${label}...`}
      />
    </div>
  );
};

const ConfigSection = ({ title, data, path = [], onChange, config }) => {
  const getIcon = (name) => {
    switch (name.toLowerCase()) {
      case 'discord': return <Globe size={16} />;
      case 'encryption': return <Shield size={16} />;
      case 'upload': return <Upload size={16} />;
      case 'download': return <Download size={16} />;
      case 'database': return <Database size={16} />;
      default: return <Settings size={16} />;
    }
  };

  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
      <div className="flex items-center gap-2 pb-2 border-b border-[#1a3a5c]">
        <div className="text-[#3bb5ff]">{getIcon(title)}</div>
        <h3 className="text-sm font-bold text-white uppercase tracking-wider">{title}</h3>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(data).map(([key, val]) => {
          const fieldPath = [...path, key];
          if (val !== null && typeof val === 'object' && !Array.isArray(val)) {
            return (
              <div key={key} className="col-span-full mt-4">
                <ConfigSection title={key} data={val} path={fieldPath} onChange={onChange} config={config} />
              </div>
            );
          }

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

          return (
            <ConfigField
              key={key}
              label={key.replace(/_/g, ' ')}
              value={val}
              path={fieldPath}
              isBoolean={isBoolean}
              onChange={onChange}
            />
          );
        })}
      </div>
    </div>
  );
};

export default function SettingsModal({ isOpen, onClose, config, onSave }) {
  const [localConfig, setLocalConfig] = useState(null);
  const [downloadFolder, setDownloadFolder] = useState('');
  const [showFolderPicker, setShowFolderPicker] = useState(false);

  useEffect(() => {
    if (config) {
      const mapToStrings = (obj) => {
        const result = {};
        for (const k in obj) {
          if (obj[k] !== null && typeof obj[k] === 'object' && !Array.isArray(obj[k])) {
            result[k] = mapToStrings(obj[k]);
          } else if (typeof obj[k] === 'boolean') {
            result[k] = obj[k];
          } else {
            result[k] = obj[k] === null || obj[k] === undefined ? '' : String(obj[k]);
          }
        }
        return result;
      };
      setLocalConfig(mapToStrings(config));
      setDownloadFolder(localStorage.getItem('VAULT_OPUS_download_folder') || './downloads');
    }
  }, [config, isOpen]);

  if (!isOpen || !localConfig) return null;

  const handleFieldChange = (path, value) => {
    setLocalConfig(prev => {
      const updateNested = (obj, pathParts, val) => {
        const [first, ...rest] = pathParts;
        if (rest.length === 0) {
          return { ...obj, [first]: val };
        }
        return {
          ...obj,
          [first]: updateNested(obj[first] || {}, rest, val)
        };
      };
      return updateNested(prev, path, value);
    });
  };

  const handleSave = () => {
    if (localConfig && config) {
      const castedConfig = castConfigTypes(config, localConfig);
      localStorage.setItem('VAULT_OPUS_download_folder', downloadFolder);
      onSave(castedConfig);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="bg-[#0a1628] border border-[#1a3a5c] rounded-3xl w-full max-w-4xl max-h-[90vh] shadow-[0_0_50px_-12px_rgba(59,181,255,0.25)] overflow-hidden flex flex-col animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[#1a3a5c] bg-[#0a1628]/80 backdrop-blur-sm sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-[#3bb5ff]/10 rounded-2xl text-[#3bb5ff]">
              <Settings size={24} className="animate-[spin_4s_linear_infinite]" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-tight">Advanced Settings</h2>
              <p className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">Configure every detail of your Vault</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-red-500/10 hover:text-red-400 rounded-xl transition-all text-gray-400 active:scale-90">
            <X size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-8 space-y-10">
          {showFolderPicker ? (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-300 h-[500px] flex flex-col">
              <div className="flex items-center gap-2 mb-6">
                <button onClick={() => setShowFolderPicker(false)} className="p-2 hover:bg-[#1a3a5c] rounded-lg text-[#3bb5ff]">
                  <ChevronRight size={20} className="rotate-180" />
                </button>
                <h3 className="text-lg font-bold text-white">Select Download Directory</h3>
              </div>
              <FolderPicker
                initialPath={downloadFolder}
                onSelect={(path) => {
                  setDownloadFolder(path);
                  setShowFolderPicker(false);
                }}
                onCancel={() => setShowFolderPicker(false)}
              />
            </div>
          ) : (
            <>
              {/* Special Section: UI Settings */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 pb-2 border-b border-[#1a3a5c]">
                  <div className="text-[#3bb5ff]"><Terminal size={16} /></div>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">Web Interface</h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-[10px] text-[#3bb5ff]/70 uppercase tracking-widest font-bold ml-1">Download Destination</label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={downloadFolder}
                        onChange={(e) => setDownloadFolder(e.target.value)}
                        className="flex-1 bg-[#060d1a] border border-[#1a3a5c] rounded-xl px-4 py-2.5 text-sm focus:border-[#3bb5ff] outline-none text-gray-200"
                        placeholder="./downloads"
                      />
                      <button
                        onClick={() => setShowFolderPicker(true)}
                        className="p-2.5 bg-[#0f1f3a] hover:bg-[#1a3a5c] text-[#3bb5ff] rounded-xl transition-colors border border-[#1a3a5c] active:scale-95"
                        title="Browse Folders"
                      >
                        <FolderOpen size={20} />
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {Object.entries(localConfig)
                .filter(([_, data]) => data !== null && typeof data === 'object' && !Array.isArray(data))
                .map(([section, data]) => (
                  <ConfigSection
                    key={section}
                    title={section}
                    data={data}
                    path={[section]}
                    config={config}
                    onChange={handleFieldChange}
                  />
                ))}
            </>
          )}
        </div>

        {/* Footer */}
        {!showFolderPicker && (
          <div className="p-6 bg-[#060d1a]/50 border-t border-[#1a3a5c] backdrop-blur-sm flex gap-4">
            <button
              onClick={onClose}
              className="flex-1 py-3.5 bg-[#0f1f3a] hover:bg-[#1a3a5c] text-white rounded-2xl font-bold transition-all duration-150 active:scale-95 border border-[#1a3a5c] uppercase tracking-widest text-xs"
            >
              Discard Changes
            </button>
            <button
              onClick={handleSave}
              className="flex-[2] py-3.5 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] hover:from-[#005a9e] hover:to-[#2aa5ef] text-white rounded-2xl font-bold shadow-lg shadow-[#3bb5ff]/20 transition-all duration-150 active:scale-95 flex items-center justify-center gap-2 uppercase tracking-widest text-xs"
            >
              <Save size={18} />
              Commit Settings
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
