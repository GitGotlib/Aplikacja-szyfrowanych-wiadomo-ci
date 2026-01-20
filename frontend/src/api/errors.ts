export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export class UnauthorizedError extends ApiError {
  constructor() {
    super('Unauthorized', 401);
    this.name = 'UnauthorizedError';
  }
}

export type ValidationErrorPayload = {
  detail?: string;
  errors?: unknown;
};
