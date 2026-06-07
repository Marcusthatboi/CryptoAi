import React, { createContext, useContext, useMemo, useState } from 'react'
import { SUPPORTED_LANGUAGES, translations } from '../i18n/translations'

const LanguageContext = createContext(null)

const DEFAULT_LANGUAGE = 'en'
const STORAGE_KEY = 'cryptoai-language'

function normalizeLanguage(value) {
  const language = String(value || '').trim().toLowerCase()
  return SUPPORTED_LANGUAGES.includes(language) ? language : DEFAULT_LANGUAGE
}

function getInitialLanguage() {
  const stored = window.localStorage.getItem(STORAGE_KEY)
  return normalizeLanguage(stored)
}

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(getInitialLanguage)

  const setLanguage = (nextLanguage) => {
    const normalized = normalizeLanguage(nextLanguage)
    setLanguageState(normalized)
    window.localStorage.setItem(STORAGE_KEY, normalized)
  }

  const value = useMemo(() => {
    const dictionary = translations[language] || translations[DEFAULT_LANGUAGE]

    const t = (key, fallback = '') => {
      if (dictionary[key]) {
        return dictionary[key]
      }
      if (translations[DEFAULT_LANGUAGE]?.[key]) {
        return translations[DEFAULT_LANGUAGE][key]
      }
      return fallback || key
    }

    return {
      language,
      setLanguage,
      t
    }
  }, [language])

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider')
  }
  return context
}