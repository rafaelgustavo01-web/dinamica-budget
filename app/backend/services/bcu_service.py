"""ETL service: parses BCU XLSX and persists all sheets to the bcu schema + syncs base_tcpo."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from io import BytesIO
from typing import Any

import openpyxl
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.logging import get_logger
from backend.models.base_tcpo import BaseTcpo
from backend.models.bcu import (
    BcuCabecalho,
    BcuEncargoItem,
    BcuEquipamentoItem,
    BcuEquipamentoPremissa,
    BcuEpiDistribuicaoFuncao,
    BcuEpiItem,
    BcuFerramentaItem,
    BcuMaoObraItem,
    BcuMobilizacaoItem,
    BcuMobilizacaoQuantidadeFuncao,
)

logger = get_logger(__name__)
_BATCH_SIZE = 500


def _to_decimal(value: Any):
    """Safe cast to float-compatible Decimal; returns None on blank/error."""
    if value is None:
        return None
    try:
        return float(str(value).replace(",", ".").strip())
    except (ValueError, TypeError):
        return None


def _find_col(col_map: dict[str, int], *keywords: str) -> int | None:
    """Finds first column index matching any of the keywords (case-insensitive)."""
    for kw in keywords:
        kw_up = kw.upper()
        for hk, idx in col_map.items():
            if kw_up in hk:
                return idx
    return None


def _parse_mao_obra(ws, cabecalho_id: uuid.UUID, seq_counter: dict[str, int]) -> tuple[list[BcuMaoObraItem], list[BaseTcpo]]:
    header_row_idx = 3
    for row_num, row in enumerate(ws.iter_rows(min_row=1, max_row=10, values_only=True), start=1):
        if any(cell and "DESCRI" in str(cell).upper() for cell in row):
            header_row_idx = row_num
            break

    header_vals = next(ws.iter_rows(min_row=header_row_idx, max_row=header_row_idx, values_only=True))
    col_map = {str(c).strip().upper(): i for i, c in enumerate(header_vals) if c}

    c_desc = _find_col(col_map, "DESCRI") if col_map else None
    if c_desc is None:
        c_desc = 0
    c_qtd = _find_col(col_map, "QUANT") or 1
    c_sal = _find_col(col_map, "SALARIO", "SALÁRIO") or 2
    c_reaj = _find_col(col_map, "REAJUSTE") or 3
    c_enc = _find_col(col_map, "ENCARGO") or 4
    c_peric = _find_col(col_map, "PERICULOSIDADE", "INSALUBRIDADE") or 5
    c_refei = _find_col(col_map, "REFEIÇÃO", "REFEICAO") or 6
    c_agua = _find_col(col_map, "ÁGUA", "AGUA") or 7
    c_vale = _find_col(col_map, "VALE ALIMENTAÇÃO", "VALE ALIMENTACAO") or 8
    c_saude = _find_col(col_map, "SAÚDE", "SAUDE") or 9
    c_ferr = _find_col(col_map, "FERRAMENTA") or 10
    c_seg = _find_col(col_map, "SEGURO") or 11
    c_ferias = _find_col(col_map, "FÉRIAS", "FERIAS") or 12
    c_unif = _find_col(col_map, "UNIFORME") or 13
    c_epi = _find_col(col_map, "EPI") or 14
    c_cunit = _find_col(col_map, "CUSTO UNITARIO", "UNITÁRIO") or 15
    c_cmensal = _find_col(col_map, "CUSTO MENSAL") or 16
    c_mob = _find_col(col_map, "MOBILIZAÇÃO", "MOBILIZACAO") or 18

    def _v(row: tuple, c: int | None) -> float | None:
        return _to_decimal(row[c]) if c is not None and c < len(row) else None

    items: list[BcuMaoObraItem] = []
    base_tcpo_items: list[BaseTcpo] = []
    for row in ws.iter_rows(min_row=header_row_idx + 1, values_only=True):
        desc = row[c_desc] if c_desc < len(row) else None
        if not desc:
            continue
        seq_counter["MO"] = seq_counter.get("MO", 0) + 1
        codigo_origem = f"BCU-MO-{seq_counter['MO']:03d}"
        items.append(
            BcuMaoObraItem(
                id=uuid.uuid4(),
                cabecalho_id=cabecalho_id,
                descricao_funcao=str(desc).strip(),
                codigo_origem=codigo_origem,
                quantidade=_v(row, c_qtd),
                salario=_v(row, c_sal),
                previsao_reajuste=_v(row, c_reaj),
                encargos_percent=_v(row, c_enc),
                periculosidade_insalubridade=_v(row, c_peric),
                refeicao=_v(row, c_refei),
                agua_potavel=_v(row, c_agua),
                vale_alimentacao=_v(row, c_vale),
                plano_saude=_v(row, c_saude),
                ferramentas_val=_v(row, c_ferr),
                seguro_vida=_v(row, c_seg),
                abono_ferias=_v(row, c_ferias),
                uniforme_val=_v(row, c_unif),
                epi_val=_v(row, c_epi),
                custo_unitario_h=_v(row, c_cunit),
                custo_mensal=_v(row, c_cmensal),
                mobilizacao=_v(row, c_mob),
            )
        )
        base_tcpo_items.append(
            BaseTcpo(
                id=uuid.uuid4(),
                codigo_origem=codigo_origem,
                descricao=str(desc).strip(),
                unidade_medida="H",
                custo_base=_v(row, c_cunit) or 0.0,
                tipo_recurso="MO",
            )
        )
    return items, base_tcpo_items


def _parse_equipamentos(ws, cabecalho_id: uuid.UUID, seq_counter: dict[str, int]):
    premissa = None
    items: list[BcuEquipamentoItem] = []
    base_tcpo_items: list[BaseTcpo] = []

    all_rows = list(ws.iter_rows(values_only=True))

    horas_mes = None
    gasolina = None
    diesel = None
    for r in all_rows[:5]:
        if r and len(r) > 9:
            label = str(r[8]).lower() if r[8] else ""
            if "hora" in label:
                horas_mes = _to_decimal(r[9])
            if "gasolina" in label:
                gasolina = _to_decimal(r[9])
            if "diesel" in label:
                diesel = _to_decimal(r[9])

    premissa = BcuEquipamentoPremissa(
        id=uuid.uuid4(),
        cabecalho_id=cabecalho_id,
        horas_mes=horas_mes,
        preco_gasolina_l=gasolina,
        preco_diesel_l=diesel,
    )

    for row in ws.iter_rows(min_row=7, values_only=True):
        equip = row[1] if len(row) > 1 else None
        if not equip:
            continue
        seq_counter["EQP"] = seq_counter.get("EQP", 0) + 1
        codigo_origem = f"BCU-EQP-{seq_counter['EQP']:03d}"
        items.append(
            BcuEquipamentoItem(
                id=uuid.uuid4(),
                cabecalho_id=cabecalho_id,
                codigo=str(row[0]).strip() if row[0] else None,
                codigo_origem=codigo_origem,
                equipamento=str(equip).strip(),
                combustivel_utilizado=str(row[2]).strip() if row[2] else None,
                consumo_l_h=_to_decimal(row[3]),
                aluguel_r_h=_to_decimal(row[4]),
                combustivel_r_h=_to_decimal(row[5]),
                mao_obra_r_h=_to_decimal(row[6]),
                hora_produtiva=_to_decimal(row[7]),
                hora_improdutiva=_to_decimal(row[8]),
                mes=_to_decimal(row[9]) if len(row) > 9 else None,
                aluguel_mensal=_to_decimal(row[11]) if len(row) > 11 else None,
            )
        )
        base_tcpo_items.append(
            BaseTcpo(
                id=uuid.uuid4(),
                codigo_origem=codigo_origem,
                descricao=str(equip).strip(),
                unidade_medida="H",
                custo_base=_to_decimal(row[4]) or 0.0,
                tipo_recurso="EQUIPAMENTO",
            )
        )
    return premissa, items, base_tcpo_items


def _parse_encargos(ws, cabecalho_id: uuid.UUID, tipo: str) -> list[BcuEncargoItem]:
    items: list[BcuEncargoItem] = []
    current_grupo = None

    for row in ws.iter_rows(min_row=4, values_only=True):
        if row[0] and str(row[0]).strip().upper() not in ("GRUPOS",):
            val0 = str(row[0]).strip()
            if len(val0) <= 3 and val0.isalpha():
                current_grupo = val0

        if tipo == "HORISTA":
            cod = str(row[1]).strip() if row[1] else None
            disc = str(row[2]).strip() if row[2] else None
            taxa = _to_decimal(row[5]) if len(row) > 5 else None
        else:
            cod = str(row[1]).strip() if row[1] else None
            disc = str(row[2]).strip() if row[2] else None
            taxa = _to_decimal(row[3]) if len(row) > 3 else None

        if not disc or disc.lower() in ("discriminação do encargo", "grupos"):
            continue
        if disc.lower().startswith("total do grupo"):
            continue

        items.append(
            BcuEncargoItem(
                id=uuid.uuid4(),
                cabecalho_id=cabecalho_id,
                tipo_encargo=tipo,
                grupo=current_grupo,
                codigo_grupo=cod,
                discriminacao_encargo=disc,
                taxa_percent=taxa,
            )
        )
    return items


_EPI_FUNCOES = [
    "OFICIAL", "AJUDANTE", "ELETRICISTA", "OPERADOR",
    "MÃO DE OBRA INDIRETA", "ALPINISTA", "MONTADOR ANDAIME",
]


def _parse_epi(ws, cabecalho_id: uuid.UUID, seq_counter: dict[str, int]):
    epi_items: list[BcuEpiItem] = []
    dist_items: list[BcuEpiDistribuicaoFuncao] = []
    base_tcpo_items: list[BaseTcpo] = []

    header_row = list(ws.iter_rows(min_row=2, max_row=2, values_only=True))[0]
    funcao_cols: list[tuple[int, str]] = []
    for idx, cell in enumerate(header_row):
        if cell and idx >= 8:
            funcao_cols.append((idx, str(cell).strip()))

    for row in ws.iter_rows(min_row=3, values_only=True):
        epi_name = row[1] if len(row) > 1 else None
        if not epi_name:
            continue

        seq_counter["EPI"] = seq_counter.get("EPI", 0) + 1
        codigo_origem = f"BCU-EPI-{seq_counter['EPI']:03d}"
        epi_id = uuid.uuid4()
        epi_items.append(
            BcuEpiItem(
                id=epi_id,
                cabecalho_id=cabecalho_id,
                codigo_origem=codigo_origem,
                epi=str(epi_name).strip(),
                unidade=str(row[2]).strip() if row[2] else None,
                custo_unitario=_to_decimal(row[3]),
                quantidade=_to_decimal(row[4]),
                vida_util_meses=_to_decimal(row[5]),
                custo_epi_mes=_to_decimal(row[6]),
            )
        )
        base_tcpo_items.append(
            BaseTcpo(
                id=uuid.uuid4(),
                codigo_origem=codigo_origem,
                descricao=str(epi_name).strip(),
                unidade_medida=str(row[2]).strip() if row[2] else "UN",
                custo_base=_to_decimal(row[3]) or 0.0,
                tipo_recurso="INSUMO",
            )
        )

        for col_idx, funcao in funcao_cols:
            val = row[col_idx] if len(row) > col_idx else None
            if val is not None:
                dist_items.append(
                    BcuEpiDistribuicaoFuncao(
                        id=uuid.uuid4(),
                        epi_item_id=epi_id,
                        funcao=funcao,
                        aplica_flag=str(val).strip(),
                    )
                )

    return epi_items, dist_items, base_tcpo_items


def _parse_ferramentas(ws, cabecalho_id: uuid.UUID, seq_counter: dict[str, int]) -> tuple[list[BcuFerramentaItem], list[BaseTcpo]]:
    items: list[BcuFerramentaItem] = []
    base_tcpo_items: list[BaseTcpo] = []
    for row in ws.iter_rows(min_row=4, values_only=True):
        desc = row[2] if len(row) > 2 else None
        if not desc:
            continue
        seq_counter["FER"] = seq_counter.get("FER", 0) + 1
        codigo_origem = f"BCU-FER-{seq_counter['FER']:03d}"
        items.append(
            BcuFerramentaItem(
                id=uuid.uuid4(),
                cabecalho_id=cabecalho_id,
                codigo_origem=codigo_origem,
                item=str(row[1]).strip() if row[1] else None,
                descricao=str(desc).strip(),
                unidade=str(row[3]).strip() if len(row) > 3 and row[3] else None,
                quantidade=_to_decimal(row[4]) if len(row) > 4 else None,
                preco=_to_decimal(row[5]) if len(row) > 5 else None,
                preco_total=_to_decimal(row[6]) if len(row) > 6 else None,
            )
        )
        base_tcpo_items.append(
            BaseTcpo(
                id=uuid.uuid4(),
                codigo_origem=codigo_origem,
                descricao=str(desc).strip(),
                unidade_medida=str(row[3]).strip() if len(row) > 3 and row[3] else "UN",
                custo_base=_to_decimal(row[5]) or 0.0,
                tipo_recurso="FERRAMENTA",
            )
        )
    return items, base_tcpo_items


def _parse_mobilizacao(ws, cabecalho_id: uuid.UUID):
    mob_items: list[BcuMobilizacaoItem] = []
    quant_items: list[BcuMobilizacaoQuantidadeFuncao] = []

    all_rows = list(ws.iter_rows(min_row=1, values_only=True))

    header_row_idx = 1
    for i, row in enumerate(all_rows[:6]):
        if row and len(row) > 2 and any(cell for cell in row[2:] if cell):
            header_row_idx = i
            break

    header_row2 = all_rows[header_row_idx] if len(all_rows) > header_row_idx else []
    funcao_cols: list[tuple[int, str]] = []
    for idx, cell in enumerate(header_row2):
        if cell and idx >= 2:
            funcao_cols.append((idx, str(cell).strip()))

    data_start_idx = None
    for i in range(header_row_idx + 1, len(all_rows)):
        row = all_rows[i]
        if row and row[0]:
            data_start_idx = i
            break

    if data_start_idx is None:
        data_start_idx = len(all_rows)

    for row in all_rows[data_start_idx:]:
        desc = row[0]
        if not desc:
            continue
        item_id = uuid.uuid4()
        valor_unitario = row[1] if len(row) > 1 else None
        mob_items.append(
            BcuMobilizacaoItem(
                id=item_id,
                cabecalho_id=cabecalho_id,
                descricao=str(desc).strip(),
                funcao=str(valor_unitario).strip() if valor_unitario else None,
                tipo_mao_obra=None,
            )
        )
        for col_idx, funcao in funcao_cols:
            val = row[col_idx] if len(row) > col_idx else None
            quant_items.append(
                BcuMobilizacaoQuantidadeFuncao(
                    id=uuid.uuid4(),
                    mobilizacao_item_id=item_id,
                    coluna_funcao=funcao,
                    quantidade=_to_decimal(val),
                )
            )

    return mob_items, quant_items


async def _sync_base_tcpo_batch(db: AsyncSession, items: list[BaseTcpo]) -> None:
    for chunk_start in range(0, len(items), _BATCH_SIZE):
        chunk = items[chunk_start : chunk_start + _BATCH_SIZE]
        rows = [
            {
                "id": bt.id,
                "codigo_origem": bt.codigo_origem,
                "descricao": bt.descricao,
                "unidade_medida": bt.unidade_medida,
                "custo_base": bt.custo_base,
                "tipo_recurso": bt.tipo_recurso,
            }
            for bt in chunk
        ]
        stmt = pg_insert(BaseTcpo).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["codigo_origem"],
            set_={
                "descricao": stmt.excluded.descricao,
                "unidade_medida": stmt.excluded.unidade_medida,
                "custo_base": stmt.excluded.custo_base,
                "tipo_recurso": stmt.excluded.tipo_recurso,
            },
        )
        await db.execute(stmt)


class BcuService:
    """
    Importa o arquivo BCU.xlsx (planilha mestra de custos) com 7 abas.
    Ao importar:
      1. Cria bcu.cabecalho (is_ativo=False inicialmente)
      2. Popula 9 tabelas filhas
      3. Sincroniza referencia.base_tcpo:
         - Para cada item de MO/EQP/EPI/FER, cria/atualiza BaseTcpo
         - codigo_origem = BCU-{tipo}-{N}
      4. Encargos e Mobilizacao NAO sao sincronizados
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def importar_bcu(
        self,
        file_bytes: bytes,
        nome_arquivo: str,
        criador_id: uuid.UUID,
    ) -> BcuCabecalho:
        cab = BcuCabecalho(
            id=uuid.uuid4(),
            nome_arquivo=nome_arquivo,
            versao_layout="v1",
            is_ativo=False,
            criado_por_id=criador_id,
        )
        try:
            wb = openpyxl.load_workbook(BytesIO(file_bytes), data_only=True)

            seq_counter: dict[str, int] = {}
            all_base_tcpo: list[BaseTcpo] = []
            db_items: list[Any] = []
            total_rows = 0

            for sheet_name in wb.sheetnames:
                if "MÃO DE OBRA" in sheet_name.upper() and "INDIRETA" not in sheet_name.upper():
                    items, bt_items = _parse_mao_obra(wb[sheet_name], cab.id, seq_counter)
                    db_items.extend(items)
                    total_rows += len(items)
                    all_base_tcpo.extend(bt_items)
                    break

            for sheet_name in wb.sheetnames:
                if "EQUIPAMENTO" in sheet_name.upper():
                    premissa, eq_items, bt_items = _parse_equipamentos(wb[sheet_name], cab.id, seq_counter)
                    db_items.append(premissa)
                    db_items.extend(eq_items)
                    total_rows += len(eq_items)
                    all_base_tcpo.extend(bt_items)
                    break

            horista_done = False
            for sheet_name in wb.sheetnames:
                if "HORISTA" in sheet_name.upper():
                    items = _parse_encargos(wb[sheet_name], cab.id, "HORISTA")
                    db_items.extend(items)
                    total_rows += len(items)
                    horista_done = True
                    break

            mensalista_done = False
            for sheet_name in wb.sheetnames:
                if "MENSALISTA" in sheet_name.upper():
                    items = _parse_encargos(wb[sheet_name], cab.id, "MENSALISTA")
                    db_items.extend(items)
                    total_rows += len(items)
                    mensalista_done = True
                    break

            if not horista_done and not mensalista_done:
                for sheet_name in wb.sheetnames:
                    if "ENCARGO" in sheet_name.upper():
                        items = _parse_encargos(wb[sheet_name], cab.id, "HORISTA")
                        db_items.extend(items)
                        total_rows += len(items)
                        break

            for sheet_name in wb.sheetnames:
                if "EPI" in sheet_name.upper():
                    epi_items, dist_items, bt_items = _parse_epi(wb[sheet_name], cab.id, seq_counter)
                    db_items.extend(epi_items)
                    db_items.extend(dist_items)
                    total_rows += len(epi_items)
                    all_base_tcpo.extend(bt_items)
                    break

            for sheet_name in wb.sheetnames:
                if "FERRAMENTA" in sheet_name.upper():
                    items, bt_items = _parse_ferramentas(wb[sheet_name], cab.id, seq_counter)
                    db_items.extend(items)
                    total_rows += len(items)
                    all_base_tcpo.extend(bt_items)
                    break

            for sheet_name in wb.sheetnames:
                if "MOBILIZA" in sheet_name.upper():
                    mob_items, quant_items = _parse_mobilizacao(wb[sheet_name], cab.id)
                    db_items.extend(mob_items)
                    db_items.extend(quant_items)
                    total_rows += len(mob_items)
                    break

            result = await self.db.execute(select(BcuCabecalho).where(BcuCabecalho.nome_arquivo == nome_arquivo))
            for existing in result.scalars().all():
                await self.db.delete(existing)
            await self.db.flush()

            self.db.add(cab)
            self.db.add_all(db_items)
            await _sync_base_tcpo_batch(self.db, all_base_tcpo)

            logger.info(
                "bcu.import_complete",
                arquivo=nome_arquivo,
                cabecalho_id=str(cab.id),
                rows=total_rows,
                base_tcpo_synced=len(all_base_tcpo),
            )
            await self.db.commit()
            await self.db.refresh(cab)
            return cab
        except Exception:
            await self.db.rollback()
            raise

    async def importar_converter(
        self,
        file_bytes: bytes,
        nome_arquivo: str,
        criador_id: uuid.UUID,
    ) -> BcuCabecalho:
        """
        Importa 'Converter em Data Center.xlsx' (6 abas: ENCARGOS, EPI-UNIFORME,
        EQUIPAMENTOS, EXAMES, FERRAMENTAS, MAO DE OBRA) e popula bcu.*.

        Diferenças vs. importar_bcu (BCU.xlsx legado):
        - Estrutura de colunas mais simples (sem premissas de equipamento, sem horista/mensalista
          duplicados, sem mobilizacao);
        - Aba EXAMES não tem tabela alvo no schema BCU atual — registrada como aviso no cabecalho.observacao;
        - sync de referencia.base_tcpo cobre MO/EQP/EPI/FER (codigo_origem = BCU-{tipo}-{N}).
        """
        cab = BcuCabecalho(
            id=uuid.uuid4(),
            nome_arquivo=nome_arquivo,
            versao_layout="converter-v1",
            is_ativo=False,
            criado_por_id=criador_id,
        )
        try:
            wb = openpyxl.load_workbook(BytesIO(file_bytes), data_only=True)

            seq: dict[str, int] = {}
            all_base_tcpo: list[BaseTcpo] = []
            db_items: list[Any] = []
            avisos: list[str] = []
            total_rows = 0

            def _find_sheet(*keywords: str) -> str | None:
                for sheet in wb.sheetnames:
                    up = sheet.upper()
                    if all(k.upper() in up for k in keywords):
                        return sheet
                return None

            s = _find_sheet("MÃO DE OBRA") or _find_sheet("MAO DE OBRA")
            if s:
                for row in wb[s].iter_rows(min_row=2, values_only=True):
                    if not row or row[0] is None or row[1] is None:
                        continue
                    seq["MO"] = seq.get("MO", 0) + 1
                    codigo_origem = f"BCU-MO-{seq['MO']:03d}"
                    desc = str(row[1]).strip()
                    db_items.append(
                        BcuMaoObraItem(
                            id=uuid.uuid4(),
                            cabecalho_id=cab.id,
                            descricao_funcao=desc,
                            codigo_origem=codigo_origem,
                            salario=_to_decimal(row[2]) if len(row) > 2 else None,
                            previsao_reajuste=_to_decimal(row[3]) if len(row) > 3 else None,
                            periculosidade_insalubridade=_to_decimal(row[4]) if len(row) > 4 else None,
                            refeicao=_to_decimal(row[5]) if len(row) > 5 else None,
                            agua_potavel=_to_decimal(row[6]) if len(row) > 6 else None,
                            vale_alimentacao=_to_decimal(row[7]) if len(row) > 7 else None,
                            plano_saude=_to_decimal(row[8]) if len(row) > 8 else None,
                            seguro_vida=_to_decimal(row[9]) if len(row) > 9 else None,
                            abono_ferias=_to_decimal(row[10]) if len(row) > 10 else None,
                        )
                    )
                    total_rows += 1
                    all_base_tcpo.append(
                        BaseTcpo(
                            id=uuid.uuid4(),
                            codigo_origem=codigo_origem,
                            descricao=desc,
                            unidade_medida="H",
                            custo_base=_to_decimal(row[2]) or 0.0,
                            tipo_recurso="MO",
                        )
                    )
            else:
                avisos.append("Aba 'MÃO DE OBRA' não encontrada.")

            s = _find_sheet("EQUIPAMENTO")
            if s:
                for row in wb[s].iter_rows(min_row=2, values_only=True):
                    if not row or row[0] is None or row[1] is None:
                        continue
                    seq["EQP"] = seq.get("EQP", 0) + 1
                    codigo_origem = f"BCU-EQP-{seq['EQP']:03d}"
                    desc = str(row[1]).strip()
                    db_items.append(
                        BcuEquipamentoItem(
                            id=uuid.uuid4(),
                            cabecalho_id=cab.id,
                            codigo=str(row[0]).strip() if row[0] else None,
                            codigo_origem=codigo_origem,
                            equipamento=desc,
                            combustivel_utilizado=str(row[2]).strip() if len(row) > 2 and row[2] else None,
                            consumo_l_h=_to_decimal(row[3]) if len(row) > 3 else None,
                            aluguel_r_h=_to_decimal(row[4]) if len(row) > 4 else None,
                            aluguel_mensal=_to_decimal(row[5]) if len(row) > 5 else None,
                        )
                    )
                    total_rows += 1
                    all_base_tcpo.append(
                        BaseTcpo(
                            id=uuid.uuid4(),
                            codigo_origem=codigo_origem,
                            descricao=desc,
                            unidade_medida="H",
                            custo_base=_to_decimal(row[4]) or 0.0,
                            tipo_recurso="EQUIPAMENTO",
                        )
                    )
            else:
                avisos.append("Aba 'EQUIPAMENTOS' não encontrada.")

            s = _find_sheet("ENCARGO")
            if s:
                for row in wb[s].iter_rows(min_row=2, values_only=True):
                    if not row or row[0] is None or row[4] is None:
                        continue
                    tipo = str(row[1]).strip().upper() if len(row) > 1 and row[1] else "HORISTA"
                    if tipo not in ("HORISTA", "MENSALISTA"):
                        tipo = "HORISTA"
                    db_items.append(
                        BcuEncargoItem(
                            id=uuid.uuid4(),
                            cabecalho_id=cab.id,
                            tipo_encargo=tipo,
                            grupo=str(row[2]).strip() if len(row) > 2 and row[2] else None,
                            codigo_grupo=str(row[3]).strip() if len(row) > 3 and row[3] else None,
                            discriminacao_encargo=str(row[4]).strip(),
                            taxa_percent=_to_decimal(row[5]) if len(row) > 5 else None,
                        )
                    )
                    total_rows += 1
            else:
                avisos.append("Aba 'ENCARGOS' não encontrada.")

            s = _find_sheet("EPI")
            if s:
                for row in wb[s].iter_rows(min_row=2, values_only=True):
                    if not row or row[0] is None or row[1] is None:
                        continue
                    seq["EPI"] = seq.get("EPI", 0) + 1
                    codigo_origem = f"BCU-EPI-{seq['EPI']:03d}"
                    desc = str(row[1]).strip()
                    db_items.append(
                        BcuEpiItem(
                            id=uuid.uuid4(),
                            cabecalho_id=cab.id,
                            codigo_origem=codigo_origem,
                            epi=desc,
                            unidade=str(row[2]).strip() if len(row) > 2 and row[2] else "UN",
                            custo_unitario=_to_decimal(row[3]) if len(row) > 3 else None,
                            vida_util_meses=_to_decimal(row[4]) if len(row) > 4 else None,
                        )
                    )
                    total_rows += 1
                    all_base_tcpo.append(
                        BaseTcpo(
                            id=uuid.uuid4(),
                            codigo_origem=codigo_origem,
                            descricao=desc,
                            unidade_medida=str(row[2]).strip() if len(row) > 2 and row[2] else "UN",
                            custo_base=_to_decimal(row[3]) or 0.0,
                            tipo_recurso="INSUMO",
                        )
                    )
            else:
                avisos.append("Aba 'EPI' não encontrada.")

            s = _find_sheet("FERRAMENTA")
            if s:
                for row in wb[s].iter_rows(min_row=2, values_only=True):
                    if not row or row[0] is None or row[1] is None:
                        continue
                    seq["FER"] = seq.get("FER", 0) + 1
                    codigo_origem = f"BCU-FER-{seq['FER']:03d}"
                    desc = str(row[1]).strip()
                    db_items.append(
                        BcuFerramentaItem(
                            id=uuid.uuid4(),
                            cabecalho_id=cab.id,
                            codigo_origem=codigo_origem,
                            descricao=desc,
                            unidade=str(row[2]).strip() if len(row) > 2 and row[2] else "UN",
                            preco=_to_decimal(row[3]) if len(row) > 3 else None,
                        )
                    )
                    total_rows += 1
                    all_base_tcpo.append(
                        BaseTcpo(
                            id=uuid.uuid4(),
                            codigo_origem=codigo_origem,
                            descricao=desc,
                            unidade_medida=str(row[2]).strip() if len(row) > 2 and row[2] else "UN",
                            custo_base=_to_decimal(row[3]) or 0.0,
                            tipo_recurso="FERRAMENTA",
                        )
                    )
            else:
                avisos.append("Aba 'FERRAMENTAS' não encontrada.")

            s = _find_sheet("EXAME")
            if s:
                count = sum(
                    1 for row in wb[s].iter_rows(min_row=2, values_only=True)
                    if row and row[0] is not None and row[1] is not None
                )
                avisos.append(
                    f"Aba 'EXAMES' identificada ({count} linhas) — schema BCU atual não tem tabela "
                    f"para Exames. Dados ignorados; criar tabela em sprint futura."
                )
            else:
                avisos.append("Aba 'EXAMES' não encontrada (opcional).")

            result = await self.db.execute(
                select(BcuCabecalho).where(BcuCabecalho.nome_arquivo == nome_arquivo)
            )
            for existing in result.scalars().all():
                await self.db.delete(existing)
            await self.db.flush()

            if avisos:
                cab.observacao = " | ".join(avisos)[:2000]
            self.db.add(cab)
            self.db.add_all(db_items)
            await _sync_base_tcpo_batch(self.db, all_base_tcpo)

            logger.info(
                "bcu.import_converter_complete",
                arquivo=nome_arquivo,
                cabecalho_id=str(cab.id),
                rows=total_rows,
                base_tcpo_synced=len(all_base_tcpo),
                avisos=len(avisos),
            )
            await self.db.commit()
            await self.db.refresh(cab)
            return cab
        except Exception:
            await self.db.rollback()
            raise

    async def ativar_cabecalho(self, cabecalho_id: uuid.UUID) -> BcuCabecalho:
        cab = await self.db.get(BcuCabecalho, cabecalho_id)
        if not cab:
            raise ValueError("Cabecalho nao encontrado")

        # Desativa todos
        await self.db.execute(
            update(BcuCabecalho).values(is_ativo=False)
        )
        # Ativa o solicitado
        cab.is_ativo = True
        self.db.add(cab)
        await self.db.commit()
        await self.db.refresh(cab)
        return cab

    async def get_cabecalho_ativo(self) -> BcuCabecalho | None:
        result = await self.db.execute(
            select(BcuCabecalho).where(BcuCabecalho.is_ativo == True).limit(1)
        )
        return result.scalar_one_or_none()
