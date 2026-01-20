import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api } from '../api/endpoints';
import { ApiError, UnauthorizedError } from '../api/errors';
import type { MessageDetail } from '../types/dto';

function fmt(ts: string): string {
  try {
    return new Date(ts).toLocaleString();
  } catch {
    return ts;
  }
}

export function MessagePage() {
  const { id } = useParams();
  const nav = useNavigate();

  const [data, setData] = useState<MessageDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load(messageId: string) {
    setLoading(true);
    setError(null);
    try {
      const d = await api.messageDetail(messageId);
      setData(d);
    } catch (e) {
      if (e instanceof UnauthorizedError) {
        setError('Brak autoryzacji.');
      } else {
        setError(e instanceof ApiError ? e.message : 'Nie udało się pobrać wiadomości.');
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!id) return;
    void load(id);
  }, [id]);

  async function onDelete() {
    if (!id) return;
    if (!confirm('Usunąć wiadomość?')) return;
    try {
      await api.deleteMessage(id);
      nav('/');
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Usuwanie nie powiodło się.');
    }
  }

  return (
    <div className="card">
      <div className="row spread" style={{ marginBottom: 12 }}>
        <div className="row">
          <Link to="/">← Inbox</Link>
        </div>
        <div className="row">
          <button className="btn-danger" onClick={() => void onDelete()} disabled={!id}>Delete</button>
        </div>
      </div>

      {error ? <div className="alert error" style={{ marginBottom: 12 }}>{error}</div> : null}

      {loading ? (
        <div className="alert">Ładowanie…</div>
      ) : data ? (
        <>
          <div className="row" style={{ marginBottom: 8 }}>
            <span className="badge">from: {data.sender_username}</span>
            <span className="badge">{fmt(data.created_at)}</span>
            {data.authenticity_verified ? <span className="badge ok">auth ok</span> : <span className="badge danger">auth fail</span>}
          </div>
          <h2 style={{ marginTop: 0 }}>{data.subject}</h2>
          <div className="alert" style={{ whiteSpace: 'pre-wrap', marginBottom: 12 }}>{data.body}</div>

          <h3 style={{ marginTop: 0 }}>Attachments</h3>
          {data.attachments.length === 0 ? (
            <div className="alert" style={{ color: 'var(--muted)' }}>No attachments.</div>
          ) : (
            <ul>
              {data.attachments.map((a) => (
                <li key={a.id}>
                  <a href={`/api/messages/${encodeURIComponent(data.id)}/attachments/${encodeURIComponent(a.id)}`}>
                    {a.filename} ({a.size_bytes} bytes)
                  </a>
                </li>
              ))}
            </ul>
          )}
        </>
      ) : (
        <div className="alert">Nie znaleziono.</div>
      )}
    </div>
  );
}
