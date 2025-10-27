import { useQuery } from '@tanstack/react-query'
import { statsAPI, heroesAPI } from '../services/api'
import { formatPercentage } from '../utils/formatters'
import './HeroStats.css'

interface Hero {
  id: number
  name: string
  localized_name: string
  primary_attr: string
  attack_type: string
  roles: string[]
  img: string
  icon: string
}

interface HeroStat {
  hero_id: number
  games_played: number
  wins: number
  losses: number
  win_rate: number
  avg_kills: number
  avg_deaths: number
  avg_assists: number
  avg_kda: number
  avg_gpm: number
  avg_xpm: number
  total_hero_damage: number
  total_tower_damage: number
}

export default function HeroStats() {
  const { data: allHeroes, isLoading: isLoadingHeroes } = useQuery({
    queryKey: ['heroes'],
    queryFn: async () => {
      const response = await heroesAPI.getHeroes()
      return response.data as Hero[]
    },
  })

  const { data: heroStats, isLoading: isLoadingStats } = useQuery({
    queryKey: ['stats', 'heroes'],
    queryFn: async () => {
      const response = await statsAPI.getHeroStats({ limit: 200 })
      return response.data as HeroStat[]
    },
  })

  const isLoading = isLoadingHeroes || isLoadingStats

  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
      </div>
    )
  }

  // Merge heroes with their stats
  const heroesWithStats = allHeroes?.map((hero) => {
    const stats = heroStats?.find((stat) => stat.hero_id === hero.id)
    return {
      hero,
      stats: stats || null,
    }
  }) || []

  // Sort by games played (descending), then alphabetically
  heroesWithStats.sort((a, b) => {
    const gamesA = a.stats?.games_played || 0
    const gamesB = b.stats?.games_played || 0
    if (gamesB !== gamesA) {
      return gamesB - gamesA
    }
    return a.hero.localized_name.localeCompare(b.hero.localized_name)
  })

  const heroesPlayed = heroesWithStats.filter((h) => h.stats).length

  return (
    <div className="hero-stats-page">
      <div className="page-header">
        <div>
          <h1>Hero Statistics</h1>
          <p className="text-secondary">
            {heroesPlayed} of {heroesWithStats.length} heroes played
          </p>
        </div>
      </div>

      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Hero</th>
              <th>Games</th>
              <th>Win Rate</th>
              <th>W-L</th>
              <th>Avg KDA</th>
              <th>K / D / A</th>
              <th>GPM / XPM</th>
              <th>Hero Damage</th>
              <th>Tower Damage</th>
            </tr>
          </thead>
          <tbody>
            {heroesWithStats.map(({ hero, stats }) => (
              <tr key={hero.id} className={!stats ? 'hero-not-played' : ''}>
                <td className="hero-name-cell">{hero.localized_name}</td>
                <td>{stats?.games_played || 0}</td>
                <td>
                  {stats ? (
                    <span className={stats.win_rate >= 50 ? 'text-success' : 'text-danger'}>
                      {formatPercentage(stats.win_rate)}
                    </span>
                  ) : (
                    <span className="text-secondary">-</span>
                  )}
                </td>
                <td className="text-secondary">
                  {stats ? `${stats.wins} - ${stats.losses}` : '-'}
                </td>
                <td className={stats ? 'kda-highlight' : 'text-secondary'}>
                  {stats ? stats.avg_kda.toFixed(2) : '-'}
                </td>
                <td className="text-secondary">
                  {stats
                    ? `${stats.avg_kills.toFixed(1)} / ${stats.avg_deaths.toFixed(1)} / ${stats.avg_assists.toFixed(1)}`
                    : '-'}
                </td>
                <td className="text-secondary">
                  {stats
                    ? `${stats.avg_gpm?.toFixed(0) || 0} / ${stats.avg_xpm?.toFixed(0) || 0}`
                    : '-'}
                </td>
                <td className="text-secondary">
                  {stats ? (stats.total_hero_damage || 0).toLocaleString() : '-'}
                </td>
                <td className="text-secondary">
                  {stats ? (stats.total_tower_damage || 0).toLocaleString() : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
