import { lazy } from 'react';
import { Route } from 'react-router-dom';

const SmartImportUploadPage = lazy(() =>
  import('./SmartImportUploadPage').then((m) => ({ default: m.SmartImportUploadPage })),
);

const SmartImportStagingPage = lazy(() =>
  import('./SmartImportStagingPage').then((m) => ({ default: m.SmartImportStagingPage })),
);

export const smartImportRoutes = (
  <Route path="smart-import">
    <Route path="upload" element={<SmartImportUploadPage />} />
    <Route path=":jobId" element={<SmartImportStagingPage />} />
  </Route>
);
