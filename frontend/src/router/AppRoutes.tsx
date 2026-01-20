import { Link, Route, Routes } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { RequireAuth } from './RequireAuth';
import { InboxPage } from '../pages/InboxPage';
import { LoginPage } from '../pages/LoginPage';
import { RegisterPage } from '../pages/RegisterPage';
import { TwoFaPage } from '../pages/TwoFaPage';
import { ComposePage } from '../pages/ComposePage';
import { MessagePage } from '../pages/MessagePage';
import { TwoFaSettingsPage } from '../pages/TwoFaSettingsPage';

export function AppRoutes() {
  const auth = useAuth();

  return (
    <div className="container">
      <div className="row spread" style={{ marginBottom: 16 }}>
        <div className="row" style={{ gap: 10 }}>
          <Link to="/" style={{ fontWeight: 700 }}>Secure Messaging</Link>
          {auth.user ? (
            <span className="badge">{auth.user.username}</span>
          ) : (
            <span className="badge">guest</span>
          )}
        </div>
        <div className="row">
          {auth.user ? (
            <>
              <Link to="/compose">Compose</Link>
              <Link to="/settings/2fa">2FA</Link>
              <button onClick={() => auth.logout()}>Logout</button>
            </>
          ) : (
            <>
              <Link to="/login">Login</Link>
              <Link to="/register">Register</Link>
            </>
          )}
        </div>
      </div>

      {auth.error ? <div className="alert error" style={{ marginBottom: 12 }}>{auth.error}</div> : null}

      <Routes>
        <Route path="/" element={<RequireAuth><InboxPage /></RequireAuth>} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/2fa" element={<TwoFaPage />} />
        <Route path="/compose" element={<RequireAuth><ComposePage /></RequireAuth>} />
        <Route path="/settings/2fa" element={<RequireAuth><TwoFaSettingsPage /></RequireAuth>} />
        <Route path="/messages/:id" element={<RequireAuth><MessagePage /></RequireAuth>} />
        <Route path="*" element={<div className="card">Not found</div>} />
      </Routes>
    </div>
  );
}
