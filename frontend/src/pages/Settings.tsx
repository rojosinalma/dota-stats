import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { syncAPI, apiUsageAPI } from '../services/api'
import { formatDate, formatNumber } from '../utils/formatters'
import './Settings.css'

type SyncOption = 'sync_all' | 'sync_missing' | 'sync_incremental'

export default function Settings() {
  const queryClient = useQueryClient()
  const [syncOption, setSyncOption] = useState<SyncOption>('sync_incremental')

  const { data: syncJobs, isLoading, error: syncJobsError } = useQuery({
    queryKey: ['sync', 'jobs'],
    queryFn: async () => {
      const response = await syncAPI.getJobs(20)
      return response.data
    },
    refetchInterval: (query) => {
      // Only refetch if there are running/pending jobs
      const jobs = query.state.data as any[]
      const hasActiveJobs = jobs?.some(
        (job: any) => job.status === 'running' || job.status === 'pending'
      )
      return hasActiveJobs ? 3000 : false
    },
    throwOnError: false,
  })

  const { data: syncStatus, error: syncStatusError } = useQuery({
    queryKey: ['sync', 'status'],
    queryFn: async () => {
      const response = await syncAPI.getStatus()
      return response.data
    },
    refetchInterval: (query) => {
      // Only refetch if syncing
      const status = query.state.data as any
      return status?.is_syncing ? 3000 : false
    },
    throwOnError: false,
  })

  const triggerSync = useMutation({
    mutationFn: () => syncAPI.trigger(syncOption),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sync'] })
    },
  })

  const cancelJob = useMutation({
    mutationFn: (jobId: number) => syncAPI.cancel(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sync'] })
    },
  })

  const cancelAllJobs = useMutation({
    mutationFn: async () => {
      const runningJobs = syncJobs?.filter(
        (job: any) => job.status === 'running' || job.status === 'pending'
      )
      if (runningJobs) {
        await Promise.all(runningJobs.map((job: any) => syncAPI.cancel(job.id)))
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sync'] })
    },
  })

  const getJobTypeName = (jobType: string) => {
    const names: Record<string, string> = {
      full_sync: 'Sync All (Full)',
      incremental_sync: 'Sync Incremental',
      collect_match_ids: 'Collect Match IDs',
      fetch_match_details: 'Fetch Match Details',
      manual_sync: 'Manual Sync',
    }
    return names[jobType] || jobType
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'text-secondary',
      running: 'text-info',
      completed: 'text-success',
      failed: 'text-danger',
      cancelled: 'text-warning',
    }
    return colors[status] || 'text-secondary'
  }

  const hasRunningJobs = syncJobs?.some(
    (job: any) => job.status === 'running' || job.status === 'pending'
  )

  const { data: apiUsage, error: apiUsageError } = useQuery({
    queryKey: ['api-usage', 'summary'],
    queryFn: async () => {
      try {
        const response = await apiUsageAPI.getSummary()
        return response.data
      } catch (error) {
        console.error('API Usage error:', error)
        throw error
      }
    },
    throwOnError: false,
    retry: false,
  })

  return (
    <div className="settings-page">
      <div className="page-header">
        <h1>Settings</h1>
        <p className="text-secondary">Manage your sync jobs and preferences</p>
      </div>

      {(syncJobsError || syncStatusError || apiUsageError) && (
        <div className="card" style={{ marginBottom: '1rem', borderColor: 'var(--danger)' }}>
          <h3 style={{ color: 'var(--danger)' }}>Error Loading Data</h3>
          {syncJobsError && (
            <p className="text-secondary">Failed to load sync jobs: {String(syncJobsError)}</p>
          )}
          {syncStatusError && (
            <p className="text-secondary">Failed to load sync status: {String(syncStatusError)}</p>
          )}
          {apiUsageError && (
            <p className="text-secondary">Failed to load API usage: {String(apiUsageError)}</p>
          )}
        </div>
      )}

      <div className="card sync-controls-card">
        <h2>Sync Options</h2>
        <p className="text-secondary">
          Choose how you want to sync your match data
        </p>

        <div className="sync-options">
          <label className="sync-option-card">
            <input
              type="radio"
              value="sync_all"
              checked={syncOption === 'sync_all'}
              onChange={(e) => setSyncOption(e.target.value as SyncOption)}
              disabled={syncStatus?.is_syncing}
            />
            <div className="option-content">
              <div className="option-title">Sync All</div>
              <div className="option-description">
                Get all historical matches and their details from the beginning
              </div>
            </div>
          </label>

          <label className="sync-option-card">
            <input
              type="radio"
              value="sync_missing"
              checked={syncOption === 'sync_missing'}
              onChange={(e) => setSyncOption(e.target.value as SyncOption)}
              disabled={syncStatus?.is_syncing}
            />
            <div className="option-content">
              <div className="option-title">Sync Missing</div>
              <div className="option-description">
                Only fetch details for matches that don't have data yet
              </div>
            </div>
          </label>

          <label className="sync-option-card">
            <input
              type="radio"
              value="sync_incremental"
              checked={syncOption === 'sync_incremental'}
              onChange={(e) => setSyncOption(e.target.value as SyncOption)}
              disabled={syncStatus?.is_syncing}
            />
            <div className="option-content">
              <div className="option-title">Sync Incremental</div>
              <div className="option-description">
                Only sync new matches since your last stored match
              </div>
            </div>
          </label>
        </div>

        <div className="sync-actions">
          <button
            onClick={() => triggerSync.mutate()}
            disabled={triggerSync.isPending || syncStatus?.is_syncing}
            className="btn-primary"
          >
            {triggerSync.isPending ? 'Starting...' : 'Start Sync'}
          </button>

          {hasRunningJobs && (
            <button
              onClick={() => cancelAllJobs.mutate()}
              disabled={cancelAllJobs.isPending}
              className="btn-danger"
            >
              {cancelAllJobs.isPending ? 'Cancelling...' : 'Cancel All Jobs'}
            </button>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-header-with-action">
          <h2>Sync Job History</h2>
          {import.meta.env.VITE_FLOWER_URL && (
            <a
              href={import.meta.env.VITE_FLOWER_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="text-link"
            >
              View in Flower →
            </a>
          )}
        </div>
        {isLoading && !syncJobs ? (
          <div className="loading-screen">
            <div className="spinner"></div>
          </div>
        ) : (
          <div className="jobs-table-container">
            <table className="jobs-table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Progress</th>
                  <th>Started</th>
                  <th>Completed</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {syncJobs?.map((job: any) => (
                  <tr key={job.id}>
                    <td>{getJobTypeName(job.job_type)}</td>
                    <td>
                      <span className={`status-badge ${getStatusColor(job.status)}`}>
                        {job.status}
                      </span>
                    </td>
                    <td>
                      {job.status === 'running' || job.status === 'completed' ? (
                        <div className="job-progress">
                          <span className="progress-text">
                            {job.processed_matches || 0} / {job.total_matches || '?'}
                          </span>
                          {job.total_matches > 0 && (
                            <div className="progress-bar-small">
                              <div
                                className="progress-fill"
                                style={{
                                  width: `${
                                    (job.processed_matches / job.total_matches) * 100
                                  }%`,
                                }}
                              ></div>
                            </div>
                          )}
                        </div>
                      ) : (
                        <span className="text-secondary">-</span>
                      )}
                    </td>
                    <td className="text-secondary">
                      {job.started_at ? formatDate(job.started_at) : '-'}
                    </td>
                    <td className="text-secondary">
                      {job.completed_at ? formatDate(job.completed_at) : '-'}
                    </td>
                    <td>
                      {(job.status === 'running' || job.status === 'pending') && (
                        <button
                          onClick={() => cancelJob.mutate(job.id)}
                          disabled={cancelJob.isPending}
                          className="btn-secondary btn-small"
                        >
                          Cancel
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                {(!syncJobs || syncJobs.length === 0) && (
                  <tr>
                    <td colSpan={6} className="text-center text-secondary">
                      No sync jobs found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {apiUsage && (
        <div className="card">
          <h2>API Usage & Cost Tracking</h2>
          <p className="text-secondary">
            {apiUsage.has_api_key
              ? 'Using OpenDota API key - tracking costs'
              : 'Using free tier - limited to 2000 calls/day'}
          </p>

          <div className="usage-stats">
            <div className="usage-summary">
              <div className="usage-card">
                <div className="usage-label">Total API Calls</div>
                <div className="usage-value">{formatNumber(apiUsage.total_calls)}</div>
              </div>

              {apiUsage.has_api_key && (
                <>
                  <div className="usage-card">
                    <div className="usage-label">Total Cost</div>
                    <div className="usage-value cost">${(apiUsage.total_cost ?? 0).toFixed(4)}</div>
                  </div>

                  <div className="usage-card">
                    <div className="usage-label">Est. Monthly Cost</div>
                    <div className="usage-value">${(apiUsage.estimated_monthly_cost ?? 0).toFixed(2)}/mo</div>
                  </div>
                </>
              )}

              {!apiUsage.has_api_key && apiUsage.daily_limit_remaining !== null && (
                <div className="usage-card">
                  <div className="usage-label">Daily Limit Remaining</div>
                  <div className="usage-value">{apiUsage.daily_limit_remaining} / 2000</div>
                </div>
              )}
            </div>

            {apiUsage.opendota_stats && apiUsage.opendota_stats.total_calls > 0 && (
              <div className="provider-stats">
                <h3>OpenDota API</h3>
                <div className="stats-grid">
                  <div className="stat-item">
                    <span className="stat-label">Success Rate:</span>
                    <span className="stat-value">
                      {apiUsage.opendota_stats.total_calls > 0
                        ? ((apiUsage.opendota_stats.success_calls / apiUsage.opendota_stats.total_calls) * 100).toFixed(1)
                        : '0.0'}%
                    </span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Calls with Key:</span>
                    <span className="stat-value">{formatNumber(apiUsage.opendota_stats.calls_with_key)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Failed Calls:</span>
                    <span className="stat-value text-danger">{formatNumber(apiUsage.opendota_stats.failed_calls)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Total Cost:</span>
                    <span className="stat-value">${apiUsage.opendota_stats.total_cost.toFixed(4)}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
