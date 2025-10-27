import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { matchesAPI } from '../services/api'
import {
  formatKDA,
  formatDuration,
  formatDate,
  getGameModeName,
  getLobbyTypeName,
  calculateKDA,
} from '../utils/formatters'
import './Matches.css'

export default function Matches() {
  const [page, setPage] = useState(1)
  const [showStubs, setShowStubs] = useState(true)
  const [lobbyTypeFilter, setLobbyTypeFilter] = useState<string>('all')
  const [filters, setFilters] = useState({
    hero_id: undefined as number | undefined,
    game_mode: undefined as number | undefined,
  })

  const { data, isLoading } = useQuery({
    queryKey: ['matches', page, filters, showStubs, lobbyTypeFilter],
    queryFn: async () => {
      const response = await matchesAPI.getMatches({
        page,
        page_size: 50,
        include_stubs: showStubs,
        lobby_type: lobbyTypeFilter === 'all' ? undefined : parseInt(lobbyTypeFilter),
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
        <div className="header-actions">
          <div className="filter-group">
            <label htmlFor="lobby-type-filter">Lobby Type:</label>
            <select
              id="lobby-type-filter"
              value={lobbyTypeFilter}
              onChange={(e) => {
                setLobbyTypeFilter(e.target.value)
                setPage(1)
              }}
              className="filter-select"
            >
              <option value="all">All Types</option>
              <option value="0">Normal</option>
              <option value="1">Practice</option>
              <option value="2">Tournament</option>
              <option value="4">Co-op Bots</option>
              <option value="6">Solo Queue</option>
              <option value="7">Ranked</option>
              <option value="8">Solo Mid 1v1</option>
            </select>
          </div>
          <label className="filter-toggle">
            <input
              type="checkbox"
              checked={showStubs}
              onChange={(e) => {
                setShowStubs(e.target.checked)
                setPage(1)
              }}
            />
            <span>Show stubs</span>
          </label>
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
                {data?.matches.map((match: any) => {
                  const isStub = match.has_details === null || match.has_details === false

                  return (
                    <tr key={match.id} className={isStub ? 'stub-match' : ''}>
                      <td>
                        {isStub ? (
                          <span className="text-secondary">No data</span>
                        ) : (
                          <span
                            className={`match-result ${
                              match.radiant_team === match.radiant_win ? 'win' : 'loss'
                            }`}
                          >
                            {match.radiant_team === match.radiant_win ? 'Win' : 'Loss'}
                          </span>
                        )}
                      </td>
                      <td>{isStub ? '-' : `Hero ${match.hero_id}`}</td>
                      <td className="text-secondary">
                        {isStub ? '-' : getGameModeName(match.game_mode)}
                      </td>
                      <td>
                        {isStub ? (
                          <span className="text-secondary">-</span>
                        ) : (
                          <div className="kda-cell">
                            <div>{formatKDA(match.kills, match.deaths, match.assists)}</div>
                            <div className="kda-ratio">
                              {calculateKDA(match.kills, match.deaths, match.assists).toFixed(
                                2
                              )}
                            </div>
                          </div>
                        )}
                      </td>
                      <td className="text-secondary">
                        {isStub ? '-' : `${match.gold_per_min || 0} / ${match.xp_per_min || 0}`}
                      </td>
                      <td className="text-secondary">
                        {isStub ? '-' : formatDuration(match.duration)}
                      </td>
                      <td className="text-secondary">
                        {isStub ? '-' : formatDate(match.start_time)}
                      </td>
                      <td>
                        {isStub ? (
                          <span className="text-secondary">Match {match.id}</span>
                        ) : (
                          <Link to={`/matches/${match.id}`} className="btn-secondary btn-small">
                            Details
                          </Link>
                        )}
                      </td>
                    </tr>
                  )
                })}
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
