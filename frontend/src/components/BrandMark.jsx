import React, { useState } from 'react'

const BRAND_LOGO_URL = '/brand-logo.png'

export default function BrandMark({ className = '', title = 'DaCryptoBeast lion logo' }) {
  const [imageFailed, setImageFailed] = useState(false)

  if (!imageFailed) {
    return (
      <img
        src={BRAND_LOGO_URL}
        alt={title}
        className={className}
        loading="eager"
        decoding="async"
        onError={() => setImageFailed(true)}
      />
    )
  }

  return (
    <svg
      className={className}
      viewBox="0 0 64 64"
      role="img"
      aria-label={title}
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="maneShade" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#3a312b" />
          <stop offset="100%" stopColor="#1d1a18" />
        </linearGradient>
      </defs>

      <circle cx="32" cy="32" r="30" fill="#181b1d" stroke="#2f3538" strokeWidth="2" />

      <path
        d="M11 48 C17 43, 24 44, 31 48 C37 44, 45 44, 53 48 L53 56 L11 56 Z"
        fill="#24362f"
      />
      <path d="M16 53 L20 44" stroke="#355246" strokeWidth="2" strokeLinecap="round" />
      <path d="M23 54 L27 45" stroke="#3f5d4f" strokeWidth="2" strokeLinecap="round" />
      <path d="M40 54 L43 45" stroke="#3a584b" strokeWidth="2" strokeLinecap="round" />

      <circle cx="32" cy="29" r="17" fill="url(#maneShade)" />
      <ellipse cx="32" cy="31" rx="11" ry="10" fill="#7a6446" />
      <circle cx="27.5" cy="29" r="1.4" fill="#0f0f0f" />
      <circle cx="36.5" cy="29" r="1.4" fill="#0f0f0f" />
      <path d="M32 31.5 L30.5 34.2 L33.5 34.2 Z" fill="#1f1f1f" />
      <path d="M27 37 C29 39, 35 39, 37 37" stroke="#1f1f1f" strokeWidth="1.8" fill="none" strokeLinecap="round" />

      <path d="M37 36.4 L41.2 34" stroke="#516f53" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M41.2 34 L43.5 30.8" stroke="#4a694d" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M41.2 34 L44.4 34" stroke="#4a694d" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M41.2 34 L43.5 37.2" stroke="#4a694d" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  )
}
