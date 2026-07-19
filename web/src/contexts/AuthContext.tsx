import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { onAuthStateChanged, User, signOut as fbSignOut } from 'firebase/auth'
import { auth, isAdminEmail } from '@/firebase'
import { ADMIN_EMAIL_KEY, clearAdminToken, getAdminToken } from '@/lib/api'

interface AuthState {
  user: User | null
  loading: boolean
  isAdmin: boolean
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthState>({} as AuthState)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [adminEmail, setAdminEmail] = useState<string | null>(null)

  useEffect(() => {
    // Restore a JWT-based admin session from localStorage (independent of Firebase).
    const token = getAdminToken()
    if (token) setAdminEmail(localStorage.getItem(ADMIN_EMAIL_KEY))
    const unsub = onAuthStateChanged(auth, u => {
      setUser(u)
      setLoading(false)
    })
    return unsub
  }, [])

  const signOut = async () => {
    // Clear JWT admin session if present.
    if (getAdminToken()) clearAdminToken()
    setAdminEmail(null)
    // Also sign out of Firebase if a Firebase session exists.
    if (auth.currentUser) await fbSignOut(auth)
  }

  // Admin status comes from EITHER a verified JWT admin session OR the
  // Firebase allowlist (Google sign-in fallback).
  const isAdmin = !!adminEmail || (!!user?.email && isAdminEmail(user.email))

  return (
    <AuthContext.Provider value={{ user, loading, isAdmin, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = (): AuthState => useContext(AuthContext)