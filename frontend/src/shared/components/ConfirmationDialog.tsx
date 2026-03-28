import WarningAmberOutlinedIcon from '@mui/icons-material/WarningAmberOutlined';
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
} from '@mui/material';
import type { PropsWithChildren } from 'react';

interface ConfirmationDialogProps extends PropsWithChildren {
  open: boolean;
  title: string;
  confirmLabel: string;
  cancelLabel?: string;
  confirmColor?: 'primary' | 'error' | 'secondary';
  isLoading?: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

export function ConfirmationDialog({
  open,
  title,
  confirmLabel,
  cancelLabel = 'Cancelar',
  confirmColor = 'primary',
  isLoading = false,
  onCancel,
  onConfirm,
  children,
}: ConfirmationDialogProps) {
  return (
    <Dialog open={open} onClose={isLoading ? undefined : onCancel} fullWidth maxWidth="sm">
      <DialogTitle sx={{ textAlign: 'center', pb: 1 }}>
        <Box
          sx={{
            width: 48,
            height: 48,
            display: 'grid',
            placeItems: 'center',
            mx: 'auto',
            mb: 1.5,
            borderRadius: '50%',
            backgroundColor: 'error.light',
            color: 'error.main',
          }}
        >
          <WarningAmberOutlinedIcon />
        </Box>
        {title}
      </DialogTitle>
      <DialogContent dividers>{children}</DialogContent>
      <DialogActions>
        <Button onClick={onCancel} disabled={isLoading}>
          {cancelLabel}
        </Button>
        <Button
          variant="contained"
          color={confirmColor}
          onClick={onConfirm}
          disabled={isLoading}
        >
          {confirmLabel}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
