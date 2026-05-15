/* eslint-disable react-hooks/rules-of-hooks */
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useState } from 'react';

import type {
  BcuEncargoItemCreate,
  BcuEpiItemCreate,
  BcuEquipamentoItemCreate,
  BcuFerramentaItemCreate,
  BcuMaoObraItemCreate,
  BcuMobilizacaoItemCreate,
} from '../../shared/services/api/bcuItemApi';

export type BcuItemType = 'MO' | 'EQP' | 'ENC' | 'EPI' | 'FER' | 'MOB';

interface Props<T> {
  open: boolean;
  type: BcuItemType;
  initial?: Partial<T>;
  onClose: () => void;
  onSubmit: (data: T) => void;
}

function NumberField(props: React.ComponentProps<typeof TextField>) {
  return <TextField {...props} type="number" inputProps={{ step: 'any' }} />;
}

function BaseDialog({ open, title, onClose, onSubmit, children, disabled }: {
  open: boolean; title: string; onClose: () => void; onSubmit: () => void; children: React.ReactNode; disabled?: boolean;
}) {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 0.5 }}>
          {children}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancelar</Button>
        <Button variant="contained" onClick={onSubmit} disabled={disabled}>Salvar</Button>
      </DialogActions>
    </Dialog>
  );
}

