export type UserPublic = {
  id: string;
  email: string;
  username: string;
};

export type RegisterRequest = {
  email: string;
  username: string;
  password: string;
};

export type RegisterResponse = {
  user: UserPublic;
};

export type LoginRequest = {
  email: string;
  password: string;
  totp_code?: string;
};

export type LoginResponse = {
  requires_2fa: boolean;
};

export type MeResponse = {
  user: UserPublic;
};

export type TwoFaStatusResponse = {
  enabled: boolean;
};

export type TwoFaSetupResponse = {
  secret: string;
  provisioning_uri: string;
};

export type InboxMessageItem = {
  id: string;
  sender_username: string;
  created_at: string;
  read: boolean;
  has_attachments: boolean;
  authenticity_verified: boolean;
};

export type AttachmentMeta = {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
};

export type MessageDetail = {
  id: string;
  sender_username: string;
  created_at: string;
  subject: string;
  body: string;
  attachments: AttachmentMeta[];
  authenticity_verified: boolean;
};

export type SendMessageResponse = {
  id: string;
};
