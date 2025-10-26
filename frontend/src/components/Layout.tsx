import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { authAPI } from '../services/api'
import './Layout.css'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const { user } = useAuth()
  const location = useLocation()

  const handleLogout = async () => {
    try {
      await authAPI.logout()
      // Force a full page reload to clear all state and redirect to login
      window.location.href = '/'
    } catch (error) {
      console.error('Logout failed:', error)
      // Even if logout fails, clear the session by reloading
      window.location.href = '/'
    }
  }

  const isActive = (path: string) => location.pathname === path

  return (
    <div className="layout">
      <nav className="navbar">
        <div className="navbar-container">
          <Link to="/" className="navbar-brand">
            Dota Stats
          </Link>

          <div className="navbar-links">
            <Link
              to="/"
              className={`nav-link ${isActive('/') ? 'active' : ''}`}
            >
              Dashboard
            </Link>
            <Link
              to="/matches"
              className={`nav-link ${isActive('/matches') ? 'active' : ''}`}
            >
              Matches
            </Link>
            <Link
              to="/heroes"
              className={`nav-link ${isActive('/heroes') ? 'active' : ''}`}
            >
              Heroes
            </Link>
          </div>

          <div className="navbar-user">
            {user && (
              <>
                <div className="user-info">
                  {user.avatar_url && (
                    <img
                      src={user.avatar_url}
                      alt={user.persona_name}
                      className="user-avatar"
                    />
                  )}
                  <span className="user-name">{user.persona_name}</span>
                </div>
                <button onClick={handleLogout} className="btn-secondary">
                  Logout
                </button>
              </>
            )}
          </div>
        </div>
      </nav>

      <main className="main-content">{children}</main>
    </div>
  )
}