export function BcuItemDialog(props: Props<unknown>) {
  const { open, type, initial, onClose, onSubmit } = props;

  if (type === 'MO') {
    const [form, setForm] = useState<BcuMaoObraItemCreate>({
      descricao_funcao: (initial as BcuMaoObraItemCreate)?.descricao_funcao ?? '',
      codigo_origem: (initial as BcuMaoObraItemCreate)?.codigo_origem ?? null,
      salario: (initial as BcuMaoObraItemCreate)?.salario ?? null,
      previsao_reajuste: (initial as BcuMaoObraItemCreate)?.previsao_reajuste ?? null,
      encargos_percent: (initial as BcuMaoObraItemCreate)?.encargos_percent ?? null,
      periculosidade_insalubridade: (initial as BcuMaoObraItemCreate)?.periculosidade_insalubridade ?? null,
      refeicao: (initial as BcuMaoObraItemCreate)?.refeicao ?? null,
      agua_potavel: (initial as BcuMaoObraItemCreate)?.agua_potavel ?? null,
      vale_alimentacao: (initial as BcuMaoObraItemCreate)?.vale_alimentacao ?? null,
      plano_saude: (initial as BcuMaoObraItemCreate)?.plano_saude ?? null,
      ferramentas_val: (initial as BcuMaoObraItemCreate)?.ferramentas_val ?? null,
      seguro_vida: (initial as BcuMaoObraItemCreate)?.seguro_vida ?? null,
      abono_ferias: (initial as BcuMaoObraItemCreate)?.abono_ferias ?? null,
      uniforme_val: (initial as BcuMaoObraItemCreate)?.uniforme_val ?? null,
      epi_val: (initial as BcuMaoObraItemCreate)?.epi_val ?? null,
      custo_unitario_h: (initial as BcuMaoObraItemCreate)?.custo_unitario_h ?? null,
      custo_mensal: (initial as BcuMaoObraItemCreate)?.custo_mensal ?? null,
      mobilizacao: (initial as BcuMaoObraItemCreate)?.mobilizacao ?? null,
    });
    return (
      <BaseDialog open={open} title="Mão de Obra" onClose={onClose} onSubmit={() => onSubmit(form)} disabled={!form.descricao_funcao.trim()}>
        <TextField label="Descrição da Função *" value={form.descricao_funcao} onChange={(e) => setForm((f) => ({ ...f, descricao_funcao: e.target.value }))} fullWidth />
        <Stack direction="row" spacing={2}>
          <NumberField label="Salário" value={form.salario ?? ''} onChange={(e) => setForm((f) => ({ ...f, salario: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
          <NumberField label="Reajuste" value={form.previsao_reajuste ?? ''} onChange={(e) => setForm((f) => ({ ...f, previsao_reajuste: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
        </Stack>
        <Stack direction="row" spacing={2}>
          <NumberField label="Encargos %" value={form.encargos_percent ?? ''} onChange={(e) => setForm((f) => ({ ...f, encargos_percent: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
          <NumberField label="Peric./Insal." value={form.periculosidade_insalubridade ?? ''} onChange={(e) => setForm((f) => ({ ...f, periculosidade_insalubridade: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
          <NumberField label="Refeição" value={form.refeicao ?? ''} onChange={(e) => setForm((f) => ({ ...f, refeicao: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
        </Stack>
        <Stack direction="row" spacing={2}>
          <NumberField label="Água Potável" value={form.agua_potavel ?? ''} onChange={(e) => setForm((f) => ({ ...f, agua_potavel: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
          <NumberField label="Vale Alimentação" value={form.vale_alimentacao ?? ''} onChange={(e) => setForm((f) => ({ ...f, vale_alimentacao: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
          <NumberField label="Plano Saúde" value={form.plano_saude ?? ''} onChange={(e) => setForm((f) => ({ ...f, plano_saude: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
        </Stack>
        <Stack direction="row" spacing={2}>
          <NumberField label="Ferramentas" value={form.ferramentas_val ?? ''} onChange={(e) => setForm((f) => ({ ...f, ferramentas_val: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
          <NumberField label="Seguro Vida" value={form.seguro_vida ?? ''} onChange={(e) => setForm((f) => ({ ...f, seguro_vida: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
          <NumberField label="Abono Férias" value={form.abono_ferias ?? ''} onChange={(e) => setForm((f) => ({ ...f, abono_ferias: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
        </Stack>
        <Stack direction="row" spacing={2}>
          <NumberField label="Uniforme" value={form.uniforme_val ?? ''} onChange={(e) => setForm((f) => ({ ...f, uniforme_val: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
          <NumberField label="EPI" value={form.epi_val ?? ''} onChange={(e) => setForm((f) => ({ ...f, epi_val: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
          <NumberField label="Custo/H" value={form.custo_unitario_h ?? ''} onChange={(e) => setForm((f) => ({ ...f, custo_unitario_h: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
        </Stack>
        <Stack direction="row" spacing={2}>
          <NumberField label="Custo Mensal" value={form.custo_mensal ?? ''} onChange={(e) => setForm((f) => ({ ...f, custo_mensal: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
          <NumberField label="Mobilização" value={form.mobilizacao ?? ''} onChange={(e) => setForm((f) => ({ ...f, mobilizacao: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
        </Stack>
      </BaseDialog>
    );
  }

  if (type === 'EQP') {
    const [form, setForm] = useState<BcuEquipamentoItemCreate>({
      codigo: (initial as BcuEquipamentoItemCreate)?.codigo ?? null,
      equipamento: (initial as BcuEquipamentoItemCreate)?.equipamento ?? '',
      combustivel_utilizado: (initial as BcuEquipamentoItemCreate)?.combustivel_utilizado ?? null,
      consumo_l_h: (initial as BcuEquipamentoItemCreate)?.consumo_l_h ?? null,
      aluguel_r_h: (initial as BcuEquipamentoItemCreate)?.aluguel_r_h ?? null,
      combustivel_r_h: (initial as BcuEquipamentoItemCreate)?.combustivel_r_h ?? null,
      mao_obra_r_h: (initial as BcuEquipamentoItemCreate)?.mao_obra_r_h ?? null,
      hora_produtiva: (initial as BcuEquipamentoItemCreate)?.hora_produtiva ?? null,
      hora_improdutiva: (initial as BcuEquipamentoItemCreate)?.hora_improdutiva ?? null,
      mes: (initial as BcuEquipamentoItemCreate)?.mes ?? null,
      aluguel_mensal: (initial as BcuEquipamentoItemCreate)?.aluguel_mensal ?? null,
    });
    return (
      <BaseDialog open={open} title="Equipamento" onClose={onClose} onSubmit={() => onSubmit(form)} disabled={!form.equipamento.trim()}>
        <TextField label="Código" value={form.codigo ?? ''} onChange={(e) => setForm((f) => ({ ...f, codigo: e.target.value || null }))} fullWidth />
        <TextField label="Equipamento *" value={form.equipamento} onChange={(e) => setForm((f) => ({ ...f, equipamento: e.target.value }))} fullWidth />
        <FormControl fullWidth>
          <InputLabel>Combustível</InputLabel>
          <Select value={form.combustivel_utilizado ?? ''} label="Combustível" onChange={(e) => setForm((f) => ({ ...f, combustivel_utilizado: e.target.value || null }))}>
            <MenuItem value=""><em>Nenhum</em></MenuItem>
            <MenuItem value="G">Gasolina</MenuItem>
            <MenuItem value="D">Diesel</MenuItem>
          </Select>
        </FormControl>
        <Stack direction="row" spacing={2}>
          <NumberField label="Consumo (l/h)" value={form.consumo_l_h ?? ''} onChange={(e) => setForm((f) => ({ ...f, consumo_l_h: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
          <NumberField label="Aluguel (R$/h)" value={form.aluguel_r_h ?? ''} onChange={(e) => setForm((f) => ({ ...f, aluguel_r_h: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
          <NumberField label="Combustível (R$/h)" value={form.combustivel_r_h ?? ''} onChange={(e) => setForm((f) => ({ ...f, combustivel_r_h: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
        </Stack>
        <Stack direction="row" spacing={2}>
          <NumberField label="MO (R$/h)" value={form.mao_obra_r_h ?? ''} onChange={(e) => setForm((f) => ({ ...f, mao_obra_r_h: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
          <NumberField label="Hora Produtiva" value={form.hora_produtiva ?? ''} onChange={(e) => setForm((f) => ({ ...f, hora_produtiva: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
          <NumberField label="Hora Improdutiva" value={form.hora_improdutiva ?? ''} onChange={(e) => setForm((f) => ({ ...f, hora_improdutiva: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
        </Stack>
        <Stack direction="row" spacing={2}>
          <NumberField label="Total/Mês" value={form.mes ?? ''} onChange={(e) => setForm((f) => ({ ...f, mes: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
          <NumberField label="Aluguel Mensal" value={form.aluguel_mensal ?? ''} onChange={(e) => setForm((f) => ({ ...f, aluguel_mensal: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
        </Stack>
      </BaseDialog>
    );
  }

  if (type === 'ENC') {
    const [form, setForm] = useState<BcuEncargoItemCreate>({
      tipo_encargo: (initial as BcuEncargoItemCreate)?.tipo_encargo ?? 'HORISTA',
      grupo: (initial as BcuEncargoItemCreate)?.grupo ?? null,
      codigo_grupo: (initial as BcuEncargoItemCreate)?.codigo_grupo ?? null,
      discriminacao_encargo: (initial as BcuEncargoItemCreate)?.discriminacao_encargo ?? '',
      taxa_percent: (initial as BcuEncargoItemCreate)?.taxa_percent ?? null,
    });
    return (
      <BaseDialog open={open} title="Encargo" onClose={onClose} onSubmit={() => onSubmit(form)} disabled={!form.discriminacao_encargo.trim()}>
        <FormControl fullWidth>
          <InputLabel>Tipo Encargo</InputLabel>
          <Select value={form.tipo_encargo} label="Tipo Encargo" onChange={(e) => setForm((f) => ({ ...f, tipo_encargo: e.target.value as 'HORISTA' | 'MENSALISTA' }))}>
            <MenuItem value="HORISTA">Horista</MenuItem>
            <MenuItem value="MENSALISTA">Mensalista</MenuItem>
          </Select>
        </FormControl>
        <TextField label="Grupo" value={form.grupo ?? ''} onChange={(e) => setForm((f) => ({ ...f, grupo: e.target.value || null }))} fullWidth />
        <TextField label="Código Grupo" value={form.codigo_grupo ?? ''} onChange={(e) => setForm((f) => ({ ...f, codigo_grupo: e.target.value || null }))} fullWidth />
        <TextField label="Discriminação *" value={form.discriminacao_encargo} onChange={(e) => setForm((f) => ({ ...f, discriminacao_encargo: e.target.value }))} fullWidth />
        <NumberField label="Taxa %" value={form.taxa_percent ?? ''} onChange={(e) => setForm((f) => ({ ...f, taxa_percent: e.target.value === '' ? null : Number(e.target.value) }))} fullWidth />
      </BaseDialog>
    );
  }

  if (type === 'EPI') {
    const [form, setForm] = useState<BcuEpiItemCreate>({
      epi: (initial as BcuEpiItemCreate)?.epi ?? '',
      unidade: (initial as BcuEpiItemCreate)?.unidade ?? null,
      custo_unitario: (initial as BcuEpiItemCreate)?.custo_unitario ?? null,
      vida_util_meses: (initial as BcuEpiItemCreate)?.vida_util_meses ?? null,
      custo_epi_mes: (initial as BcuEpiItemCreate)?.custo_epi_mes ?? null,
    });
    return (
      <BaseDialog open={open} title="EPI / Uniforme" onClose={onClose} onSubmit={() => onSubmit(form)} disabled={!form.epi.trim()}>
        <TextField label="EPI / Uniforme *" value={form.epi} onChange={(e) => setForm((f) => ({ ...f, epi: e.target.value }))} fullWidth />
        <TextField label="Unidade" value={form.unidade ?? ''} onChange={(e) => setForm((f) => ({ ...f, unidade: e.target.value || null }))} fullWidth />
        <Stack direction="row" spacing={2}>
          <NumberField label="Custo Unitário" value={form.custo_unitario ?? ''} onChange={(e) => setForm((f) => ({ ...f, custo_unitario: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
          <NumberField label="Vida Útil (meses)" value={form.vida_util_meses ?? ''} onChange={(e) => setForm((f) => ({ ...f, vida_util_meses: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
        </Stack>
        <NumberField label="Custo EPI/Mês" value={form.custo_epi_mes ?? ''} onChange={(e) => setForm((f) => ({ ...f, custo_epi_mes: e.target.value === '' ? null : Number(e.target.value) }))} fullWidth />
      </BaseDialog>
    );
  }

  if (type === 'FER') {
    const [form, setForm] = useState<BcuFerramentaItemCreate>({
      item: (initial as BcuFerramentaItemCreate)?.item ?? null,
      descricao: (initial as BcuFerramentaItemCreate)?.descricao ?? '',
      unidade: (initial as BcuFerramentaItemCreate)?.unidade ?? null,
      preco: (initial as BcuFerramentaItemCreate)?.preco ?? null,
      preco_total: (initial as BcuFerramentaItemCreate)?.preco_total ?? null,
    });
    return (
      <BaseDialog open={open} title="Ferramenta" onClose={onClose} onSubmit={() => onSubmit(form)} disabled={!form.descricao.trim()}>
        <TextField label="Item" value={form.item ?? ''} onChange={(e) => setForm((f) => ({ ...f, item: e.target.value || null }))} fullWidth />
        <TextField label="Descrição *" value={form.descricao} onChange={(e) => setForm((f) => ({ ...f, descricao: e.target.value }))} fullWidth />
        <TextField label="Unidade" value={form.unidade ?? ''} onChange={(e) => setForm((f) => ({ ...f, unidade: e.target.value || null }))} fullWidth />
        <Stack direction="row" spacing={2}>
          <NumberField label="Preço" value={form.preco ?? ''} onChange={(e) => setForm((f) => ({ ...f, preco: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
          <NumberField label="Preço Total" value={form.preco_total ?? ''} onChange={(e) => setForm((f) => ({ ...f, preco_total: e.target.value === '' ? null : Number(e.target.value) }))} sx={{ flex: 1 }} />
        </Stack>
      </BaseDialog>
    );
  }

  if (type === 'MOB') {
    const [form, setForm] = useState<BcuMobilizacaoItemCreate>({
      descricao: (initial as BcuMobilizacaoItemCreate)?.descricao ?? '',
      funcao: (initial as BcuMobilizacaoItemCreate)?.funcao ?? null,
      tipo_mao_obra: (initial as BcuMobilizacaoItemCreate)?.tipo_mao_obra ?? null,
      quantidades_funcao: (initial as BcuMobilizacaoItemCreate)?.quantidades_funcao ?? [],
    });
    return (
      <BaseDialog open={open} title="Mobilização" onClose={onClose} onSubmit={() => onSubmit(form)} disabled={!form.descricao.trim()}>
        <TextField label="Descrição *" value={form.descricao} onChange={(e) => setForm((f) => ({ ...f, descricao: e.target.value }))} fullWidth />
        <TextField label="Função" value={form.funcao ?? ''} onChange={(e) => setForm((f) => ({ ...f, funcao: e.target.value || null }))} fullWidth />
        <TextField label="Tipo Mão de Obra" value={form.tipo_mao_obra ?? ''} onChange={(e) => setForm((f) => ({ ...f, tipo_mao_obra: e.target.value || null }))} fullWidth />
        <Box>
          <Typography variant="subtitle2" fontWeight={600}>Quantidades por Função</Typography>
          {form.quantidades_funcao.map((qf, idx) => (
            <Stack key={idx} direction="row" spacing={1} alignItems="center" sx={{ mt: 1 }}>
              <TextField size="small" label="Função" value={qf.coluna_funcao} onChange={(e) => {
                const arr = [...form.quantidades_funcao];
                arr[idx] = { ...qf, coluna_funcao: e.target.value };
                setForm((f) => ({ ...f, quantidades_funcao: arr }));
              }} sx={{ flex: 1 }} />
              <NumberField size="small" label="Qtd" value={qf.quantidade ?? ''} onChange={(e) => {
                const arr = [...form.quantidades_funcao];
                arr[idx] = { ...qf, quantidade: e.target.value === '' ? null : Number(e.target.value) };
                setForm((f) => ({ ...f, quantidades_funcao: arr }));
              }} sx={{ width: 120 }} />
              <Button size="small" color="error" onClick={() => {
                const arr = form.quantidades_funcao.filter((_, i) => i !== idx);
                setForm((f) => ({ ...f, quantidades_funcao: arr }));
              }}>Remover</Button>
            </Stack>
          ))}
          <Button size="small" sx={{ mt: 1 }} onClick={() => setForm((f) => ({ ...f, quantidades_funcao: [...f.quantidades_funcao, { coluna_funcao: '', quantidade: null }] }))}>
            + Adicionar função
          </Button>
        </Box>
      </BaseDialog>
    );
  }

  return null;
}
