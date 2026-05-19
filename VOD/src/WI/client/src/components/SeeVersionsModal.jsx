//SeeVersionsModal.jsx
import React, { useState, useEffect } from 'react';

export default function SeeVersionsModal({ itemPath, onClose }) {
    const [versions, setVersions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedDb, setSelectedDb] = useState(localStorage.getItem('selectedDb') || '');

    useEffect(() => {
        fetchVersions();
    }, [itemPath, selectedDb]);

    const fetchVersions = async () => {
        if (!selectedDb) {
            setError('No database selected');
            setLoading(false);
            return;
        }

        try {
            setLoading(true);
            setError(null);

            // First, get the item details to find its itemid
            const pathResponse = await fetch(
                `http://localhost:8000/api/listfiles?db=${encodeURIComponent(selectedDb)}&path=${encodeURIComponent(itemPath)}`
            );

            if (!pathResponse.ok) {
                throw new Error('Failed to fetch item details');
            }

            const pathData = await pathResponse.json();

            // Find the itemid from the results
            let itemid = null;

            // Check if there's an error in the response
            if (pathData.error) {
                throw new Error(pathData.error);
            }

            if (pathData.results) {
                // The itemid is the key in the results object
                const resultKeys = Object.keys(pathData.results);
                if (resultKeys.length > 0) {
                    itemid = resultKeys[0];
                }
            }

            if (!itemid) {
                // Try to get itemid from the nested structure
                if (pathData.results && typeof pathData.results === 'object') {
                    const firstKey = Object.keys(pathData.results)[0];
                    if (firstKey && pathData.results[firstKey].itemid) {
                        itemid = pathData.results[firstKey].itemid;
                    }
                }
            }

            if (!itemid) {
                throw new Error('Could not find item identifier for path: ' + itemPath);
            }

            // Now fetch all versions using the itemid
            const versionsResponse = await fetch(
                `http://localhost:8000/api/listfiles?db=${encodeURIComponent(selectedDb)}&itemid=${encodeURIComponent(itemid)}`
            );

            if (!versionsResponse.ok) {
                throw new Error('Failed to fetch versions');
            }

            const versionsData = await versionsResponse.json();

            // Extract versions from the results
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

            // Sort versions by upload_timestamp (newest first)
            const sortedVersions = versionData
                .sort((a, b) => {
                    // Sort by upload_timestamp, newest first
                    if (a.upload_timestamp && b.upload_timestamp) {
                        return new Date(b.upload_timestamp) - new Date(a.upload_timestamp);
                    }
                    // If no timestamp, fallback to version number sorting
                    const aParts = a.version.split('.').map(Number);
                    const bParts = b.version.split('.').map(Number);
                    for (let i = 0; i < Math.max(aParts.length, bParts.length); i++) {
                        const aVal = aParts[i] || 0;
                        const bVal = bParts[i] || 0;
                        if (aVal !== bVal) {
                            return bVal - aVal;
                        }
                    }
                    return 0;
                })
                .map(v => v.version);

            setVersions(sortedVersions);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };


    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
            <div className="bg-[#0a1628] border border-[#1a3a5c] rounded-xl shadow-2xl w-full max-w-lg max-h-[70vh] overflow-hidden animate-in zoom-in-95 duration-200">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-[#1a3a5c] sticky top-0 bg-[#0a1628] z-10">
                    <div className="flex items-center gap-2">
                        <svg className="w-5 h-5 text-[#3bb5ff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                        <h3 className="text-sm font-bold text-white uppercase tracking-wider">See Versions</h3>
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

                {/* Versions List */}
                <div className="p-4 flex-1 overflow-hidden flex flex-col">
                    {loading ? (
                        <div className="flex items-center justify-center h-full text-gray-500 text-sm">
                            <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-[#3bb5ff]" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Loading versions...
                        </div>
                    ) : error ? (
                        <div className="flex flex-col items-center justify-center h-full text-red-400 bg-red-900/10 rounded-lg border border-red-900/20 p-4">
                            <svg className="w-8 h-8 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                            <p className="text-sm">{error}</p>
                        </div>
                    ) : versions.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-gray-500 opacity-50">
                            <svg className="w-12 h-12 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                            <p>No versions found</p>
                        </div>
                    ) : (
                        <div className="flex-1 overflow-y-auto">
                            <div className="text-xs text-[#3bb5ff]/70 uppercase tracking-wider mb-2">
                                Available Versions ({versions.length})
                            </div>
                            <div className="space-y-1">
                                {versions.map((version, idx) => (
                                    <div
                                        key={idx}
                                        className="flex items-center justify-between px-3 py-2 bg-[#0f1f3a] border border-[#1a3a5c] rounded hover:bg-[#1a3a5c] hover:border-[#3bb5ff]/50 transition-all duration-150 group"
                                    >
                                        <div className="flex items-center gap-2">
                                            <svg className="w-4 h-4 text-[#3bb5ff] group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                            </svg>
                                            <span className="text-sm text-gray-300 font-mono">Version {version}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}