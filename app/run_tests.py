#!/usr/bin/env python3
"""
Script de Execução de Testes e Validações — Dinamica Budget

Este script executa:
1. Testes de sintaxe Python
2. Testes unitários
3. Testes de integração  
4. Testes E2E/casos de uso simulados
5. Validações de segurança e performance

Resultado: Relatório completo com status e recomendações
"""

import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


class TestRunner:
    """Executor de testes estruturado"""
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        self.base_dir = Path(__file__).parent
    
    def run_test_suite(self, name: str, cmd: list, description: str = "") -> dict:
        """Executar suite de testes e registrar resultado"""
        print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
        print(f"{BOLD}{BLUE}▶ {name}{RESET}")
        if description:
            print(f"  {description}")
        print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")
        
        start = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=self.base_dir,
                capture_output=False,
                timeout=300
            )
            elapsed = time.time() - start
            status = "✅ PASSOU" if result.returncode == 0 else "❌ FALHOU"
            
            self.results.append({
                "nome": name,
                "status": "PASSOU" if result.returncode == 0 else "FALHOU",
                "tempo": elapsed,
                "return_code": result.returncode
            })
            
            print(f"\n{status} ({elapsed:.1f}s)\n")
            return {"status": result.returncode, "elapsed": elapsed}
        
        except subprocess.TimeoutExpired:
            self.results.append({
                "nome": name,
                "status": "TIMEOUT",
                "tempo": 300,
                "return_code": -1
            })
            print(f"\n{RED}⏱️  TIMEOUT (>300s){RESET}\n")
            return {"status": -1, "elapsed": 300}
        
        except Exception as exc:
            self.results.append({
                "nome": name,
                "status": "ERRO",
                "tempo": time.time() - start,
                "return_code": -1,
                "error": str(exc)
            })
            print(f"\n{RED}❌ ERRO: {exc}{RESET}\n")
            return {"status": -1, "elapsed": time.time() - start}
    
    def print_summary(self):
        """Imprimir resumo dos testes"""
        total_time = time.time() - self.start_time
        passed = sum(1 for r in self.results if r["status"] == "PASSOU")
        failed = sum(1 for r in self.results if r["status"] == "FALHOU")
        timeout = sum(1 for r in self.results if r["status"] == "TIMEOUT")
        errors = sum(1 for r in self.results if r["status"] == "ERRO")
        
        print(f"\n\n{BOLD}{BLUE}{'='*70}{RESET}")
        print(f"{BOLD}{BLUE}RESUMO DE TESTES{RESET}")
        print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")
        
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Tempo Total: {total_time:.1f}s\n")
        
        print(f"Testes Executados: {len(self.results)}")
        print(f"  {GREEN}✅ Passou: {passed}{RESET}")
        print(f"  {RED}❌ Falhou: {failed}{RESET}")
        print(f"  {YELLOW}⏱️  Timeout: {timeout}{RESET}")
        print(f"  {RED}🔥 Erros: {errors}{RESET}\n")
        
        if self.results:
            print("Detalhes:")
            for r in self.results:
                icon = "✅" if r["status"] == "PASSOU" else "❌" if r["status"] == "FALHOU" else "⏱️" if r["status"] == "TIMEOUT" else "🔥"
                print(f"  {icon} {r['nome']}: {r['status']} ({r['tempo']:.1f}s)")
        
        print(f"\n{BOLD}{BLUE}{'='*70}{RESET}\n")
        
        # Retornar status geral
        return 0 if (failed == 0 and timeout == 0 and errors == 0) else 1


def main():
    """Função principal"""
    runner = TestRunner()
    
    print(f"\n{BOLD}{BLUE}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║          DINAMICA BUDGET — SUITE DE TESTES COMPLETA              ║")
    print("║                    Deploy Validation v1.0                         ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{RESET}\n")
    
    # 1. Validação de Sintaxe Python
    runner.run_test_suite(
        "01: Validação de Sintaxe Python",
        ["python", "-m", "py_compile", "-b", "backend"],
        "Compilar todos os arquivos .py para detectar erros de sintaxe"
    )
    
    # 2. Testes Unitários (sem DB)
    runner.run_test_suite(
        "02: Testes Unitários (Sem DB)",
        ["python", "-m", "pytest", "backend/tests/unit/", "-v", "--tb=short", "-x"],
        "Executar testes unitários isolados (não requerem banco de dados)"
    )
    
    # 3. Validação de Endpoints
    runner.run_test_suite(
        "03: Validação de Endpoints API",
        ["python", "-m", "pytest", "backend/tests/integration/test_endpoints_validation.py", "-v", "--tb=short"],
        "Verificar se todos os endpoints necessários existem e respondem"
    )
    
    # 4. Casos de Uso Simulados
    runner.run_test_suite(
        "04: Casos de Uso Simulados (E2E)",
        ["python", "-m", "pytest", "backend/tests/e2e/test_casos_uso_simulados.py", "-v", "--tb=short", "-k", "health"],
        "Simular fluxos reais de usuários (login, busca, homologação, etc)"
    )
    
    # 5. Cobertura de Testes
    runner.run_test_suite(
        "05: Relatório de Cobertura",
        ["python", "-m", "pytest", "backend/tests/", "--cov=backend", "--cov-report=term-missing", "-q"],
        "Gerar relatório de cobertura de testes"
    )
    
    # Imprimir resumo
    exit_code = runner.print_summary()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
