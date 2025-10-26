import axios from 'axios'

const api = axios.create({
  baseURL: '/',
  withCredentials: true,
})

// Auth
export const authAPI = {
  getMe: () => api.get('/auth/me'),
  login: () => {
    window.location.href = '/auth/login'
  },
  logout: () => api.post('/auth/logout'),
}

// Matches
export const matchesAPI = {
  getMatches: (params?: {
    page?: number
    page_size?: number
    hero_id?: number
    game_mode?: number
    start_date?: string
    end_date?: string
  }) => api.get('/matches', { params }),
  getMatch: (matchId: number) => api.get(`/matches/${matchId}`),
}

// Stats
export const statsAPI = {
  getDashboard: () => api.get('/stats/dashboard'),
  getPlayerStats: (params?: {
    hero_id?: number
    game_mode?: number
    start_date?: string
    end_date?: string
  }) => api.get('/stats/player', { params }),
  getHeroStats: (params?: {
    hero_id?: number
    game_mode?: number
    start_date?: string
    end_date?: string
    limit?: number
  }) => api.get('/stats/heroes', { params }),
  getPlayersEncountered: (limit?: number) =>
    api.get('/stats/players-encountered', { params: { limit } }),
  getTimeStats: () => api.get('/stats/time-based'),
}

// Sync
export const syncAPI = {
  trigger: (jobType: string = 'incremental_sync') =>
    api.post('/sync/trigger', { job_type: jobType }),
  cancel: (jobId: number) => api.post(`/sync/cancel/${jobId}`),
  getJobs: (limit?: number) => api.get('/sync/jobs', { params: { limit } }),
  getJob: (jobId: number) => api.get(`/sync/jobs/${jobId}`),
  getStatus: () => api.get('/sync/status'),
}

// Heroes
export const heroesAPI = {
  getHeroes: () => api.get('/heroes'),
}

export default api
