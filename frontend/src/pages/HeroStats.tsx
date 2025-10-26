import { useQuery } from '@tanstack/react-query'
import { statsAPI } from '../services/api'
import { formatPercentage } from '../utils/formatters'
import './HeroStats.css'

export default function HeroStats() {
  const { data: heroStats, isLoading } = useQuery({
    queryKey: ['stats', 'heroes'],
    queryFn: async () => {
      const response = await statsAPI.getHeroStats({ limit: 100 })
      return response.data
    },
  })

  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
      </div>
    )
  }

  return (
    <div className="hero-stats-page">
      <div className="page-header">
        <div>
          <h1>Hero Statistics</h1>
          <p className="text-secondary">
            {heroStats?.length || 0} heroes played
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
            {heroStats?.map((hero: any) => (
              <tr key={hero.hero_id}>
                <td className="hero-name-cell">Hero {hero.hero_id}</td>
                <td>{hero.games_played}</td>
                <td>
                  <span className={hero.win_rate >= 50 ? 'text-success' : 'text-danger'}>
                    {formatPercentage(hero.win_rate)}
                  </span>
                </td>
                <td className="text-secondary">
                  {hero.wins} - {hero.losses}
                </td>
                <td className="kda-highlight">{hero.avg_kda.toFixed(2)}</td>
                <td className="text-secondary">
                  {hero.avg_kills.toFixed(1)} / {hero.avg_deaths.toFixed(1)} /{' '}
                  {hero.avg_assists.toFixed(1)}
                </td>
                <td className="text-secondary">
                  {hero.avg_gpm?.toFixed(0) || 0} / {hero.avg_xpm?.toFixed(0) || 0}
                </td>
                <td className="text-secondary">
                  {(hero.total_hero_damage || 0).toLocaleString()}
                </td>
                <td className="text-secondary">
                  {(hero.total_tower_damage || 0).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
