import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { matchesAPI } from '../services/api'
import {
  formatKDA,
  formatDuration,
  formatDate,
  getGameModeName,
  getLobbyTypeName,
  formatNumber,
} from '../utils/formatters'
import './MatchDetail.css'

export default function MatchDetail() {
  const { matchId } = useParams()

  const { data: match, isLoading } = useQuery({
    queryKey: ['match', matchId],
    queryFn: async () => {
      const response = await matchesAPI.getMatch(Number(matchId))
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

  if (!match) {
    return <div>Match not found</div>
  }

  const won = match.radiant_team === match.radiant_win

  return (
    <div className="match-detail-page">
      <div className="breadcrumb">
        <Link to="/matches" className="breadcrumb-link">
          Matches
        </Link>
        <span className="breadcrumb-separator">/</span>
        <span>Match {match.id}</span>
      </div>

      <div className="card match-header">
        <div className="match-result-banner" data-result={won ? 'win' : 'loss'}>
          <h1>{won ? 'Victory' : 'Defeat'}</h1>
          <p>{getGameModeName(match.game_mode)}</p>
        </div>

        <div className="match-info-grid">
          <div className="info-item">
            <div className="info-label">Match ID</div>
            <div className="info-value">{match.id}</div>
          </div>
          <div className="info-item">
            <div className="info-label">Duration</div>
            <div className="info-value">{formatDuration(match.duration)}</div>
          </div>
          <div className="info-item">
            <div className="info-label">Date</div>
            <div className="info-value">{formatDate(match.start_time)}</div>
          </div>
          <div className="info-item">
            <div className="info-label">Lobby Type</div>
            <div className="info-value">{getLobbyTypeName(match.lobby_type)}</div>
          </div>
        </div>
      </div>

      <div className="stats-section">
        <h2>Your Performance</h2>
        <div className="performance-grid">
          <div className="card perf-card">
            <div className="perf-label">KDA</div>
            <div className="perf-value">
              {formatKDA(match.kills, match.deaths, match.assists)}
            </div>
            <div className="perf-ratio">
              {match.deaths === 0
                ? match.kills + match.assists
                : ((match.kills + match.assists) / match.deaths).toFixed(2)}{' '}
              ratio
            </div>
          </div>

          <div className="card perf-card">
            <div className="perf-label">GPM / XPM</div>
            <div className="perf-value">
              {match.gold_per_min || 0} / {match.xp_per_min || 0}
            </div>
          </div>

          <div className="card perf-card">
            <div className="perf-label">Last Hits / Denies</div>
            <div className="perf-value">
              {match.last_hits || 0} / {match.denies || 0}
            </div>
          </div>

          <div className="card perf-card">
            <div className="perf-label">Hero Damage</div>
            <div className="perf-value">{formatNumber(match.hero_damage || 0)}</div>
          </div>

          <div className="card perf-card">
            <div className="perf-label">Tower Damage</div>
            <div className="perf-value">{formatNumber(match.tower_damage || 0)}</div>
          </div>

          <div className="card perf-card">
            <div className="perf-label">Healing</div>
            <div className="perf-value">{formatNumber(match.hero_healing || 0)}</div>
          </div>
        </div>
      </div>

      {match.players && match.players.length > 0 && (
        <div className="card">
          <h2>All Players</h2>
          <table>
            <thead>
              <tr>
                <th>Team</th>
                <th>Hero</th>
                <th>K/D/A</th>
                <th>GPM/XPM</th>
                <th>Damage</th>
                <th>Net Worth</th>
              </tr>
            </thead>
            <tbody>
              {match.players.map((player: any, index: number) => (
                <tr key={index}>
                  <td>
                    <span className={player.player_slot < 128 ? 'team-radiant' : 'team-dire'}>
                      {player.player_slot < 128 ? 'Radiant' : 'Dire'}
                    </span>
                  </td>
                  <td>Hero {player.hero_id}</td>
                  <td>
                    {formatKDA(
                      player.kills || 0,
                      player.deaths || 0,
                      player.assists || 0
                    )}
                  </td>
                  <td className="text-secondary">
                    {player.gold_per_min || 0} / {player.xp_per_min || 0}
                  </td>
                  <td className="text-secondary">
                    {formatNumber(player.hero_damage || 0)}
                  </td>
                  <td className="text-secondary">
                    {formatNumber(player.net_worth || 0)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
