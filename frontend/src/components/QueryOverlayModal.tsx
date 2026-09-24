import ResearcherQueryBar from './ResearcherQueryBar';

interface QueryOverlayModalProps {
  isOpen: boolean;
  onClose: () => void;
  onExecuteQuery: (result: any) => void;
}

export default function QueryOverlayModal({ isOpen, onClose, onExecuteQuery }: QueryOverlayModalProps) {
  if (!isOpen) return null;

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(2, 6, 23, 0.85)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '80px 20px 20px'
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          backgroundColor: '#0b1329',
          border: '1px solid #1e293b',
          borderRadius: '12px',
          width: '100%',
          maxWidth: '780px',
          boxShadow: '0 20px 40px rgba(0,0,0,0.6)',
          overflow: 'hidden'
        }}
      >
        <div style={{
          display: 'flex',
          justifyContent: 'flex-end',
          padding: '10px 14px 0'
        }}>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              fontSize: '18px',
              cursor: 'pointer'
            }}
          >
            ✕
          </button>
        </div>

        <div style={{ padding: '0 6px 16px' }}>
          <ResearcherQueryBar
            onExecuteQuery={(result) => {
              onExecuteQuery(result);
            }}
          />
        </div>
      </div>
    </div>
  );
}