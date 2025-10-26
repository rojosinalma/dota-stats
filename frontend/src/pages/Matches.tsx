import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { matchesAPI } from '../services/api'
import {
  formatKDA,
  formatDuration,
  formatDate,
  getGameModeName,
  calculateKDA,
} from '../utils/formatters'
import './Matches.css'

export default function Matches() {
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState({
    hero_id: undefined as number | undefined,
    game_mode: undefined as number | undefined,
  })

  const { data, isLoading } = useQuery({
    queryKey: ['matches', page, filters],
    queryFn: async () => {
      const response = await matchesAPI.getMatches({
        page,
        page_size: 50,
        ...filters,
      })
      return response.data
    },
  })

  const totalPages = data ? Math.ceil(data.total / data.page_size) : 0

  return (
    <div className="matches-page">
      <div className="page-header">
        <div>
          <h1>Match History</h1>
          <p className="text-secondary">
            {data?.total || 0} total matches
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="loading-screen">
          <div className="spinner"></div>
        </div>
      ) : (
        <>
          <div className="card matches-table">
            <table>
              <thead>
                <tr>
                  <th>Result</th>
                  <th>Hero</th>
                  <th>Mode</th>
                  <th>KDA</th>
                  <th>GPM/XPM</th>
                  <th>Duration</th>
                  <th>Date</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {data?.matches.map((match: any) => (
                  <tr key={match.id}>
                    <td>
                      <span
                        className={`match-result ${
                          match.radiant_team === match.radiant_win ? 'win' : 'loss'
                        }`}
                      >
                        {match.radiant_team === match.radiant_win ? 'Win' : 'Loss'}
                      </span>
                    </td>
                    <td>Hero {match.hero_id}</td>
                    <td className="text-secondary">
                      {getGameModeName(match.game_mode)}
                    </td>
                    <td>
                      <div className="kda-cell">
                        <div>{formatKDA(match.kills, match.deaths, match.assists)}</div>
                        <div className="kda-ratio">
                          {calculateKDA(match.kills, match.deaths, match.assists).toFixed(
                            2
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="text-secondary">
                      {match.gold_per_min || 0} / {match.xp_per_min || 0}
                    </td>
                    <td className="text-secondary">
                      {formatDuration(match.duration)}
                    </td>
                    <td className="text-secondary">
                      {formatDate(match.start_time)}
                    </td>
                    <td>
                      <Link to={`/matches/${match.id}`} className="btn-secondary btn-small">
                        Details
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="pagination">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn-secondary"
              >
                Previous
              </button>
              <span className="pagination-info">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="btn-secondary"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
