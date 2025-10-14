import axios from 'axios'
import { auth } from './firebase'

const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

// Create axios instance
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token - PRODUCTION MODE ONLY
api.interceptors.request.use(
  async (config) => {
    if (auth.currentUser) {
      try {
        const token = await auth.currentUser.getIdToken()
        config.headers.Authorization = `Bearer ${token}`
      } catch (error) {
        console.error('Failed to get auth token:', error)
        throw new Error('Authentication required. Please sign in.')
      }
    } else {
      throw new Error('Authentication required. Please sign in.')
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      console.error('Unauthorized access - redirecting to login')
      // You could redirect to login here
    }
    return Promise.reject(error)
  }
)

// API endpoints
export const apiEndpoints = {
  // Auth
  verifyToken: '/auth/verify-token',
  
  // Website Integration
  integrateWebsite: '/integrate-website',
  analyseWebsite: '/analyse-website',
  platformSuggestions: '/platform-suggestions',
  
  // Campaign
  generateCampaign: '/generate-campaign',
  publishCampaign: '/publish-campaign',
  
  // Analytics
  campaignAnalytics: '/campaign-analytics',
}

// Typed API functions
export const apiClient = {
  // Website Integration
  integrateWebsite: async (data: {
    platform: 'shopify' | 'wordpress' | 'custom'
    url: string
    oauth?: any
  }) => {
    const response = await api.post(apiEndpoints.integrateWebsite, data)
    return response.data
  },

  analyseWebsite: async (siteData: any) => {
    const response = await api.post(apiEndpoints.analyseWebsite, { site_data: siteData })
    return response.data
  },

  getPlatformSuggestions: async (productType?: string) => {
    const response = await api.get(apiEndpoints.platformSuggestions, {
      params: { product_type: productType }
    })
    return response.data
  },

  // Campaign
  generateCampaign: async (data: {
    product: any
    platform: string
    budget: number
    language?: string
    goal: string
  }) => {
    const response = await api.post(apiEndpoints.generateCampaign, data)
    return response.data
  },

  publishCampaign: async (data: {
    campaign_draft: any
    platform: string
    publish_mode?: 'dry_run' | 'go_live'
    confirm_token?: string
  }) => {
    const response = await api.post(apiEndpoints.publishCampaign, data)
    return response.data
  },

  // Analytics
  getCampaignAnalytics: async (campaignId: string, platform: string) => {
    const response = await api.get(apiEndpoints.campaignAnalytics, {
      params: { campaign_id: campaignId, platform }
    })
    return response.data
  },
}

export default api
