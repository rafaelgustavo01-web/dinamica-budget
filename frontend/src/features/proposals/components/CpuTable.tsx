import { Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material';
import { formatCurrency } from '../../../shared/utils/format';
import type { CpuItem } from '../types';

interface CpuTableProps {
  itens: CpuItem[];
}

export function CpuTable({ itens }: CpuTableProps) {
  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHead>Código</TableHead>
          <TableHead>Descrição</TableHead>
          <TableHead>Unidade</TableHead>
          <TableHead>Qtd</TableHead>
          <TableHead>Preço Unit.</TableHead>
          <TableHead>Preço Total</TableHead>
        </TableRow>
      </TableHead>
      <TableBody>
        {itens.map((i) => (
          <TableRow key={i.id}>
            <TableCell>{i.codigo}</TableCell>
            <TableCell>{i.descricao}</TableCell>
            <TableCell>{i.unidade}</TableCell>
            <TableCell>{i.quantidade}</TableCell>
            <TableCell>{formatCurrency(i.preco_unitario)}</TableCell>
            <TableCell>{formatCurrency(i.preco_total)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
