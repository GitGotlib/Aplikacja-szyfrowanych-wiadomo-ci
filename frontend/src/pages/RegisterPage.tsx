import { useState } from 'react';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate } from 'react-router-dom';
import { FormField } from '../components/FormField';
import { useAuth } from '../auth/AuthContext';
import { ApiError } from '../api/errors';

const schema = z.object({
  email: z.string().email('Nieprawidłowy email'),
  username: z.string().min(3).max(32).regex(/^[a-zA-Z0-9_\-]+$/, 'Dozwolone: litery, cyfry, _ i -'),
  password: z.string().min(12, 'Min. 12 znaków').max(256),
});

type FormData = z.infer<typeof schema>;

export function RegisterPage() {
  const auth = useAuth();
  const nav = useNavigate();
  const [submitError, setSubmitError] = useState<string | null>(null);

  const { register, handleSubmit, formState } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { email: '', username: '', password: '' },
  });

  const onSubmit = handleSubmit(async (data) => {
    setSubmitError(null);
    try {
      await auth.register(data);
      nav(`/login?email=${encodeURIComponent(data.email)}`);
    } catch (e) {
      setSubmitError(e instanceof ApiError ? e.message : 'Rejestracja nie powiodła się.');
    }
  });

  return (
    <div className="card">
      <h2>Register</h2>
      {submitError ? <div className="alert error" style={{ marginBottom: 12 }}>{submitError}</div> : null}
      <form onSubmit={onSubmit}>
        <FormField label="Email" error={formState.errors.email?.message}>
          <input type="email" autoComplete="email" {...register('email')} />
        </FormField>
        <FormField label="Username" error={formState.errors.username?.message}>
          <input autoComplete="username" {...register('username')} />
        </FormField>
        <FormField label="Password" hint="Min. 12 znaków, złożoność wymusza backend." error={formState.errors.password?.message}>
          <input type="password" autoComplete="new-password" {...register('password')} />
        </FormField>
        <div className="row">
          <button type="submit" disabled={formState.isSubmitting}>Create account</button>
        </div>
      </form>
    </div>
  );
}
