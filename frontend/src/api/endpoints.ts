import {
  type InboxMessageItem,
  type LoginRequest,
  type LoginResponse,
  type MeResponse,
  type MessageDetail,
  type RegisterRequest,
  type RegisterResponse,
  type SendMessageResponse,
  type TwoFaSetupResponse,
  type TwoFaStatusResponse,
} from '../types/dto';
import { apiDeleteJson, apiFetchJson, apiPostForm, apiPostJson } from './http';

export const api = {
  register: (payload: RegisterRequest) => apiPostJson<RegisterResponse>('/api/users/register', payload),
  login: (payload: LoginRequest) => apiPostJson<LoginResponse>('/api/auth/login', payload),
  logout: () => apiPostJson<{ ok: boolean }>('/api/auth/logout', {}),
  me: () => apiFetchJson<MeResponse>('/api/users/me'),

  twoFaStatus: () => apiFetchJson<TwoFaStatusResponse>('/api/2fa/status'),
  twoFaSetup: () => apiPostJson<TwoFaSetupResponse>('/api/2fa/setup', {}),
  twoFaEnable: (code: string) => apiPostJson<{ ok: boolean }>('/api/2fa/enable', { code }),
  twoFaDisable: (code: string) => apiPostJson<{ ok: boolean }>('/api/2fa/disable', { code }),

  inbox: () => apiFetchJson<InboxMessageItem[]>('/api/messages/inbox'),
  messageDetail: (id: string) => apiFetchJson<MessageDetail>(`/api/messages/${encodeURIComponent(id)}`),
  deleteMessage: (id: string) => apiDeleteJson<{ ok: boolean }>(`/api/messages/${encodeURIComponent(id)}`),

  sendMessage: (args: { recipients: string[]; subject: string; body: string; files: File[] }) => {
    const form = new FormData();
    form.set('recipients', JSON.stringify(args.recipients));
    form.set('subject', args.subject);
    form.set('body', args.body);
    for (const f of args.files) {
      form.append('files', f);
    }
    return apiPostForm<SendMessageResponse>('/api/messages/send', form);
  },
};
