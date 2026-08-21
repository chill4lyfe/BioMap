import React from 'react';

export const Spinner: React.FC = () => {
  return (
    <div className="flex flex-col items-center gap-5">
      <div className="helix-loader" aria-hidden="true">
        {/* Strand 1 */}
        <span />
        <span />
        <span />
        <span />
        <span />
        <span />
        <span />
        <span />
        
        {/* Strand 2 (Reverse phase) */}
        <span />
        <span />
        <span />
        <span />
        <span />
        <span />
        <span />
        <span />
      </div>

      <div className="font-mono text-[11px] tracking-[0.28em] uppercase text-blue-300">
        Processing cellular sequence
      </div>
    </div>
  );
};