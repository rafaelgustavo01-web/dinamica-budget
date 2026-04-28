import { http, HttpResponse } from 'msw';

export const handlers = [
  // Placeholder handlers — adicionar conforme necessário para smoke tests (F2-DT-C)
  http.get('/api/health', () => {
    return HttpResponse.json({ status: 'ok' });
  }),
];
