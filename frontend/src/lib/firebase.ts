import { initializeApp, getApps } from 'firebase/app'
import { getAuth } from 'firebase/auth'
import { getFirestore } from 'firebase/firestore'

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
}

// Validate Firebase configuration - PRODUCTION MODE ONLY
const validateFirebaseConfig = () => {
  const requiredFields = ['apiKey', 'authDomain', 'projectId', 'appId']
  const missing = requiredFields.filter(field => !firebaseConfig[field as keyof typeof firebaseConfig])
  
  if (missing.length > 0) {
    throw new Error(`Missing required Firebase configuration: ${missing.join(', ')}. Please check your environment variables.`)
  }
}

// Initialize Firebase - PRODUCTION MODE ONLY
validateFirebaseConfig()

const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0]
console.log('✅ Firebase initialized successfully')

// Initialize Firebase Authentication and get a reference to the service
export const auth = getAuth(app)

// Initialize Cloud Firestore and get a reference to the service
export const db = getFirestore(app)

export default app
