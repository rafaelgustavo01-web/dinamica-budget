import {
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
      <DialogTitle>{title}</DialogTitle>
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
