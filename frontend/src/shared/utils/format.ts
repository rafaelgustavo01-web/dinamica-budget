import type { PerfilUsuario } from '../types/contracts/auth';
import type { OrigemMatch } from '../types/contracts/busca';
import type { DecimalValue } from '../types/contracts/common';

const currencyFormatter = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
});

const numberFormatter = new Intl.NumberFormat('pt-BR', {
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

export function getPropostaStatusLabel(status: string) {
  const labels: Record<string, string> = {
    RASCUNHO: 'Rascunho',
    EM_ANALISE: 'Em análise',
    CPU_GERADA: 'CPU gerada',
    APROVADA: 'Aprovada',
    REPROVADA: 'Reprovada',
    ARQUIVADA: 'Arquivada',
  };

  return labels[status] ?? status;
}

