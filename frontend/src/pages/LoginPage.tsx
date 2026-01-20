import { useState } from 'react';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Link, useNavigate } from 'react-router-dom';
import { FormField } from '../components/FormField';
import { useAuth } from '../auth/AuthContext';
import { ApiError, UnauthorizedError } from '../api/errors';
import { useQueryParam } from '../hooks/useQueryParam';

const schema = z.object({
  email: z.string().email('Nieprawidłowy email'),
  password: z.string().min(1, 'Wymagane'),
});

type FormData = z.infer<typeof schema>;

export function LoginPage() {
  const auth = useAuth();
  const nav = useNavigate();
  const emailPrefill = useQueryParam('email') ?? '';
  const next = useQueryParam('next') ?? '/';

  const [submitError, setSubmitError] = useState<string | null>(null);

  const { register, handleSubmit, formState, getValues } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { email: emailPrefill, password: '' },
  });

  const onSubmit = handleSubmit(async (data) => {
    setSubmitError(null);
    try {
      await auth.login({ email: data.email, password: data.password });
      nav(next);
    } catch (e) {
      if (e instanceof UnauthorizedError) {
        setSubmitError('Nieprawidłowy email/hasło. Jeśli masz włączone 2FA, użyj weryfikacji TOTP.');
        return;
      }
      setSubmitError(e instanceof ApiError ? e.message : 'Logowanie nie powiodło się.');
    }
  });

  return (
    <div className="card">
      <h2>Login</h2>
      {submitError ? <div className="alert error" style={{ marginBottom: 12 }}>{submitError}</div> : null}
      <form onSubmit={onSubmit}>
        <FormField label="Email" error={formState.errors.email?.message}>
          <input type="email" autoComplete="email" {...register('email')} />
        </FormField>
        <FormField label="Password" error={formState.errors.password?.message}>
          <input type="password" autoComplete="current-password" {...register('password')} />
        </FormField>
        <div className="row">
          <button type="submit" disabled={formState.isSubmitting}>Login</button>
          <Link to={`/2fa?email=${encodeURIComponent(getValues('email'))}&next=${encodeURIComponent(next)}`}>Use 2FA</Link>
          <span style={{ color: 'var(--muted)' }}>
            Brak konta? <Link to="/register">Register</Link>
          </span>
        </div>
      </form>
    </div>
  );
}
