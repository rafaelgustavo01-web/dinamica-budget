import { useNavigate } from 'react-router-dom';
import { StatusBadge } from '../../../shared/components/StatusBadge';
import { formatCurrency, formatDateTime } from '../../../shared/utils/format';
import type { Proposta } from '../types';
import { DataTable } from '../../../shared/components/DataTable';

interface ProposalsTableProps {
  propostas: Proposta[];
  isLoading: boolean;
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
}

export function ProposalsTable({
  propostas,
  isLoading,
  page,
  pageSize,
  total,
  onPageChange,
  onPageSizeChange,
}: ProposalsTableProps) {
  const navigate = useNavigate();

  return (
    <DataTable
      columns={[
        {
          key: 'codigo',
          header: 'Código',
          render: (row) => row.codigo,
        },
        {
          key: 'titulo',
          header: 'Título',
          render: (row) => row.titulo || '—',
        },
        {
          key: 'status',
          header: 'Status',
          render: (row) => <StatusBadge value={row.status} kind="proposta" />,
        },
        {
          key: 'total',
          header: 'Total',
          align: 'right',
          render: (row) => (row.total_geral ? formatCurrency(row.total_geral) : '—'),
        },
        {
          key: 'data',
          header: 'Criada em',
          render: (row) => formatDateTime(row.created_at),
        },
      ]}
      rows={propostas}
      rowKey={(row) => row.id}
      loading={isLoading}
      page={page}
      pageSize={pageSize}
      total={total}
      onPageChange={onPageChange}
      onPageSizeChange={onPageSizeChange}
      onRowClick={(row) => navigate(`/propostas/${row.id}`)}
      emptyTitle="Nenhuma proposta encontrada"
      emptyDescription="Crie uma nova proposta para começar a orçamentar."
    />
  );
}
