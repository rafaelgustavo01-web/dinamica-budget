import { useState } from 'react';
import {
  Alert,
  Button,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  CircularProgress,
  Snackbar,
} from '@mui/material';
import DownloadOutlinedIcon from '@mui/icons-material/DownloadOutlined';
import GridOnOutlinedIcon from '@mui/icons-material/GridOnOutlined';
import PictureAsPdfOutlinedIcon from '@mui/icons-material/PictureAsPdfOutlined';
import { proposalsApi } from '../../../shared/services/api/proposalsApi';

interface ExportMenuProps {
  propostaId: string;
  propostaCodigo: string;
  disabled?: boolean;
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function ExportMenu({ propostaId, propostaCodigo, disabled }: ExportMenuProps) {
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleExcel() {
    setAnchor(null);
    setBusy(true);
    setError(null);
    try {
      const blob = await proposalsApi.exportExcel(propostaId);
      triggerDownload(blob, `proposta-${propostaCodigo}.xlsx`);
    } catch {
      setError('Falha ao exportar Excel. Tente novamente.');
    } finally {
      setBusy(false);
    }
  }

  async function handlePdf() {
    setAnchor(null);
    setBusy(true);
    setError(null);
    try {
      const blob = await proposalsApi.exportPdf(propostaId);
      triggerDownload(blob, `proposta-${propostaCodigo}.pdf`);
    } catch {
      setError('Falha ao exportar PDF. Tente novamente.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Button
        variant="outlined"
        startIcon={busy ? <CircularProgress size={16} /> : <DownloadOutlinedIcon />}
        disabled={disabled || busy}
        onClick={(e) => setAnchor(e.currentTarget)}
      >
        Exportar
      </Button>
      <Menu anchorEl={anchor} open={Boolean(anchor)} onClose={() => setAnchor(null)}>
        <MenuItem onClick={handleExcel}>
          <ListItemIcon><GridOnOutlinedIcon fontSize="small" /></ListItemIcon>
          <ListItemText>Excel (xlsx)</ListItemText>
        </MenuItem>
        <MenuItem onClick={handlePdf}>
          <ListItemIcon><PictureAsPdfOutlinedIcon fontSize="small" /></ListItemIcon>
          <ListItemText>PDF (folha de rosto)</ListItemText>
        </MenuItem>
      </Menu>
      <Snackbar
        open={Boolean(error)}
        autoHideDuration={6000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>
    </>
  );
}
