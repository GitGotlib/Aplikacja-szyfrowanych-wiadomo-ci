import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/endpoints';
import { ApiError, UnauthorizedError } from '../api/errors';
import type { InboxMessageItem } from '../types/dto';

function fmt(ts: string): string {
  try {
    return new Date(ts).toLocaleString();
  } catch {
    return ts;
  }
}

export function InboxPage() {
  const [items, setItems] = useState<InboxMessageItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.inbox();
      setItems(data);
    } catch (e) {
      if (e instanceof UnauthorizedError) {
        setError('Brak autoryzacji. Zaloguj się ponownie.');
      } else {
        setError(e instanceof ApiError ? e.message : 'Nie udało się pobrać skrzynki.');
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <div className="card">
      <div className="row spread" style={{ marginBottom: 12 }}>
        <h2>Inbox</h2>
        <div className="row">
          <button onClick={() => void load()} disabled={loading}>Refresh</button>
          <Link to="/compose">Compose</Link>
        </div>
      </div>

      {error ? <div className="alert error" style={{ marginBottom: 12 }}>{error}</div> : null}

      {loading ? (
        <div className="alert">Ładowanie…</div>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Status</th>
              <th>From</th>
              <th>Created</th>
              <th>Attachments</th>
              <th>Auth</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((m) => (
              <tr key={m.id}>
                <td>{m.read ? <span className="badge">read</span> : <span className="badge danger">unread</span>}</td>
                <td>{m.sender_username}</td>
                <td>{fmt(m.created_at)}</td>
                <td>{m.has_attachments ? 'yes' : 'no'}</td>
                <td>{m.authenticity_verified ? <span className="badge ok">ok</span> : <span className="badge">-</span>}</td>
                <td><Link to={`/messages/${encodeURIComponent(m.id)}`}>Open</Link></td>
              </tr>
            ))}
            {items.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ color: 'var(--muted)' }}>No messages.</td>
              </tr>
            ) : null}
          </tbody>
        </table>
      )}
    </div>
  );
}
