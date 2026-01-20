import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { api } from '../api/endpoints';
import { ApiError } from '../api/errors';
import { FormField } from '../components/FormField';

const schema = z.object({
  recipients: z.string().min(1, 'Wymagany co najmniej 1 odbiorca'),
  subject: z.string().min(1, 'Wymagany temat').max(200),
  body: z.string().min(1, 'Wymagana treść').max(20000),
});

type FormData = z.infer<typeof schema>;

function parseRecipients(raw: string): string[] {
  const parts = raw
    .split(/[,\n]/)
    .map((s) => s.trim())
    .filter(Boolean);
  return Array.from(new Set(parts));
}

export function ComposePage() {
  const nav = useNavigate();
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [files, setFiles] = useState<File[]>([]);

  const { register, handleSubmit, formState } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { recipients: '', subject: '', body: '' },
  });

  const onSubmit = handleSubmit(async (data) => {
    setSubmitError(null);
    const recipients = parseRecipients(data.recipients);
    if (recipients.length === 0) {
      setSubmitError('Podaj co najmniej jednego odbiorcę (username lub email).');
      return;
    }
    try {
      const res = await api.sendMessage({ recipients, subject: data.subject, body: data.body, files });
      nav(`/messages/${encodeURIComponent(res.id)}`);
    } catch (e) {
      setSubmitError(e instanceof ApiError ? e.message : 'Wysyłka nie powiodła się.');
    }
  });

  return (
    <div className="card">
      <h2>Compose</h2>
      {submitError ? <div className="alert error" style={{ marginBottom: 12 }}>{submitError}</div> : null}

      <form onSubmit={onSubmit}>
        <FormField label="Recipients" hint="Username lub email. Wiele: nowe linie lub przecinki." error={formState.errors.recipients?.message}>
          <textarea {...register('recipients')} placeholder="user123\nu456@example.com" />
        </FormField>

        <FormField label="Subject" error={formState.errors.subject?.message}>
          <input {...register('subject')} />
        </FormField>

        <FormField label="Body" error={formState.errors.body?.message}>
          <textarea {...register('body')} />
        </FormField>

        <FormField label="Attachments" hint="Szyfrowanie i HMAC są po stronie backendu.">
          <input
            type="file"
            multiple
            onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
          />
          {files.length ? (
            <div style={{ marginTop: 8, color: 'var(--muted)', fontSize: 12 }}>
              Selected: {files.map((f) => f.name).join(', ')}
            </div>
          ) : null}
        </FormField>

        <div className="row">
          <button type="submit" disabled={formState.isSubmitting}>Send</button>
        </div>
      </form>
    </div>
  );
}
