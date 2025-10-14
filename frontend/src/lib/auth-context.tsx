'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import { 
  User,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  GoogleAuthProvider,
  signInWithPopup,
  updateProfile
} from 'firebase/auth'
import { auth } from './firebase'
import { api } from './api'
import toast from 'react-hot-toast'

interface UserProfile {
  uid: string
  email: string
  name?: string
  plan: string
  created_at?: string
}

interface AuthContextType {
  user: User | null
  userProfile: UserProfile | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string, name: string) => Promise<void>
  signInWithGoogle: () => Promise<void>
  logout: () => Promise<void>
  refreshProfile: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshProfile = async () => {
    if (!user) return
    
    try {
      const token = await user.getIdToken()
      const response = await api.post('/auth/verify-token', { token })
      setUserProfile(response.data.user)
    } catch (error) {
      console.error('Failed to refresh profile:', error)
    }
  }

  const signIn = async (email: string, password: string) => {
    try {
      const result = await signInWithEmailAndPassword(auth, email, password)
      const token = await result.user.getIdToken()
      
      // Verify token with backend
      const response = await api.post('/auth/verify-token', { token })
      setUserProfile(response.data.user)
      
      toast.success('Welcome back!')
    } catch (error: any) {
      console.error('Sign in error:', error)
      toast.error(error.message || 'Failed to sign in')
      throw error
    }
  }

  const signUp = async (email: string, password: string, name: string) => {
    try {
      const result = await createUserWithEmailAndPassword(auth, email, password)
      
      // Update profile with name
      await updateProfile(result.user, { displayName: name })
      
      const token = await result.user.getIdToken()
      
      // Verify token with backend to create profile
      const response = await api.post('/auth/verify-token', { token })
      setUserProfile(response.data.user)
      
      toast.success('Account created successfully!')
    } catch (error: any) {
      console.error('Sign up error:', error)
      toast.error(error.message || 'Failed to create account')
      throw error
    }
  }

  const signInWithGoogle = async () => {
    try {
      const provider = new GoogleAuthProvider()
      const result = await signInWithPopup(auth, provider)
      const token = await result.user.getIdToken()
      
      // Verify token with backend
      const response = await api.post('/auth/verify-token', { token })
      setUserProfile(response.data.user)
      
      toast.success('Welcome!')
    } catch (error: any) {
      console.error('Google sign in error:', error)
      toast.error(error.message || 'Failed to sign in with Google')
      throw error
    }
  }

  const logout = async () => {
    try {
      await signOut(auth)
      setUserProfile(null)
      toast.success('Signed out successfully')
    } catch (error: any) {
      console.error('Logout error:', error)
      toast.error('Failed to sign out')
      throw error
    }
  }

  useEffect(() => {

    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      setUser(user)
      
      if (user) {
        try {
          const token = await user.getIdToken()
          const response = await api.post('/auth/verify-token', { token })
          setUserProfile(response.data.user)
        } catch (error) {
          console.error('Failed to verify token:', error)
          setUserProfile(null)
        }
      } else {
        setUserProfile(null)
      }
      
      setLoading(false)
    })

    return unsubscribe
  }, [])

  const value: AuthContextType = {
    user,
    userProfile,
    loading,
    signIn,
    signUp,
    signInWithGoogle,
    logout,
    refreshProfile,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
