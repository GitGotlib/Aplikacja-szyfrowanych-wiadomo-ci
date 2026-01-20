import { useState } from 'react';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate } from 'react-router-dom';
import { FormField } from '../components/FormField';
import { useAuth } from '../auth/AuthContext';
import { ApiError, UnauthorizedError } from '../api/errors';
import { useQueryParam } from '../hooks/useQueryParam';
import { api } from '../api/endpoints';

const schema = z.object({
  email: z.string().email('Nieprawidłowy email'),
  password: z.string().min(1, 'Wymagane'),
  totp_code: z.string().regex(/^[0-9]{6,8}$/, 'Kod 6-8 cyfr'),
});

type FormData = z.infer<typeof schema>;

export function TwoFaPage() {
  const auth = useAuth();
  const nav = useNavigate();
  const emailPrefill = useQueryParam('email') ?? '';
  const next = useQueryParam('next') ?? '/';

  const [submitError, setSubmitError] = useState<string | null>(null);

  const { register, handleSubmit, formState } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { email: emailPrefill, password: '', totp_code: '' },
  });

  const onSubmit = handleSubmit(async (data) => {
    setSubmitError(null);
    try {
      await api.login2fa({ email: data.email, password: data.password, totp_code: data.totp_code });
      await auth.refreshMe();
      nav(next);
    } catch (e) {
      if (e instanceof UnauthorizedError) {
        setSubmitError('Nieprawidłowe dane lub kod 2FA.');
        return;
      }
      setSubmitError(e instanceof ApiError ? e.message : 'Weryfikacja 2FA nie powiodła się.');
    }
  });

  return (
    <div className="card">
      <h2>2FA Verification</h2>
      <div className="alert" style={{ marginBottom: 12 }}>
        Jeśli Twoje konto ma włączone 2FA, po poprawnym haśle backend wymaga kodu TOTP (RFC 6238).
      </div>
      {submitError ? <div className="alert error" style={{ marginBottom: 12 }}>{submitError}</div> : null}
      <form onSubmit={onSubmit}>
        <FormField label="Email" error={formState.errors.email?.message}>
          <input type="email" autoComplete="email" {...register('email')} />
        </FormField>
        <FormField label="Password" error={formState.errors.password?.message}>
          <input type="password" autoComplete="current-password" {...register('password')} />
        </FormField>
        <FormField label="TOTP code" hint="Kod z aplikacji Authenticator." error={formState.errors.totp_code?.message}>
          <input inputMode="numeric" autoComplete="one-time-code" {...register('totp_code')} />
        </FormField>
        <div className="row">
          <button type="submit" disabled={formState.isSubmitting}>Verify & Login</button>
        </div>
      </form>
    </div>
  );
}
