import React from 'react'
import { useNavigate } from 'react-router-dom'
import './UpgradePrompt.css'

export default function UpgradePrompt({
  title = 'Upgrade to unlock this feature',
  message,
  ctaLabel = 'View Plans',
  compact = false,
  className = ''
}) {
  const navigate = useNavigate()

  return (
    <div className={`upgrade-prompt ${compact ? 'compact' : ''} ${className}`.trim()}>
      <p className="upgrade-prompt-title">{title}</p>
      {message && <p className="upgrade-prompt-message">{message}</p>}
      <button className="upgrade-prompt-btn" onClick={() => navigate('/pricing')}>
        {ctaLabel}
      </button>
    </div>
  )
}
