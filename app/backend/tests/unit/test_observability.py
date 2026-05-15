from backend.core.observability import classify_operation


def test_classify_spreadsheet_and_cpu_operations():
    assert classify_operation("/api/v1/smart-import") == "planilha.smart_import"
    assert classify_operation("/api/v1/propostas/abc/pq/importar") == "planilha.pq_import"
    assert classify_operation("/api/v1/propostas/abc/pq/match") == "planilha.pq_match"
    assert classify_operation("/api/v1/propostas/abc/cpu") == "cpu.calculo"


def test_classify_tcpo_search_operations():
    assert classify_operation("/api/v1/busca") == "tcpo.busca"
    assert classify_operation("/api/v1/servicos") == "tcpo.busca"
    assert classify_operation("/api/v1/composicoes/abc/explodir") == "tcpo.busca"
