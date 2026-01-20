import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

export function RequireAuth(props: { children: React.ReactNode }) {
  const auth = useAuth();
  const loc = useLocation();

  if (auth.loading) {
    return (
      <div className="container">
        <div className="card">Ładowanie…</div>
      </div>
    );
  }

  if (!auth.user) {
    return <Navigate to={`/login?next=${encodeURIComponent(loc.pathname)}`} replace />;
  }

  return <>{props.children}</>;
}
