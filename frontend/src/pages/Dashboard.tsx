import { useQuery } from '@tanstack/react-query'
import { statsAPI } from '../services/api'
import { formatPercentage, formatNumber } from '../utils/formatters'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import './Dashboard.css'

export default function Dashboard() {
  const { data: dashboard, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const response = await statsAPI.getDashboard()
      return response.data
    },
  })

  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    )
  }

  const stats = dashboard?.player_stats

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h1>Dashboard</h1>
          <p className="text-secondary">Your Dota 2 statistics overview</p>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card card">
          <div className="stat-label">Total Matches</div>
          <div className="stat-value">{formatNumber(stats?.total_matches || 0)}</div>
        </div>

        <div className="stat-card card">
          <div className="stat-label">Win Rate</div>
          <div className="stat-value text-success">
            {formatPercentage(stats?.win_rate || 0)}
          </div>
          <div className="stat-subtext">
            {stats?.total_wins}W - {stats?.total_losses}L
          </div>
        </div>

        <div className="stat-card card">
          <div className="stat-label">Average KDA</div>
          <div className="stat-value">{stats?.avg_kda?.toFixed(2) || '0.00'}</div>
          <div className="stat-subtext">
            {stats?.avg_kills?.toFixed(1)} / {stats?.avg_deaths?.toFixed(1)} /{' '}
            {stats?.avg_assists?.toFixed(1)}
          </div>
        </div>

        <div className="stat-card card">
          <div className="stat-label">Avg GPM / XPM</div>
          <div className="stat-value">
            {stats?.avg_gpm?.toFixed(0) || '0'} / {stats?.avg_xpm?.toFixed(0) || '0'}
          </div>
        </div>
      </div>

      {dashboard?.time_stats && dashboard.time_stats.length > 0 && (
        <div className="card chart-card">
          <h2>Performance Over Time</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={dashboard.time_stats}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="period" stroke="#a0a0a0" />
              <YAxis stroke="#a0a0a0" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1a1f26',
                  border: '1px solid #374151',
                  borderRadius: '0.5rem',
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="win_rate"
                stroke="#10b981"
                name="Win Rate %"
              />
              <Line
                type="monotone"
                dataKey="avg_kda"
                stroke="#3b82f6"
                name="Avg KDA"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="dashboard-row">
        <div className="card hero-stats-card">
          <h2>Most Played Heroes</h2>
          <div className="hero-list">
            {dashboard?.hero_stats?.slice(0, 10).map((hero: any) => (
              <div key={hero.hero_id} className="hero-item">
                <div className="hero-info">
                  <div className="hero-name">Hero {hero.hero_id}</div>
                  <div className="hero-games">{hero.games_played} games</div>
                </div>
                <div className="hero-stats-row">
                  <span className={hero.win_rate >= 50 ? 'text-success' : 'text-danger'}>
                    {formatPercentage(hero.win_rate)} WR
                  </span>
                  <span>{hero.avg_kda.toFixed(2)} KDA</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card players-card">
          <h2>Frequently Played With</h2>
          <div className="players-list">
            {dashboard?.players_encountered?.slice(0, 10).map((player: any) => (
              <div key={player.account_id} className="player-item">
                <div className="player-info">
                  <div className="player-name">
                    {player.persona_name || `Player ${player.account_id}`}
                  </div>
                  <div className="player-games">{player.games_together} games</div>
                </div>
                <div className={player.win_rate >= 50 ? 'text-success' : 'text-danger'}>
                  {formatPercentage(player.win_rate)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
