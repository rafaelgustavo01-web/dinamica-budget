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
const MatchReviewPage = lazy(() =>
  import('./pages/MatchReviewPage').then((m) => ({ default: m.MatchReviewPage })),
);

export const proposalRoutes = (
  <Route path="propostas">
    <Route index element={<ProposalsListPage />} />
    <Route path="nova" element={<ProposalCreatePage />} />
    <Route path=":id" element={<ProposalDetailPage />} />
    <Route path=":id/importar" element={<ProposalImportPage />} />
    <Route path=":id/match-review" element={<MatchReviewPage />} />
    <Route path=":id/cpu" element={<ProposalCpuPage />} />
  </Route>
);
