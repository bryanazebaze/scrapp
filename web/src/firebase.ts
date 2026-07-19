import { initializeApp } from 'firebase/app'
import { getAuth } from 'firebase/auth'

// Provided Firebase project: centralimo-71b0d
// Note: apiKey in Firebase config is a client identifier, NOT a secret.
// It is safe to commit. Real auth security comes from Firebase Auth + server-side ID-token verification.
const firebaseConfig = {
  apiKey: 'AIzaSyCcHKCbwD1WukAHsStB7WO4vSQO58vneHw',
  authDomain: 'centralimo-71b0d.firebaseapp.com',
  projectId: 'centralimo-71b0d',
  storageBucket: 'centralimo-71b0d.firebasestorage.app',
  messagingSenderId: '462226982834',
  appId: '1:462226982834:web:7cc7424ca72317d8c146ab',
  measurementId: 'G-2PK3786Q8E'
}

export const app = initializeApp(firebaseConfig)
export const auth = getAuth(app)

// Admin allowlist — emails that may access /admin routes on the web via the
// Firebase Google sign-in fallback. JWT-authenticated admins (POST /admin/login)
// bypass this allowlist because the backend already verified their credentials.
export const ADMIN_EMAILS = new Set<string>([
  'azebazeaurel@gmail.com',
  'kelcyazef@gmail.com',
])

export const isAdminEmail = (email?: string | null): boolean =>
  !!email && ADMIN_EMAILS.has(email.toLowerCase())
