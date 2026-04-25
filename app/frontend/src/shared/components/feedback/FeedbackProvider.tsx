import { Alert, type AlertColor, Snackbar } from '@mui/material';
import {
  createContext,
  type PropsWithChildren,
  useContext,
  useMemo,
  useState,
} from 'react';

interface FeedbackState {
  open: boolean;
  message: string;
  severity: AlertColor;
}

interface FeedbackContextValue {
  showMessage: (message: string, severity?: AlertColor) => void;
}

const FeedbackContext = createContext<FeedbackContextValue | null>(null);

export function FeedbackProvider({ children }: PropsWithChildren) {
  const [state, setState] = useState<FeedbackState>({
    open: false,
    message: '',
    severity: 'success',
  });

  const value = useMemo<FeedbackContextValue>(
    () => ({
      showMessage(message, severity = 'success') {
        setState({
          open: true,
          message,
          severity,
        });
      },
    }),
    [],
  );

  return (
    <FeedbackContext.Provider value={value}>
      {children}
      <Snackbar
        open={state.open}
        autoHideDuration={4_500}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        onClose={() => setState((current) => ({ ...current, open: false }))}
      >
        <Alert
          onClose={() => setState((current) => ({ ...current, open: false }))}
          severity={state.severity}
          variant="standard"
          sx={{ minWidth: 320, boxShadow: 6 }}
        >
          {state.message}
        </Alert>
      </Snackbar>
    </FeedbackContext.Provider>
  );
}

export function useFeedback() {
  const context = useContext(FeedbackContext);

  if (!context) {
    throw new Error('useFeedback must be used within FeedbackProvider.');
  }

  return context;
}
