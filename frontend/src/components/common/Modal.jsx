// src/components/common/Modal.jsx
import React, { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';
import { cn } from '../../utils/cn';

/**
 * Accessible Modal Dialog with keyboard ESC dismissal & background backdrop
 */
const Modal = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  maxWidth = 'max-w-lg',
  className = '',
}) => {
  const modalRef = useRef(null);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    }

    return () => {
      document.body.style.overflow = '';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/75 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Dialog Surface */}
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? 'modal-title' : undefined}
        className={cn(
          'relative w-full rounded-[14px] bg-[var(--bg-surface)] border border-[var(--border-strong)] p-5 sm:p-6 shadow-2xl text-[var(--text-primary)] animate-fade-in z-10 max-h-[90vh] overflow-y-auto',
          maxWidth,
          className
        )}
      >
        <div className="flex items-start justify-between gap-4 pb-3 border-b border-[var(--border-subtle)]">
          <div>
            {title && (
              <h2 id="modal-title" className="text-base font-semibold tracking-tight text-[var(--text-primary)]">
                {title}
              </h2>
            )}
            {description && (
              <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                {description}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-[var(--text-muted)] hover:text-[var(--text-primary)] p-1 rounded-[6px] hover:bg-[var(--bg-elevated)] transition-colors cursor-pointer"
            aria-label="Close dialog"
          >
            <X size={16} />
          </button>
        </div>

        <div className="mt-4">{children}</div>
      </div>
    </div>,
    document.body
  );
};

export default Modal;

