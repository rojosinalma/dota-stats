import { authAPI } from '../services/api'
import './Login.css'

export default function Login() {
  return (
    <div className="login-page">
      <div className="login-card">
        <h1>Dota Stats</h1>
        <p className="login-subtitle">
          Track your Dota 2 matches and improve your gameplay
        </p>
        <button onClick={authAPI.login} className="btn-steam">
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="currentColor"
            style={{ marginRight: '0.5rem' }}
          >
            <path d="M12 2a10 10 0 0 1 10 10 10 10 0 0 1-10 10C6.48 22 2 17.52 2 12L11.99 12v-.025L8.525 8.5a2.5 2.5 0 0 1 3.5-3.55l3.55 3.55H16a4 4 0 0 1 0 8h-.5v-.025a2.5 2.5 0 1 1-3.5-3.475L8.5 9.5z" />
          </svg>
          Sign in with Steam
        </button>
      </div>
    </div>
  )
}
