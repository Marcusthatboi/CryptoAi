import { useState, useEffect, useContext, createContext } from 'react'
import { cryptoAPI } from '../utils/api'

const AuthContext = createContext(null)

const buildStoredUser = () => {
  const storedUsername = localStorage.getItem('username')
  const storedUserId = localStorage.getItem('user_id')

  if (!storedUsername || !storedUserId) {
    return null
  }

  return {
    username: storedUsername,
    user_id: storedUserId,
    is_admin: localStorage.getItem('is_admin') === 'true',
    role: localStorage.getItem('role') || 'user'
  }
}

const persistAuthUser = (authData) => {
  localStorage.setItem('token', authData.access_token)
  localStorage.setItem('username', authData.username)
  localStorage.setItem('user_id', authData.user_id)
  localStorage.setItem('is_admin', authData.is_admin ? 'true' : 'false')
  localStorage.setItem('role', authData.role || (authData.is_admin ? 'admin' : 'user'))

  return {
    username: authData.username,
    user_id: authData.user_id,
    is_admin: Boolean(authData.is_admin),
    role: authData.role || (authData.is_admin ? 'admin' : 'user')
  }
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(null)
  const [loading, setLoading] = useState(true)

  // Check if user is already logged in
  useEffect(() => {
    const storedToken = localStorage.getItem('token')

    if (storedToken) {
      setToken(storedToken)
      setUser(buildStoredUser())

      cryptoAPI.getProfile()
        .then((response) => {
          const profile = response.data
          localStorage.setItem('username', profile.username)
          localStorage.setItem('user_id', profile.user_id)
          localStorage.setItem('is_admin', profile.is_admin ? 'true' : 'false')
          localStorage.setItem('role', profile.role || (profile.is_admin ? 'admin' : 'user'))
          setUser({
            username: profile.username,
            user_id: profile.user_id,
            is_admin: Boolean(profile.is_admin),
            role: profile.role || (profile.is_admin ? 'admin' : 'user')
          })
        })
        .catch(() => {
          localStorage.removeItem('token')
          localStorage.removeItem('username')
          localStorage.removeItem('user_id')
          localStorage.removeItem('is_admin')
          localStorage.removeItem('role')
          setToken(null)
          setUser(null)
        })
        .finally(() => setLoading(false))

      return
    }

    setLoading(false)
  }, [])

  const login = async (username, password) => {
    const response = await cryptoAPI.login(username, password)
    const data = response.data
    const hydratedUser = persistAuthUser(data)

    setToken(data.access_token)
    setUser(hydratedUser)

    return data
  }

  const register = async (username, password, email) => {
    const response = await cryptoAPI.register(username, password, email)
    const data = response.data
    const hydratedUser = persistAuthUser(data)

    setToken(data.access_token)
    setUser(hydratedUser)

    return data
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('user_id')
    localStorage.removeItem('is_admin')
    localStorage.removeItem('role')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
