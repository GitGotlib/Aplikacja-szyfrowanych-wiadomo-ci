import React from 'react';

export function FormField(props: {
  label: string;
  hint?: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div style={{ marginBottom: 12 }}>
      <label>
        {props.label}
      </label>
      {props.children}
      {props.hint ? <div style={{ color: 'var(--muted)', fontSize: 12, marginTop: 6 }}>{props.hint}</div> : null}
      {props.error ? <div style={{ color: 'var(--danger)', fontSize: 12, marginTop: 6 }}>{props.error}</div> : null}
    </div>
  );
}
