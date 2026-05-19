// Terminal.jsx (FOR CLIENT/DESKTOP) from the VAULT OPUS PROJECT version 1-beta-release-5
// ==================== FULL CLIENT/DESKTOP GUI====================
import React, { useEffect, useRef } from 'react';

export default function Terminal({ output }) {
  const endRef = useRef(null);

  // Auto-scroll
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [output]);

  // Process characters so progress bars display correctly
  const processOutput = (raw) => {
    const lines = raw.split('');
    return lines.map(line => {
      const parts = line.split('');
      return parts[parts.length - 1]; // Only keep the last part of a separated line
    }).join('');
  };

  return (
    <div className="h-full flex flex-col font-mono text-xs text-[#3bb5ff] p-4 overflow-y-auto">
      <pre className="whitespace-pre-wrap leading-relaxed break-words">
        {processOutput(output)}
      </pre>
      <div ref={endRef} />
    </div>
  );
}