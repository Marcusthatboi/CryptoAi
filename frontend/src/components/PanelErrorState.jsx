import React from 'react'
import './PanelErrorState.css'

export default function PanelErrorState({
  title,
  message,
  onRetry,
  retryLabel = 'Retry',
  className = ''
}) {
  return (
    <div className={`panel-error-state ${className}`.trim()} role="alert" aria-live="polite">
      {title ? <h3>{title}</h3> : null}
      <p>{message || 'Something went wrong while loading this panel.'}</p>
      {onRetry ? (
        <button type="button" className="panel-error-retry-btn" onClick={onRetry}>
          {retryLabel}
        </button>
      ) : null}
    </div>
  )
}
