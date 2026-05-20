// DownloadVersionModal.jsx (FOR CLIENT/DESKTOP) from the VAULT OPUS PROJECT version 1-beta-release-6-ESEN-2
// ==================== FULL CLIENT/DESKTOP GUI====================
import React, { useState, useEffect } from 'react';

export default function DownloadVersionModal({
    itemPath,
    onClose,
    onDownload,
    availableVersions = [],
    selectedDb = '',
    selectedItem = null
}) {
    const [versionInput, setVersionInput] = useState('');
    const [startVersion, setStartVersion] = useState('');
    const [endVersion, setEndVersion] = useState('');
    const [allVersions, setAllVersions] = useState(false);
    const [strictnessMode, setStrictnessMode] = useState('NA');

    const [localVersions, setLocalVersions] = useState(availableVersions);
    const [loadingVersions, setLoadingVersions] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (selectedItem && selectedDb) {
            fetchVersions();
        } else if (availableVersions.length > 0) {
            setLocalVersions(availableVersions);
        }
    }, [selectedItem, selectedDb, availableVersions]);

    const fetchVersions = async () => {
        try {
            setLoadingVersions(true);
            setError(null);

            let itemid = selectedItem?.itemid;

            if (!itemid && itemPath) {
                const pathResponse = await fetch(
                    `http://localhost:8000/api/listfiles?db=${encodeURIComponent(selectedDb)}&path=${encodeURIComponent(itemPath)}`
                );
                if (!pathResponse.ok) throw new Error('Failed to fetch item details');
                const pathData = await pathResponse.json();

                if (pathData.error) throw new Error(pathData.error);

                if (pathData.results) {
                    const keys = Object.keys(pathData.results);
                    if (keys.length > 0) {
                        itemid = keys[0];
                        if (pathData.results[itemid]?.itemid) {
                            itemid = pathData.results[itemid].itemid;
                        }
                    }
                }
            }

            if (!itemid) throw new Error('Could not find item identifier');

            const versionsResponse = await fetch(
                `http://localhost:8000/api/listfiles?db=${encodeURIComponent(selectedDb)}&itemid=${encodeURIComponent(itemid)}`
            );

            if (!versionsResponse.ok) throw new Error('Failed to fetch versions');
            const versionsData = await versionsResponse.json();

            const versionSet = new Set();
            const versionData = [];

            if (versionsData.results) {
                Object.values(versionsData.results).forEach(item => {
                    if (item.version && !versionSet.has(item.version)) {
                        versionSet.add(item.version);
                        versionData.push({
                            version: item.version,
                            upload_timestamp: item.upload_timestamp || ''
                        });
                    }
                });
            }

            const sortedVersions = versionData
                .sort((a, b) => {
                    if (a.upload_timestamp && b.upload_timestamp) {
                        return new Date(b.upload_timestamp) - new Date(a.upload_timestamp);
                    }
                    const aParts = a.version.split('.').map(Number);
                    const bParts = b.version.split('.').map(Number);
                    for (let i = 0; i < Math.max(aParts.length, bParts.length); i++) {
                        const aVal = aParts[i] || 0;
                        const bVal = bParts[i] || 0;
                        if (aVal !== bVal) return bVal - aVal;
                    }
                    return 0;
                })
                .map(v => v.version);

            setLocalVersions(sortedVersions);
        } catch (err) {
            console.error('Error fetching versions for download modal:', err);
            setError(err.message);
        } finally {
            setLoadingVersions(false);
        }
    };

    const handleDownload = () => {
        let args = ['download', itemPath, '-db', selectedDb, '--download_folder', localStorage.getItem('VAULT_OPUS_download_folder') || './downloads'];

        if (allVersions) {
            args.push('--all_versions', 'yes');
        } else if (startVersion && endVersion) {
            args.push('--st_version', startVersion, '--en_version', endVersion);
        } else if (versionInput) {
            args.push('--version', versionInput);
        }

        if (strictnessMode && strictnessMode !== 'NA') {
            args.push('--strictness_mode', strictnessMode);
        }

        onDownload(args);
        onClose();
    };

    const handleVersionSelect = (version) => {
        setVersionInput(version);
        setStartVersion('');
        setEndVersion('');
        setAllVersions(false);
    };

    const displayVersions = localVersions.length > 0 ? localVersions : availableVersions;

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
            <div className="bg-[#0a1628] border border-[#1a3a5c] rounded-xl shadow-2xl w-full max-w-lg max-h-[85vh] overflow-hidden animate-in zoom-in-95 duration-200 flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-[#1a3a5c] sticky top-0 bg-[#0a1628] z-10">
                    <div className="flex items-center gap-2">
                        <svg className="w-5 h-5 text-[#3bb5ff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4-4m0 0L8 8m4-4v12"></path>
                        </svg>
                        <h3 className="text-sm font-bold text-white uppercase tracking-wider">Download Version</h3>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1 hover:bg-[#0f1f3a] rounded-full transition-colors text-gray-400"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>

                {/* Item Path Info */}
                <div className="mx-4 mt-4 p-3 bg-[#3bb5ff]/10 border border-[#3bb5ff]/30 rounded-lg">
                    <div className="text-[10px] text-[#3bb5ff] uppercase tracking-wider mb-1">Item Path</div>
                    <div className="text-xs text-gray-300 font-mono truncate">{itemPath}</div>
                </div>

                {/* Main Content */}
                <div className="p-4 flex-1 overflow-y-auto custom-scrollbar">
                    {/* Single Version Selection — DROPDOWN */}
                    <div className="mb-4 p-3 bg-[#0f1f3a] border border-[#1a3a5c] rounded-lg">
                        <label className="block text-xs text-[#3bb5ff]/70 uppercase tracking-wider mb-2">
                            Specific Version
                        </label>
                        {loadingVersions ? (
                            <div className="h-9 bg-[#060d1a] border border-[#1a3a5c] rounded animate-pulse" />
                        ) : error ? (
                            <div className="text-xs text-red-400 bg-red-900/10 rounded border border-red-900/20 p-2">
                                Error: {error}
                            </div>
                        ) : (
                            <select
                                value={versionInput}
                                onChange={(e) => {
                                    setVersionInput(e.target.value);
                                    setStartVersion('');
                                    setEndVersion('');
                                    setAllVersions(false);
                                }}
                                className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded px-3 py-2 text-sm focus:border-[#3bb5ff] outline-none text-gray-200 transition-colors"
                            >
                                <option value="">Select version...</option>
                                {displayVersions.map((v, idx) => (
                                    <option key={idx} value={v}>Version {v}</option>
                                ))}
                            </select>
                        )}
                        <div className="text-[10px] text-gray-500 mt-1">
                            Double-click a version below to auto-fill
                        </div>
                    </div>

                    {/* Range Selection Section */}
                    <div className="mb-4 p-3 bg-[#0f1f3a] border border-[#1a3a5c] rounded-lg">
                        <label className="block text-xs text-[#3bb5ff]/70 uppercase tracking-wider mb-2">
                            Version Range Selection
                        </label>
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <label className="block text-[10px] text-gray-400 mb-1">Start Version</label>
                                <select
                                    value={startVersion}
                                    onChange={(e) => {
                                        setStartVersion(e.target.value);
                                        setVersionInput('');
                                        setAllVersions(false);
                                    }}
                                    className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded px-3 py-2 text-sm focus:border-[#3bb5ff] outline-none text-gray-200"
                                >
                                    <option value="">Select start...</option>
                                    {displayVersions.map((v, idx) => (
                                        <option key={idx} value={v}>Version {v}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-[10px] text-gray-400 mb-1">End Version</label>
                                <select
                                    value={endVersion}
                                    onChange={(e) => {
                                        setEndVersion(e.target.value);
                                        setVersionInput('');
                                        setAllVersions(false);
                                    }}
                                    className="w-full bg-[#060d1a] border border-[#1a3a5c] rounded px-3 py-2 text-sm focus:border-[#3bb5ff] outline-none text-gray-200"
                                >
                                    <option value="">Select end...</option>
                                    {displayVersions.map((v, idx) => (
                                        <option key={idx} value={v}>Version {v}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                        {startVersion && endVersion && (
                            <div className="mt-2 text-[10px] text-[#3bb5ff]/70">
                                Will download versions from {startVersion} to {endVersion}
                            </div>
                        )}
                    </div>

                    {/* All Versions Checkbox */}
                    <label
                        className={`flex items-center gap-2 px-3 py-2 rounded cursor-pointer transition-all duration-150 ${allVersions
                            ? 'bg-[#3bb5ff]/20 border border-[#3bb5ff]/50'
                            : 'bg-[#0f1f3a] border border-[#1a3a5c] hover:bg-[#1a3a5c]'
                            }`}
                    >
                        <input
                            type="checkbox"
                            checked={allVersions}
                            onChange={(e) => {
                                setAllVersions(e.target.checked);
                                if (e.target.checked) {
                                    setVersionInput('');
                                    setStartVersion('');
                                    setEndVersion('');
                                }
                            }}
                            className="w-3 h-3 accent-[#3bb5ff]"
                        />
                        <span className="text-xs text-gray-300">Download All Versions</span>
                    </label>

                    {/* Strictness Mode Section */}
                    <div className="mt-4 p-3 bg-[#0f1f3a] border border-[#1a3a5c] rounded-lg">
                        <label className="block text-xs text-[#3bb5ff]/70 uppercase tracking-wider mb-2">
                            Strictness Mode
                        </label>
                        <div className="grid grid-cols-1 gap-2">
                            <button
                                onClick={() => setStrictnessMode('NA')}
                                className={`px-3 py-2.5 rounded-lg border text-left transition-all duration-200 ${strictnessMode === 'NA'
                                    ? 'bg-[#1a3a5c]/40 border-[#3bb5ff] text-white shadow-[0_0_15px_rgba(59,181,255,0.2)]'
                                    : 'bg-[#060d1a] border-[#1a3a5c] text-gray-400 hover:border-[#3bb5ff]/50'
                                    }`}
                            >
                                <div className="font-medium text-xs">NOT ATOMIC (DEFAULT)</div>
                                <div className="text-[10px] opacity-60">Continue downloading on failure</div>
                            </button>

                            <button
                                onClick={() => setStrictnessMode('SA')}
                                className={`px-3 py-2.5 rounded-lg border text-left transition-all duration-200 ${strictnessMode === 'SA'
                                    ? 'bg-[#1a3a5c]/40 border-[#3bb5ff] text-white shadow-[0_0_15px_rgba(59,181,255,0.2)]'
                                    : 'bg-[#060d1a] border-[#1a3a5c] text-gray-400 hover:border-[#3bb5ff]/50'
                                    }`}
                            >
                                <div className="font-medium text-xs">SOFT ATOMIC</div>
                                <div className="text-[10px] opacity-60">Stop immediately, ask before cleanup</div>
                            </button>

                            <button
                                onClick={() => setStrictnessMode('HA')}
                                className={`px-3 py-2.5 rounded-lg border text-left transition-all duration-200 ${strictnessMode === 'HA'
                                    ? 'bg-[#1a3a5c]/40 border-[#3bb5ff] text-white shadow-[0_0_15px_rgba(59,181,255,0.2)]'
                                    : 'bg-[#060d1a] border-[#1a3a5c] text-gray-400 hover:border-[#3bb5ff]/50'
                                    }`}
                            >
                                <div className="font-medium text-xs">HARD ATOMIC</div>
                                <div className="text-[10px] opacity-60">Stop immediately, auto-cleanup</div>
                            </button>
                        </div>
                    </div>

                    {/* Available Versions List */}
                    <div className="mt-4">
                        <div className="text-xs text-[#3bb5ff]/70 uppercase tracking-wider mb-2">
                            Available Versions ({displayVersions.length})
                        </div>
                        {loadingVersions ? (
                            <div className="flex items-center justify-center py-4 text-gray-500 text-sm">
                                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-[#3bb5ff]" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Loading versions...
                            </div>
                        ) : error ? (
                            <div className="text-xs text-red-400 bg-red-900/10 rounded-lg border border-red-900/20 p-3">
                                Error: {error}
                            </div>
                        ) : displayVersions.length === 0 ? (
                            <div className="text-sm text-gray-500 text-center py-4">
                                No versions available
                            </div>
                        ) : (
                            <div className="max-h-32 overflow-y-auto space-y-1">
                                {displayVersions.map((version, idx) => (
                                    <div
                                        key={idx}
                                        onDoubleClick={() => handleVersionSelect(version)}
                                        className={`flex items-center justify-between px-3 py-1.5 rounded text-sm cursor-pointer transition-all duration-150 ${versionInput === version
                                            ? 'bg-[#3bb5ff]/20 border border-[#3bb5ff]/50'
                                            : 'bg-[#0f1f3a] border border-[#1a3a5c] hover:bg-[#1a3a5c]'
                                            }`}
                                        title="Double-click to select"
                                    >
                                        <span className="text-gray-300 font-mono">Version {version}</span>
                                        {versionInput === version && (
                                            <svg className="w-3 h-3 text-[#3bb5ff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                                            </svg>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-[#1a3a5c] bg-[#0a1628] flex gap-2">
                    <button
                        onClick={onClose}
                        className="flex-1 py-2 bg-[#0f1f3a] hover:bg-[#1a3a5c] text-gray-300 rounded text-sm transition-all duration-150 active:scale-95"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleDownload}
                        disabled={!selectedDb || loadingVersions}
                        className="flex-1 py-2 bg-gradient-to-r from-[#006fbe] to-[#3bb5ff] hover:from-[#005a9e] hover:to-[#2aa5ef] text-white rounded text-sm transition-all duration-150 shadow-lg shadow-[#3bb5ff]/20 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Download
                    </button>
                </div>
            </div>
        </div>
    );
}