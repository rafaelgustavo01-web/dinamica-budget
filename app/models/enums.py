"""
Central enum definitions for Dinamica Budget V2.
All enums used across models are defined here to avoid circular imports.
"""

import enum


class TipoCusto(str, enum.Enum):
    HORISTA = "HORISTA"
    MENSALISTA = "MENSALISTA"
    GLOBAL = "GLOBAL"


class OrigemItem(str, enum.Enum):
    TCPO = "TCPO"           # Item do catálogo oficial TCPO
    PROPRIA = "PROPRIA"     # Item próprio do cliente


class StatusHomologacao(str, enum.Enum):
    PENDENTE = "PENDENTE"
    APROVADO = "APROVADO"
    REPROVADO = "REPROVADO"


class OrigemAssociacao(str, enum.Enum):
    MANUAL_USUARIO = "MANUAL_USUARIO"
    IA_CONSOLIDADA = "IA_CONSOLIDADA"


class StatusValidacaoAssociacao(str, enum.Enum):
    SUGERIDA = "SUGERIDA"       # Criada automaticamente, baixa confiança
    VALIDADA = "VALIDADA"       # Confirmada pelo usuário ao menos 1x
    CONSOLIDADA = "CONSOLIDADA" # Confirmada N vezes — auto-return no motor


class PerfilUsuario(str, enum.Enum):
    USUARIO = "USUARIO"         # Buscar, criar item próprio, confirmar associação
    APROVADOR = "APROVADOR"     # Tudo do USUARIO + homologar itens do cliente
    ADMIN = "ADMIN"             # Acesso global, múltiplos clientes


class TipoOperacaoAuditoria(str, enum.Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    APROVAR = "APROVAR"
    REPROVAR = "REPROVAR"


class TipoRecurso(str, enum.Enum):
    MO = "MO"                   # Mão de obra
    INSUMO = "INSUMO"           # Material/insumo
    FERRAMENTA = "FERRAMENTA"   # Ferramenta
    EQUIPAMENTO = "EQUIPAMENTO" # Equipamento
    SERVICO = "SERVICO"         # Composição de serviços (permite explosão recursiva)
