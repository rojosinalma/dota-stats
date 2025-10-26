import { useQuery } from '@tanstack/react-query'
import { authAPI } from '../services/api'

export interface User {
  id: number
  steam_id: string
  persona_name: string
  profile_url?: string
  avatar_url?: string
  created_at: string
  last_sync_at?: string
}

export function useAuth() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      try {
        const response = await authAPI.getMe()
        return response.data as User
      } catch (err) {
        return null
      }
    },
    retry: false,
  })

  return {
    user: data,
    isLoading,
    isAuthenticated: !!data,
    error,
  }
}
