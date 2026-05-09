import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import { Tooltip } from '@mui/material';

interface HelpTooltipProps {
  title: string;
}

/**
 * Inline help icon with tooltip. Place next to labels, headings, or tab titles
 * to give contextual guidance without cluttering the UI.
 */
export function HelpTooltip({ title }: HelpTooltipProps) {
  return (
    <Tooltip title={title} arrow placement="top">
      <HelpOutlineIcon
        fontSize="small"
        sx={{
          ml: 0.5,
          mb: '-2px',
          color: 'text.disabled',
          fontSize: '0.95rem',
          cursor: 'help',
          verticalAlign: 'middle',
          '&:hover': { color: 'primary.main' },
        }}
      />
    </Tooltip>
  );
}
