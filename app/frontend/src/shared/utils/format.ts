import type { PerfilUsuario } from '../types/contracts/auth';
import type { OrigemMatch } from '../types/contracts/busca';
import type { DecimalValue } from '../types/contracts/common';

const currencyFormatter = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
});

const numberFormatter = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const quantityFormatter = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const dateTimeFormatter = new Intl.DateTimeFormat('pt-BR', {
  dateStyle: 'short',
  timeStyle: 'short',
});

export function toNumber(value: DecimalValue | null | undefined) {
  if (typeof value === 'number') {
    return value;
  }
  if (typeof value === 'string') {
    const normalized = value.replace(',', '.');
    return Number(normalized);
  }
  return 0;
}

export function formatCurrency(value: DecimalValue | null | undefined) {
  return currencyFormatter.format(toNumber(value));
}

export function formatNumber(value: DecimalValue | null | undefined) {
  return numberFormatter.format(toNumber(value));
}

export function formatQuantity(value: DecimalValue | string | null | undefined): string {
  if (value === null || value === undefined || value === '') return '—';
  return quantityFormatter.format(toNumber(value as DecimalValue));
}

export function formatUnit(value: string | null | undefined): string {
  if (!value) return '—';
  return String(value).trim().toUpperCase();
}

export function formatPercent(value: DecimalValue | string | null | undefined, digits = 0): string {
  if (value === null || value === undefined || value === '') return '—';
  const n = toNumber(value as DecimalValue);
  return (n * 100).toLocaleString('pt-BR', { minimumFractionDigits: digits, maximumFractionDigits: digits }) + '%';
}

export function formatDateTime(value: string | Date | null | undefined) {
  if (!value) {
    return '-';
  }

  const date = value instanceof Date ? value : new Date(value);
  return dateTimeFormatter.format(date);
}

export function shortenUuid(value: string) {
  if (value.length < 12) {
    return value;
  }
  return `${value.slice(0, 8)}...${value.slice(-4)}`;
}

export function getOrigemMatchLabel(origem: OrigemMatch) {
  const labels: Record<OrigemMatch, string> = {
    ASSOCIACAO_DIRETA: 'Associação direta',
    FUZZY: 'Busca fuzzy',
    IA_SEMANTICA: 'IA semântica',
    PROPRIA_CLIENTE: 'Item próprio',
  };

  return labels[origem];
}

export function getPerfilLabel(perfil: PerfilUsuario) {
  const labels: Record<string, string> = {
    USUARIO: 'Usuário',
    APROVADOR: 'Aprovador',
    ADMIN: 'Administrador',
  };

  return labels[perfil] ?? perfil;
}

export function getHomologacaoLabel(status: string) {
  const labels: Record<string, string> = {
    APROVADO: 'Aprovado',
    PENDENTE: 'Pendente',
    REPROVADO: 'Reprovado',
    VALIDADA: 'Validada',
    CONSOLIDADA: 'Consolidada',
    SUGERIDA: 'Sugerida',
  };

  return labels[status] ?? status;
}

export function formatCnpj(value: string | null | undefined) {
  if (!value) return '—';
  const d = value.replace(/\D/g, '');
  if (d.length !== 14) return value;
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`;
}

export function formatCep(value: string | null | undefined) {
  if (!value) return '—';
  const d = value.replace(/\D/g, '');
  if (d.length !== 8) return value;
  return `${d.slice(0, 5)}-${d.slice(5)}`;
}

export function getPropostaStatusLabel(status: string) {
  const labels: Record<string, string> = {
    RASCUNHO: 'Rascunho',
    EM_ANALISE: 'Em análise',
    CPU_GERADA: 'CPU gerada',
    AGUARDANDO_APROVACAO: 'Aguardando aprovação',
    APROVADA: 'Aprovada',
    REPROVADA: 'Reprovada',
    ARQUIVADA: 'Arquivada',
  };

  return labels[status] ?? status;
}

