import React from 'react'
import { useLanguage } from '../context/LanguageContext'
import { LANGUAGE_LABELS, SUPPORTED_LANGUAGES } from '../i18n/translations'
import './LanguageSelector.css'

export default function LanguageSelector() {
  const { language, setLanguage, t } = useLanguage()

  return (
    <label className="language-selector" htmlFor="language-select">
      <span>{t('common_language', 'Language')}</span>
      <select
        id="language-select"
        value={language}
        onChange={(event) => setLanguage(event.target.value)}
      >
        {SUPPORTED_LANGUAGES.map((code) => (
          <option key={code} value={code}>
            {LANGUAGE_LABELS[code] || code.toUpperCase()}
          </option>
        ))}
      </select>
    </label>
  )
}