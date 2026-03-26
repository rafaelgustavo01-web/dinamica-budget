import {
  LinearProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  Typography,
} from '@mui/material';
import type { ReactNode } from 'react';

interface DataColumn<T> {
  key: string;
  header: string;
  align?: 'left' | 'right' | 'center';
  width?: number | string;
  render: (row: T) => ReactNode;
}

interface DataTableProps<T> {
  columns: DataColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  loading?: boolean;
  page: number;
  pageSize: number;
  total: number;
  emptyTitle: string;
  emptyDescription: string;
  onPageChange?: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  onRowClick?: (row: T) => void;
}

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  loading = false,
  page,
  pageSize,
  total,
  emptyTitle,
  emptyDescription,
  onPageChange,
  onPageSizeChange,
  onRowClick,
}: DataTableProps<T>) {
  const hasRows = rows.length > 0;

  return (
    <Paper sx={{ overflow: 'hidden' }}>
      {loading ? <LinearProgress /> : null}

      <TableContainer>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              {columns.map((column) => (
                <TableCell
                  key={column.key}
                  align={column.align}
                  sx={{ width: column.width, fontWeight: 700 }}
                >
                  {column.header}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>

          <TableBody>
            {hasRows ? (
              rows.map((row) => (
                <TableRow
                  key={rowKey(row)}
                  hover
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  sx={{
                    cursor: onRowClick ? 'pointer' : 'default',
                    '&:last-child td': { borderBottom: 0 },
                  }}
                >
                  {columns.map((column) => (
                    <TableCell key={column.key} align={column.align}>
                      {column.render(row)}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length}>
                  <Typography variant="subtitle1" sx={{ mb: 0.5 }}>
                    {emptyTitle}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {emptyDescription}
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        component="div"
        count={total}
        page={Math.max(page - 1, 0)}
        onPageChange={(_, nextPage) => onPageChange?.(nextPage + 1)}
        rowsPerPage={pageSize}
        onRowsPerPageChange={(event) =>
          onPageSizeChange?.(Number(event.target.value))
        }
        rowsPerPageOptions={[10, 20, 50, 100]}
        labelRowsPerPage="Itens por página"
      />
    </Paper>
  );
}
