import { lazy } from 'react';
import { Route } from 'react-router-dom';

const ProposalsListPage = lazy(() =>
  import('./pages/ProposalsListPage').then((m) => ({ default: m.ProposalsListPage })),
);
const ProposalCreatePage = lazy(() =>
  import('./pages/ProposalCreatePage').then((m) => ({ default: m.ProposalCreatePage })),
);
const ProposalDetailPage = lazy(() =>
  import('./pages/ProposalDetailPage').then((m) => ({ default: m.ProposalDetailPage })),
);
const ProposalImportPage = lazy(() =>
  import('./pages/ProposalImportPage').then((m) => ({ default: m.ProposalImportPage })),
);
const ProposalCpuPage = lazy(() =>
  import('./pages/ProposalCpuPage').then((m) => ({ default: m.ProposalCpuPage })),
);
const ProposalHistogramaPage = lazy(() =>
  import('./pages/ProposalHistogramaPage').then((m) => ({ default: m.HistogramaPage })),
);
const MatchReviewPage = lazy(() =>
  import('./pages/MatchReviewPage').then((m) => ({ default: m.MatchReviewPage })),
);
// F2-09: Approval queue — must be declared BEFORE :id to avoid React Router confusion
const ApprovalQueuePage = lazy(() =>
  import('./pages/ApprovalQueuePage').then((m) => ({ default: m.ApprovalQueuePage })),
);

export const proposalRoutes = (
  <Route path="propostas">
    <Route index element={<ProposalsListPage />} />
    <Route path="nova" element={<ProposalCreatePage />} />
    {/* Static routes before parameterized :id */}
    <Route path="aprovacoes" element={<ApprovalQueuePage />} />
    <Route path=":id" element={<ProposalDetailPage />} />
    <Route path=":id/importar" element={<ProposalImportPage />} />
    <Route path=":id/histograma" element={<ProposalHistogramaPage />} />
    <Route path=":id/match-review" element={<MatchReviewPage />} />
    <Route path=":id/cpu" element={<ProposalCpuPage />} />
  </Route>
);
