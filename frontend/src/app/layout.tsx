import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { AuthProvider } from '@/lib/auth-context'
import { Toaster } from 'react-hot-toast'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'MarkezardAI - AI-Powered Marketing Campaigns',
  description: 'Generate high-converting marketing campaigns with AI-powered insights and untapped interest targeting',
  keywords: 'AI marketing, campaign generation, Meta ads, Google ads, untapped interests',
  authors: [{ name: 'MarkezardAI Team' }],
  viewport: 'width=device-width, initial-scale=1',
  themeColor: '#8A2BE2',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} min-h-screen bg-background text-foreground antialiased`}>
        <AuthProvider>
          <div className="relative min-h-screen">
            {/* Background gradient */}
            <div className="fixed inset-0 bg-gradient-to-br from-background via-background to-purple-950/20 pointer-events-none" />
            
            {/* Floating orbs for ambiance */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
              <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-primary/10 rounded-full blur-3xl animate-float" />
              <div className="absolute top-3/4 right-1/4 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }} />
              <div className="absolute top-1/2 left-3/4 w-48 h-48 bg-blue-500/5 rounded-full blur-3xl animate-float" style={{ animationDelay: '4s' }} />
            </div>
            
            {/* Main content */}
            <div className="relative z-10">
              {children}
            </div>
          </div>
          
          {/* Toast notifications */}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: 'rgba(255, 255, 255, 0.1)',
                backdropFilter: 'blur(12px)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#ffffff',
              },
              success: {
                iconTheme: {
                  primary: '#8A2BE2',
                  secondary: '#ffffff',
                },
              },
              error: {
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#ffffff',
                },
              },
            }}
          />
        </AuthProvider>
      </body>
    </html>
  )
}
