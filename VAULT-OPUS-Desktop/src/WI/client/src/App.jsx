//App.jsx
import React, { useState, useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import ActionBar from './components/ActionBar';
import FileExplorer from './components/FileExplorer';
import Terminal from './components/Terminal';
import QueuePanel from './components/QueuePanel';
import SettingsModal from './components/SettingsModal';
import VolumeCreationModal from './components/VolumeCreationModal';
import NewVersionUploadModal from './components/NewVersionUploadModal';
import PromptModal from './components/PromptModal';
import SeeVersionsModal from './components/SeeVersionsModal';
import DownloadVersionModal from './components/DownloadVersionModal';
import PasswordPromptModal from './components/PasswordPromptModal';
import AlertModal from './components/AlertModal';
import RenameVolumeModal from './components/RenameVolumeModal';
import DeleteModal from './components/DeleteModal';
import DownloadModal from './components/DownloadModal';
import FullNameModal from './components/FullNameModal';
import OpenVolumeModal from './components/OpenVolumeModal';
import ModifyModal from './components/ModifyModal';
import MakeFolderModal from './components/MakeFolderModal';
import SharablesModal from './components/SharablesModal';
import NukeModal from './components/NukeModal';

export default function App() {
  const [dbs, setDbs] = useState([]);
  const [externalVolumes, setExternalVolumes] = useState(() => {
    const saved = localStorage.getItem('externalVolumes');
    return saved ? JSON.parse(saved) : [];
  });
  const [selectedDb, setSelectedDb] = useState('');
  const [tree, setTree] = useState(null);
  const [currentPath, setCurrentPath] = useState('.');
  const [currentVersion, setCurrentVersion] = useState(null);
  const [selectedItems, setSelectedItems] = useState([]);
  const [terminalOutput, setTerminalOutput] = useState('');
  const [queue, setQueue] = useState([]);
  const [showSettings, setShowSettings] = useState(false);
  const [config, setConfig] = useState(null);
  const [ws, setWs] = useState(null);
  const [promptData, setPromptData] = useState(null);
  const [showVolumeModal, setShowVolumeModal] = useState(false);
  const [pendingUpload, setPendingUpload] = useState(null);

  // Terminal controls
  const [showTerminal, setShowTerminal] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);

  // Recent Volumes
  const [recentVolumes, setRecentVolumes] = useState(() => {
    const saved = localStorage.getItem('recentVolumes');
    return saved ? JSON.parse(saved) : [];
  });

  // New Version Upload Modal state
  const [showNewVersionModal, setShowNewVersionModal] = useState(false);
  const [newVersionTargetPath, setNewVersionTargetPath] = useState('');

  // Volume Rename state
  const [showRenameModal, setShowRenameModal] = useState(false);
  const [dbToRename, setDbToRename] = useState('');

  // See Versions Modal state
  const [showSeeVersionsModal, setShowSeeVersionsModal] = useState(false);
  const [seeVersionsItemPath, setSeeVersionsItemPath] = useState('');

  // Download Version Modal state
  const [downloadVersionItem, setDownloadVersionItem] = useState(null);
  const [showDownloadVersionModal, setShowDownloadVersionModal] = useState(false);
  const [downloadVersionItemPath, setDownloadVersionItemPath] = useState('');
  const [availableVersions, setAvailableVersions] = useState([]);
  // Password Prompt state
  const [passwordPromptItems, setPasswordPromptItems] = useState(null);
  const [pendingDownloadItems, setPendingDownloadItems] = useState(null);

  // Custom Alert state
  const [alertState, setAlertState] = useState({
    type: 'error'
  });

  // Delete Modal state
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteModalOptions, setDeleteModalOptions] = useState({ showVersionControls: false });

  // Download Modal state
  const [showDownloadModal, setShowDownloadModal] = useState(false);

  // Full Name Modal state
  const [showFullNameModal, setShowFullNameModal] = useState(false);
  const [fullNameItem, setFullNameItem] = useState(null);
  const [showOpenVolumeModal, setShowOpenVolumeModal] = useState(false);

  // Modify Modal state
  const [showModifyModal, setShowModifyModal] = useState(false);
  const [modifyOptions, setModifyOptions] = useState(null);
  const [showSharablesModal, setShowSharablesModal] = useState(false);
  const [showMakeFolderModal, setShowMakeFolderModal] = useState(false);

  // NUKE Modal state
  const [showNukeModal, setShowNukeModal] = useState(false);
  const [dbToNuke, setDbToNuke] = useState('');

  const showAlert = (message, title = 'Attention', type = 'error', action = null) => {
    setAlertState({
      isOpen: true,
      title,
      message,
      type,
      action
    });
  };

  // Fetch DBs on mount
  useEffect(() => {
    fetchDbs();
    fetchConfig();

    const handleCreateVolumeClick = (e) => {
      // If there's a pending upload, the modal will handle it via pendingUpload state
      // Otherwise it's a standalone volume creation
      setShowVolumeModal(true);
    };
    window.addEventListener('create-volume', handleCreateVolumeClick);

    const handleOpenSettings = (e) => {
      setShowSettings(true);
    };
    window.addEventListener('open-settings', handleOpenSettings);

    return () => {
      window.removeEventListener('create-volume', handleCreateVolumeClick);
      window.removeEventListener('open-settings', handleOpenSettings);
    };
  }, []);

  // Fetch files when DB changes
  useEffect(() => {
    if (selectedDb) {
      localStorage.setItem('selectedDb', selectedDb);

      // Update recent volumes
      setRecentVolumes(prev => {
        const updated = [selectedDb, ...prev.filter(db => db !== selectedDb)].slice(0, 10);
        localStorage.setItem('recentVolumes', JSON.stringify(updated));
        return updated;
      });

      setCurrentVersion(null);
      fetchFiles(currentPath, null);
    }
  }, [selectedDb]);

  // WebSocket connection
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);

  const connectWS = () => {
    if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);

    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    // Fix: Always target port 8000 for backend if on localhost or PC IP
    let host = window.location.host;
    if (window.location.port === '5173') {
      host = window.location.hostname + ':8000';
    } else if (!window.location.port && window.location.hostname === 'localhost') {
      // Fallback for some environments
      host = 'localhost:8000';
    }

    setConnectionStatus('connecting');
    const socket = new WebSocket(`${proto}//${host}/ws/cli`);
    
    socket.onopen = () => {
      setWs(socket);
      setConnectionStatus('connected');
      reconnectAttemptsRef.current = 0;
      setTerminalOutput(prev => prev + '\n[Connected to VAULT_OPUS CLI]\n');
    };

    socket.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      const taskId = msg.task_id;

      if (msg.type === 'stdout' || msg.type === 'stderr' || msg.type === 'status') {
        if (msg.type === 'stdout' || msg.type === 'stderr') {
          setTerminalOutput(prev => prev + msg.data);
        }

        // Parse output for queue updates
        const line = msg.data || "";

        setQueue(prev => prev.map(item => {
          if (item.id === taskId) {
            let status = item.status;
            let progress = item.progress;

            if (msg.type === 'status' && line.includes('Queued')) {
              status = 'queued';
            } else if (status === 'queued' && (msg.type === 'stdout' || msg.type === 'stderr')) {
              status = 'running';
            }

            if (line.includes('[OP_SUCCESS]')) {
              status = 'completed';
              progress = 100;
            } else if (line.includes('[OP_FAILURE]')) {
              status = 'failed';
            } else {
              const progressMatch = line.match(/Overall.*Progress.*\((\d+)%\)/i) || line.match(/Overall:.*\((\d+)%\)/i);
              if (progressMatch && progressMatch[1]) {
                progress = parseInt(progressMatch[1], 10);
                status = 'running';
              }
            }
            return { ...item, status, progress };
          }
          return item;
        }));
      } else if (msg.type === 'prompt') {
        setPromptData({
          text: msg.prompt,
          isPassword: msg.is_password,
          taskId: msg.task_id // Track which task needs input
        });
      } else if (msg.type === 'exit') {
        setTerminalOutput(prev => prev + `\n[Process ${taskId} exited with code: ${msg.code}]\n`);

        setQueue(prev => prev.map(item => {
          if (item.id === taskId) {
            if (item.status === 'running' || item.status === 'queued') {
              return { ...item, status: msg.code === 0 ? 'completed' : 'failed', progress: msg.code === 0 ? 100 : item.progress };
            }
          }
          return item;
        }));

        // Refresh file list after operations
        fetchFiles(currentPath);
      }
    };

    socket.onclose = () => {
      setWs(null);
      setConnectionStatus('disconnected');
      setTerminalOutput(prev => prev + '\n[Disconnected from VAULT_OPUS CLI]\n');
      
      // Retry logic: up to 3 times, then stop
      if (reconnectAttemptsRef.current < 3) {
        reconnectAttemptsRef.current += 1;
        reconnectTimeoutRef.current = setTimeout(connectWS, 3000);
      }
    };

    socket.onerror = () => {
      socket.close();
    };
  };

  useEffect(() => {
    connectWS();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (ws) ws.close();
    };
  }, []);

  const fetchDbs = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/dbs');
      const data = await res.json();
      const availableDbs = data.dbs || [];
      setDbs(availableDbs);

      // Merge with external volumes
      setDbs(prev => {
        const all = [...availableDbs];
        externalVolumes.forEach(ext => {
          if (!all.includes(ext)) all.push(ext);
        });
        return all;
      });

      // Validate stored selection from localStorage
      const storedDb = localStorage.getItem('selectedDb');
      if (storedDb) {
        if (availableDbs.includes(storedDb) || externalVolumes.includes(storedDb)) {
          setSelectedDb(storedDb);
        } else {
          console.warn(`Stored database "${storedDb}" not found. Clearing selection.`);
          localStorage.removeItem('selectedDb');
          setSelectedDb('');
          setTree(null);
        }
      }
    } catch (e) {
      console.error('Failed to fetch DBs:', e);
    }
  };

  const fetchConfig = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/config');
      const data = await res.json();
      setConfig(data);
    } catch (e) {
      console.error('Failed to fetch config:', e);
    }
  };

  const fetchFiles = async (path, version = currentVersion) => {
    if (!selectedDb) return;
    try {
      let url = `http://localhost:8000/api/listfiles?db=${encodeURIComponent(selectedDb)}&path=${encodeURIComponent(path)}`;
      if (version) {
        url += `&version=${encodeURIComponent(version)}`;
      }
      const res = await fetch(url);
      const data = await res.json();
      setTree(data);
    } catch (e) {
      console.error('Failed to fetch files:', e);
    }
  };

  const handleNavigate = (path) => {
    setCurrentPath(path);
    setSelectedItems([]);
    fetchFiles(path, currentVersion);
  };

  const handleUpload = (files, encryption, password, options) => {
    if (!selectedDb) {
      setPendingUpload({ files, encryption, password, options });
      setShowVolumeModal(true);
      return;
    }

    const effectiveEncryption = (options.minimize && encryption === 'not_automatic') ? 'automatic' : encryption;

    const args = [
      'upload',
      files[0].path,
      '-db', selectedDb,
      '-c', config?.discord?.channel_id || '',
      '--encryption_mode', effectiveEncryption === 'automatic' ? 'automatic' : effectiveEncryption === 'off' ? 'off' : 'not_automatic'
    ];

    if (effectiveEncryption === 'not_automatic' && password) {
      args.push('--password_seed', password);
      if (options.randomSeed) args.push('--random_seed');
    }

    if (options.uploadName) args.push('--upload_name', options.uploadName);
    if (options.uploadMode === 'new_version') {
      args.push('--upload_mode', 'new_version');
      if (options.targetItemPath) args.push('--target_item_path', options.targetItemPath);
    }
    if (options.newVersionString) args.push('--new_version_string', options.newVersionString);
    if (options.nameCheck === false) args.push('--no_name_check');
    if (options.strictnessMode && options.strictnessMode !== 'NA') {
      args.push('--strictness_mode', options.strictnessMode);
    }
    if (options.chunkSizeMb) args.push('--chunk_size_mb', options.chunkSizeMb.toString());
    if (options.idBased) args.push('--id_based');
    if (options.additionMode) {
      args.push('--addition');
      if (options.sourceVersion) args.push('--source_version', options.sourceVersion);
    }
    if (options.minimize) args.push('--minimize', 'yes');
    args.push('--save_hash', options.saveHash ? 'True' : 'False');

    // Add to queue with unique taskId
    const taskId = `upload-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
    const queueItem = {
      id: taskId,
      name: files[0].name,
      status: 'queued',
      progress: 0,
      error: null
    };
    setQueue(prev => [...prev, queueItem]);

    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'run', args, task_id: taskId }));
    }
  };

  const handleDownload = (isFolder) => {
    if (selectedItems.length === 0) return;
    setShowDownloadModal(true);
  };

  const proceedWithDownload = (options) => {
    // Check if any items need passwords
    const encryptedItems = selectedItems.filter(item => item.encryption === 'not_automatic' || item.encryption_mode === 'not_automatic');

    if (encryptedItems.length > 0) {
      setPasswordPromptItems(encryptedItems.map(item => ({
        id: item.itemid,
        name: item.displayName || item.name
      })));
      setPendingDownloadItems({ items: selectedItems, strictnessMode: options.strictnessMode });
      return;
    }

    executeDownload(selectedItems, {}, options.strictnessMode);
  };

  const executeDownload = (itemsToDownload, passwords, strictnessMode = 'NA') => {
    const downloadFolder = localStorage.getItem('VAULT_OPUS_download_folder') || './downloads';

    itemsToDownload.forEach(item => {
      const itemPath = currentPath === '.' ? item.displayName : `${currentPath}/${item.displayName}`;
      const args = [
        'download',
        itemPath,
        '-db', selectedDb,
        '-o', downloadFolder
      ];

      if (Object.keys(passwords).length > 0) {
        args.push('--passwords', JSON.stringify(passwords));
      }

      if (strictnessMode && strictnessMode !== 'NA') {
        args.push('--strictness_mode', strictnessMode);
      }

      const taskId = `download-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
      const queueItem = {
        id: taskId,
        name: item.displayName,
        status: 'queued',
        progress: 0,
        error: null
      };
      setQueue(prev => [...prev, queueItem]);

      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'run', args, task_id: taskId }));
      }
    });
  };

  const handleDelete = (options) => {
    if (selectedItems.length === 0) return;

    selectedItems.forEach(item => {
      const args = ['delete'];

      if (item.itemid) {
        args.push(item.itemid, '--id_based');
      } else {
        const itemPath = currentPath === '.' ? item.displayName : `${currentPath}/${item.displayName}`;
        args.push(itemPath);
      }

      args.push('-db', selectedDb, '--skip_confirmation', 'yes');

      if (options.type === 'hard') args.push('--hard');
      if (options.scope === 'all') args.push('--all_versions', 'yes');
      else if (options.scope === 'specific' && options.version) {
        args.push('--version', options.version);
      } else if (options.scope === 'range' && options.startVersion && options.endVersion) {
        args.push('--start_version', options.startVersion, '--end_version', options.endVersion);
      }

      const taskId = `delete-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
      const queueItem = {
        id: taskId,
        name: item.displayName,
        status: 'queued',
        progress: 0,
        error: null
      };
      setQueue(prev => [...prev, queueItem]);

      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'run', args, task_id: taskId }));
      }
    });
  };

  const openDeleteModal = (options = { showVersionControls: false }) => {
    setDeleteModalOptions(options);
    setShowDeleteModal(true);
  };

  const handleNewVersionRequest = (itemPath) => {
    setNewVersionTargetPath(itemPath);
    setShowNewVersionModal(true);
  };
  const handleOpenVolumes = (selectedDbs) => {
    // Determine which are external (have absolute path indicators)
    const newExternal = selectedDbs.filter(path =>
      path.includes('/') || path.includes('\\')
    );

    if (newExternal.length > 0) {
      setExternalVolumes(prev => {
        const updated = [...prev];
        newExternal.forEach(ext => {
          if (!updated.includes(ext)) updated.push(ext);
        });
        localStorage.setItem('externalVolumes', JSON.stringify(updated));
        return updated;
      });
    }

    // Add to dbs list immediately
    setDbs(prev => {
      const newDbs = [...prev];
      selectedDbs.forEach(dbName => {
        if (!newDbs.includes(dbName)) {
          newDbs.push(dbName);
        }
      });
      return newDbs;
    });

    // Also mark as recent
    setRecentVolumes(prev => {
      const newRecent = [...prev];
      selectedDbs.forEach(dbName => {
        if (!newRecent.includes(dbName)) {
          newRecent.unshift(dbName);
        }
      });
      const trimmed = newRecent.slice(0, 10);
      localStorage.setItem('recentVolumes', JSON.stringify(trimmed));
      return trimmed;
    });

    // Select the first one if none selected
    if (!selectedDb && selectedDbs.length > 0) {
      setSelectedDb(selectedDbs[0]);
    }
  };

  const handleRemoveFromList = (dbPath) => {
    // Remove from external volumes list
    setExternalVolumes(prev => {
      const updated = prev.filter(p => p !== dbPath);
      localStorage.setItem('externalVolumes', JSON.stringify(updated));
      return updated;
    });

    // Remove from active dbs list
    setDbs(prev => prev.filter(p => p !== dbPath));

    // Also remove from recent volumes
    setRecentVolumes(prev => {
      const updated = prev.filter(p => p !== dbPath);
      localStorage.setItem('recentVolumes', JSON.stringify(updated));
      return updated;
    });

    // Clear selection if it was the removed one
    if (selectedDb === dbPath) {
      setSelectedDb('');
      setTree(null);
    }
  };

  const handleDeleteVolume = (dbPath) => {
    showAlert(
      `Are you absolutely sure you want to PERMANENTLY DELETE the volume '${dbPath}'?\n\nThis will remove the database file and its security configuration from the disk. This action CANNOT be undone.`,
      'Confirm Permanent Deletion',
      'error',
      {
        label: '🗑️ YES, DELETE PERMANENTLY',
        isDanger: true,
        onClick: async () => {
          try {
            const res = await fetch('http://localhost:8000/api/dbs/delete', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ db_name: dbPath })
            });

            if (!res.ok) {
              const err = await res.json();
              throw new Error(err.detail || 'Failed to delete volume');
            }

            // Remove from local states
            setExternalVolumes(prev => {
              const updated = prev.filter(p => p !== dbPath);
              localStorage.setItem('externalVolumes', JSON.stringify(updated));
              return updated;
            });

            setDbs(prev => prev.filter(p => p !== dbPath));

            if (selectedDb === dbPath) {
              setSelectedDb('');
              setTree(null);
            }

            await fetchDbs(); // Full refresh
          } catch (e) {
            showAlert(e.message, 'Deletion Error', 'error');
          }
        }
      }
    );
  };

  // NUKE handler
  const handleNukeVolume = (dbPath) => {
    setDbToNuke(dbPath);
    setShowNukeModal(true);
  };

  const executeNuke = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/dbs/nuke', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ db_name: dbToNuke })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to nuke volume');
      }

      const data = await res.json();
      showAlert(
        `☢️ Volume '${dbToNuke}' has been completely wiped!\n\n${data.db_entries_deleted} database entries destroyed.\nThe volume file remains but is now empty.`,
        'NUKE Complete',
        'success'
      );

      // Refresh file list if this was the selected DB
      if (selectedDb === dbToNuke) {
        setTree(null);
        fetchFiles('.');
      }
    } catch (e) {
      showAlert(e.message, 'NUKE Failed', 'error');
    } finally {
      setShowNukeModal(false);
      setDbToNuke('');
    }
  };

  const handleRefresh = () => {
    if (selectedDb) {
      fetchFiles(currentPath, currentVersion);
    }
  };

  const handleSeeVersions = (itemPath) => {
    setSeeVersionsItemPath(itemPath);
    setShowSeeVersionsModal(true);
  };

  const handleShowFullName = (item) => {
    setFullNameItem(item);
    setShowFullNameModal(true);
  };

  const handleModifyConfirm = (data) => {
    const args = ['modify', data.type];

    if (data.type === 'move') {
      args.push(data.src, data.dst);
      if (data.copyMode) args.push('--copy');
      // Use separate src/dst ID-based flags if provided
      if (data.srcIdBased) { args.push('--src_id_based'); }
      if (data.dstIdBased) { args.push('--dst_id_based'); }
    } else {
      args.push(data.item, data.newName);
      if (data.nameMode !== 'D') args.push('--mode', data.nameMode);
    }

    args.push('-db', selectedDb);
    if (data.type !== 'move' && data.idBased) args.push('--id_based');
    if (data.nameCheck === false) args.push('--no_name_check');

    const taskId = `${data.type}-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
    const queueItem = {
      id: taskId,
      name: `${data.type === 'move' ? 'Move' : 'Rename'} ${data.type === 'move' ? data.src : data.item}`,
      status: 'queued',
      progress: 0,
      error: null
    };
    setQueue(prev => [...prev, queueItem]);

    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'run', args, task_id: taskId }));
    }

    setShowModifyModal(false);
  };

  const handleMakeFolder = (folderName) => {
    setShowMakeFolderModal(false);
    setTerminalOutput(prev => prev + `\n[SYSTEM] ${folderName}\n`);
    // Refresh file list
    fetchFiles(currentPath, currentVersion);
  };

  const handleDownloadVersion = (itemPath, item) => {
    setDownloadVersionItemPath(itemPath);
    setDownloadVersionItem(item);
    // Fetch available versions for this item
    if (selectedDb) {
      // First, get the item details to find its itemid
      fetch(`http://localhost:8000/api/listfiles?db=${encodeURIComponent(selectedDb)}&path=${encodeURIComponent(itemPath)}`)
        .then(res => res.json())
        .then(pathData => {
          // Check for errors
          if (pathData.error) {
            throw new Error(pathData.error);
          }

          // Find the itemid from the results
          let itemid = null;
          if (pathData.results) {
            // The itemid is the key in the results object
            const resultKeys = Object.keys(pathData.results);
            if (resultKeys.length > 0) {
              itemid = resultKeys[0];
            }
          }

          if (!itemid) {
            // Try to get itemid from nested structure
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
          return fetch(`http://localhost:8000/api/listfiles?db=${encodeURIComponent(selectedDb)}&itemid=${encodeURIComponent(itemid)}`);
        })
        .then(res => res.json())
        .then(versionsData => {
          // Check for errors
          if (versionsData.error) {
            throw new Error(versionsData.error);
          }

          const versionData = [];

          // Handle different response formats
          if (versionsData.results) {
            // If results is an object with versions as keys
            if (typeof versionsData.results === 'object' && !Array.isArray(versionsData.results)) {
              // Check if it's a version-keyed object
              const keys = Object.keys(versionsData.results);
              if (keys.length > 0 && keys[0].includes('.')) {
                // Version-keyed format
                keys.forEach(version => {
                  if (version.includes('.')) {
                    versionData.push({
                      version: version,
                      upload_timestamp: versionsData.results[version].upload_timestamp || ''
                    });
                  }
                });
              } else {
                // Standard format with itemid as keys
                Object.values(versionsData.results).forEach(item => {
                  if (item.version) {
                    versionData.push({
                      version: item.version,
                      upload_timestamp: item.upload_timestamp || ''
                    });
                  }
                  // Also check contents for versions
                  if (item.contents) {
                    Object.values(item.contents).forEach(subItem => {
                      if (subItem.version) {
                        versionData.push({
                          version: subItem.version,
                          upload_timestamp: subItem.upload_timestamp || ''
                        });
                      }
                    });
                  }
                });
              }
            }
          }

          // If no versions found, try to get from stats
          if (versionData.length === 0 && versionsData.stats && versionsData.stats.total_versions > 0) {
            console.warn('Found versions in stats but could not extract them from results');
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

          console.log('Available versions for', itemPath, ':', sortedVersions);
          setAvailableVersions(sortedVersions);
        })
        .catch(err => {
          console.error('Failed to fetch versions:', err);
          setAvailableVersions([]);
        });
    }
    setShowDownloadVersionModal(true);
  };

  const handleVersionView = (version) => {
    setCurrentVersion(version);
    setShowSeeVersionsModal(false);
    setCurrentPath(seeVersionsItemPath);
    fetchFiles(seeVersionsItemPath, version);
  };

  const handleCreateVolume = async (dbName, files, options) => {
    try {
      const res = await fetch('http://localhost:8000/api/dbs/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ db_name: dbName })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to create volume');
      }

      await fetchDbs();
      setSelectedDb(dbName);
      setShowVolumeModal(false);

      if (pendingUpload) {
        handleUpload(pendingUpload.files, pendingUpload.encryption, pendingUpload.password, pendingUpload.options);
        setPendingUpload(null);
      }
    } catch (e) {
      throw e;
    }
  };

  const handleShareVolume = async (dbName) => {
    try {
      const res = await fetch('http://localhost:8000/api/dbs/share', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ db_name: dbName })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to package volume');
      }

      const data = await res.json();
      showAlert(
        `Volume '${dbName}' packaged successfully!\n📦 Package: ${data.filename}\n📍 Stored in src/SHARABLES folder.`,
        'Volume Packaged',
        'success',
        {
          label: '📁 Open src/SHARABLES Folder',
          onClick: handleOpenSharables
        }
      );
    } catch (e) {
      showAlert(e.message, 'Share Error', 'error');
    }
  };

  const handleOpenSharables = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/dbs/open_sharables', {
        method: 'POST'
      });
      const data = await res.json();
      if (data.status === 'success') {
        setTerminalOutput(prev => prev + `\n[SYSTEM] ${data.message}\n`);
      } else {
        showAlert(data.message, 'Explorer Error', 'error');
      }
    } catch (e) {
      console.error('Failed to open sharables:', e);
      showAlert('Could not connect to backend to open explorer.', 'Connection Error', 'error');
    }
  };

  const handleImportPackage = async (vovPath) => {
    try {
      const res = await fetch('http://localhost:8000/api/dbs/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vov_path: vovPath })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to import package');
      }

      const data = await res.json();
      await fetchDbs();
      showAlert(
        `Package imported successfully!\n📂 Volume: ${data.db_name} is now available.`,
        'Import Success',
        'success'
      );
      return data;
    } catch (e) {
      showAlert(e.message, 'Import Error', 'error');
      throw e;
    }
  };

  const handleSaveConfig = async (newConfig) => {
    try {
      await fetch('http://localhost:8000/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newConfig)
      });
      await fetchConfig();
    } catch (e) {
      console.error('Failed to save config:', e);
    }
  };

  const handleClearTerminal = () => {
    setTerminalOutput('');
  };

  return (
    <div className="flex h-screen bg-[#060d1a] text-gray-100 overflow-hidden relative">
      {showSidebar && (
        <Sidebar
          dbs={dbs}
          recentVolumes={recentVolumes}
          selectedDb={selectedDb}
          onSelectDb={setSelectedDb}
          onRenameVolume={(db) => {
            setDbToRename(db);
            setShowRenameModal(true);
          }}
          onOpenVolume={() => setShowOpenVolumeModal(true)}
          onDeleteVolume={handleDeleteVolume}
          onRemoveFromList={handleRemoveFromList}
          onShareVolume={handleShareVolume}
          onOpenSharables={() => setShowSharablesModal(true)}
          onRefreshDbs={fetchDbs}
          onClose={() => setShowSidebar(false)}
          onNukeVolume={handleNukeVolume}
        />
      )}

      {!showSidebar && (
        <button
          onClick={() => setShowSidebar(true)}
          className="absolute left-4 top-4 z-50 p-2 bg-[#0a1628] border border-[#1a3a5c] rounded-lg text-[#3bb5ff] hover:bg-[#0f1f3a] transition-all active:scale-95 shadow-xl"
          title="Show Sidebar"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
        </button>
      )}

      <div className="flex flex-col flex-1 min-w-0">
        <ActionBar
          onUpload={handleUpload}
          onDownload={handleDownload}
          onDeleteRequest={openDeleteModal}
          selectedItems={selectedItems}
          selectedDb={selectedDb}
          currentPath={currentPath}
          onAlert={showAlert}
        />

        <div className="flex flex-1 min-h-0">
          <div className="flex-1 p-6 overflow-y-auto">
            <FileExplorer
              tree={tree}
              selectedDb={selectedDb}
              currentPath={currentPath}
              onNavigate={handleNavigate}
              selectedItems={selectedItems}
              onSelect={setSelectedItems}
              onNewVersionRequest={handleNewVersionRequest}
              onSeeVersions={handleSeeVersions}
              onDownloadVersion={handleDownloadVersion}
              onDeleteVersionsRequest={() => openDeleteModal({ showVersionControls: true })}
              onShowFullName={handleShowFullName}
              onRefresh={handleRefresh}
              currentVersion={currentVersion}
              onExitVersionView={() => {
                setCurrentVersion(null);
                fetchFiles(currentPath, null);
              }}
              onMoveRequest={(item) => {
                setModifyOptions({ type: 'move', item });
                setShowModifyModal(true);
              }}
              onRenameRequest={(item) => {
                setModifyOptions({ type: 'rename', item });
                setShowModifyModal(true);
              }}
              onMakeFolder={() => setShowMakeFolderModal(true)}
            />
          </div>

          {/* Terminal Panel - Collapsible */}
          {showTerminal && (
            <div className="w-96 border-l border-[#1a3a5c] bg-[#060d1a] flex flex-col transition-all duration-300">
              {/* Terminal Header with Controls */}
              <div className="px-4 py-2 border-b border-[#1a3a5c] flex items-center justify-between bg-[#0a1628]">
                <span className="text-xs font-semibold text-[#3bb5ff]/70 uppercase tracking-wider">
                  Terminal Output
                </span>
                <div className="flex items-center gap-1">
                  <button
                    onClick={handleClearTerminal}
                    className="p-1.5 hover:bg-[#1a3a5c] rounded text-gray-500 hover:text-[#3bb5ff] transition-all duration-150 active:scale-95"
                    title="Clear logs"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                    </svg>
                  </button>
                  <button
                    onClick={() => setShowTerminal(false)}
                    className="p-1.5 hover:bg-[#1a3a5c] rounded text-gray-500 hover:text-[#3bb5ff] transition-all duration-150 active:scale-95"
                    title="Hide terminal"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                  </button>
                </div>
              </div>
              <div className="flex-1 overflow-hidden">
                <Terminal output={terminalOutput} />
              </div>
            </div>
          )}

          {/* Show Terminal Toggle Button (when hidden) */}
          {!showTerminal && (
            <button
              onClick={() => setShowTerminal(true)}
              className="absolute right-4 top-20 z-40 p-2 bg-[#0a1628] border border-[#1a3a5c] rounded-lg text-[#3bb5ff] hover:bg-[#0f1f3a] hover:border-[#3bb5ff]/50 transition-all duration-200 shadow-lg active:scale-95"
              title="Show terminal"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
              </svg>
            </button>
          )}
        </div>

        <QueuePanel
          queue={queue}
          onClear={() => setQueue([])}
        />
      </div>

      {showSettings && (
        <SettingsModal
          isOpen={showSettings}
          onClose={() => setShowSettings(false)}
          config={config}
          onSave={handleSaveConfig}
        />
      )}

      {showVolumeModal && (
        <VolumeCreationModal
          isOpen={showVolumeModal}
          onClose={() => {
            setShowVolumeModal(false);
            setPendingUpload(null);
          }}
          onConfirm={handleCreateVolume}
          uploadFiles={pendingUpload?.files}
          uploadOptions={pendingUpload?.options}
        />
      )}

      {/* New Version Upload Modal */}
      {showNewVersionModal && (
        <NewVersionUploadModal
          targetItemPath={newVersionTargetPath}
          selectedDb={selectedDb}
          onUpload={handleUpload}
          onClose={() => {
            setShowNewVersionModal(false);
            setNewVersionTargetPath('');
          }}
          onAlert={showAlert}
        />
      )}

      {/* See Versions Modal */}
      {showSeeVersionsModal && (
        <SeeVersionsModal
          itemPath={seeVersionsItemPath}
          onClose={() => setShowSeeVersionsModal(false)}
          onVersionSelect={handleVersionView}
        />
      )}

      {/* Download Version Modal */}
      {showDownloadVersionModal && (
        <DownloadVersionModal
          itemPath={downloadVersionItemPath}
          selectedItem={downloadVersionItem}
          selectedDb={selectedDb}
          onClose={() => {
            setShowDownloadVersionModal(false);
            setAvailableVersions([]);
          }}
          onDownload={(args) => {
            const taskId = `download-version-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
            // Add to queue and send command
            const queueItem = {
              id: taskId,
              name: downloadVersionItemPath.split('/').pop() || 'item',
              status: 'queued',
              progress: 0,
              error: null
            };
            setQueue(prev => [...prev, queueItem]);

            if (ws && ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ action: 'run', args, task_id: taskId }));
            }
            setShowDownloadVersionModal(false);
            setAvailableVersions([]);
          }}
          availableVersions={availableVersions}
        />
      )}

      {promptData && (
        <PromptModal
          promptText={promptData.text}
          isPassword={promptData.isPassword}
          onSubmit={(input) => {
            if (ws && ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ action: 'input', data: input, task_id: promptData.taskId }));
            }
            setPromptData(null);
          }}
          onCancel={() => setPromptData(null)}
        />
      )}

      {passwordPromptItems && (
        <PasswordPromptModal
          items={passwordPromptItems}
          onSubmit={(passwords) => {
            setPasswordPromptItems(null);
            if (pendingDownloadItems) {
              const items = pendingDownloadItems.items || pendingDownloadItems;
              const strictnessMode = pendingDownloadItems.strictnessMode || 'NA';
              executeDownload(items, passwords, strictnessMode);
              setPendingDownloadItems(null);
            }
          }}
          onCancel={() => {
            setPasswordPromptItems(null);
            setPendingDownloadItems(null);
          }}
        />
      )}

      <DownloadModal
        isOpen={showDownloadModal}
        onClose={() => setShowDownloadModal(false)}
        onConfirm={proceedWithDownload}
        selectedItems={selectedItems}
      />

      <AlertModal
        isOpen={alertState.isOpen}
        onClose={() => setAlertState(prev => ({ ...prev, isOpen: false }))}
        title={alertState.title}
        message={alertState.message}
        type={alertState.type}
        action={alertState.action}
      />

      {showRenameModal && (
        <RenameVolumeModal
          isOpen={showRenameModal}
          onClose={() => setShowRenameModal(false)}
          currentName={dbToRename}
          onConfirm={handleRenameVolume}
        />
      )}

      {showDeleteModal && (
        <DeleteModal
          isOpen={showDeleteModal}
          onClose={() => setShowDeleteModal(false)}
          onConfirm={handleDelete}
          itemName={selectedItems.length === 1 ? selectedItems[0].displayName : (selectedItems.length > 1 ? `${selectedItems.length} items` : "")}
          selectedItems={selectedItems}
          selectedDb={selectedDb}
          currentPath={currentPath}
          onAlert={showAlert}
          showVersionControls={deleteModalOptions.showVersionControls}
        />
      )}

      {showFullNameModal && (
        <FullNameModal
          isOpen={showFullNameModal}
          onClose={() => {
            setShowFullNameModal(false);
            setFullNameItem(null);
          }}
          item={fullNameItem}
        />
      )}

      <OpenVolumeModal
        isOpen={showOpenVolumeModal}
        onClose={() => setShowOpenVolumeModal(false)}
        onOpenVolumes={handleOpenVolumes}
        onImportPackage={handleImportPackage}
      />

      <SharablesModal
        isOpen={showSharablesModal}
        onClose={() => setShowSharablesModal(false)}
        onImportPackage={handleImportPackage}
      />

      {showModifyModal && (
        <ModifyModal
          type={modifyOptions.type}
          item={modifyOptions.item}
          selectedDb={selectedDb}
          onConfirm={handleModifyConfirm}
          onCancel={() => setShowModifyModal(false)}
        />
      )}

      {showMakeFolderModal && (
        <MakeFolderModal
          selectedDb={selectedDb}
          currentPath={currentPath}
          onConfirm={handleMakeFolder}
          onCancel={() => setShowMakeFolderModal(false)}
        />
      )}

      {/* NUKE Modal */}
      {showNukeModal && (
        <NukeModal
          isOpen={showNukeModal}
          onClose={() => {
            setShowNukeModal(false);
            setDbToNuke('');
          }}
          dbName={dbToNuke}
          onConfirm={executeNuke}
        />
      )}
    </div>
  );
}