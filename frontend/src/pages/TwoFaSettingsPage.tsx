import { useEffect, useState } from 'react';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { api } from '../api/endpoints';
import { ApiError } from '../api/errors';
import type { TwoFaSetupResponse } from '../types/dto';
import { FormField } from '../components/FormField';

const codeSchema = z.object({
  code: z.string().regex(/^[0-9]{6,8}$/, 'Kod 6-8 cyfr'),
});

type CodeForm = z.infer<typeof codeSchema>;

export function TwoFaSettingsPage() {
  const [status, setStatus] = useState<boolean | null>(null);
  const [setup, setSetup] = useState<TwoFaSetupResponse | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const enableForm = useForm<CodeForm>({ resolver: zodResolver(codeSchema), defaultValues: { code: '' } });
  const disableForm = useForm<CodeForm>({ resolver: zodResolver(codeSchema), defaultValues: { code: '' } });

  async function refresh() {
    setErr(null);
    setMsg(null);
    try {
      const s = await api.twoFaStatus();
      setStatus(s.enabled);
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : 'Nie udało się pobrać statusu 2FA.');
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function onSetup() {
    setErr(null);
    setMsg(null);
    try {
      const s = await api.twoFaSetup();
      setSetup(s);
      setMsg('Wygenerowano sekret. Zeskanuj URI w aplikacji Authenticator, potem włącz 2FA kodem.');
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : 'Setup 2FA nie powiódł się.');
    }
  }

  async function onEnable(data: CodeForm) {
    setErr(null);
    setMsg(null);
    try {
      await api.twoFaEnable(data.code);
      setMsg('2FA włączone.');
      enableForm.reset();
      await refresh();
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : 'Włączenie 2FA nie powiodło się.');
    }
  }

  async function onDisable(data: CodeForm) {
    setErr(null);
    setMsg(null);
    try {
      await api.twoFaDisable(data.code);
      setMsg('2FA wyłączone.');
      disableForm.reset();
      await refresh();
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : 'Wyłączenie 2FA nie powiodło się.');
    }
  }

  return (
    <div className="card">
      <h2>2FA Settings</h2>
      <div className="row" style={{ marginBottom: 12 }}>
        <span className="badge">status: {status === null ? '...' : status ? 'enabled' : 'disabled'}</span>
        <button onClick={() => void refresh()}>Refresh</button>
      </div>

      {err ? <div className="alert error" style={{ marginBottom: 12 }}>{err}</div> : null}
      {msg ? <div className="alert ok" style={{ marginBottom: 12 }}>{msg}</div> : null}

      <div className="row" style={{ marginBottom: 12 }}>
        <button onClick={() => void onSetup()}>Generate / Show TOTP secret</button>
      </div>

      {setup ? (
        <div className="alert" style={{ marginBottom: 12 }}>
          <div><b>Secret:</b> {setup.secret}</div>
          <div style={{ marginTop: 8 }}>
            <b>Provisioning URI:</b>
            <div style={{ wordBreak: 'break-all' }}>{setup.provisioning_uri}</div>
          </div>
        </div>
      ) : null}

      <div className="row" style={{ alignItems: 'flex-start' }}>
        <div style={{ flex: 1, minWidth: 280 }}>
          <h3 style={{ marginTop: 0 }}>Enable 2FA</h3>
          <form onSubmit={enableForm.handleSubmit((d) => onEnable(d))}>
            <FormField label="TOTP code" error={enableForm.formState.errors.code?.message}>
              <input inputMode="numeric" autoComplete="one-time-code" {...enableForm.register('code')} />
            </FormField>
            <button type="submit" disabled={enableForm.formState.isSubmitting}>Enable</button>
          </form>
        </div>

        <div style={{ flex: 1, minWidth: 280 }}>
          <h3 style={{ marginTop: 0 }}>Disable 2FA</h3>
          <form onSubmit={disableForm.handleSubmit((d) => onDisable(d))}>
            <FormField label="TOTP code" error={disableForm.formState.errors.code?.message}>
              <input inputMode="numeric" autoComplete="one-time-code" {...disableForm.register('code')} />
            </FormField>
            <button className="btn-danger" type="submit" disabled={disableForm.formState.isSubmitting}>Disable</button>
          </form>
        </div>
      </div>
    </div>
  );
}
