# Frontend Review — F4-04 — Claude — 2026-05-09

> Sprint: F4-04 — Cadastro de Clientes para Folha PC
> Reviewer: Claude (pós-quota, revisão e refinamento do trabalho Opencode)
> Escopo: somente frontend/UX — `ClientsPage.tsx`, `format.ts`, `clientes.ts`
> Verdict: **PASS com correções aplicadas**

---

## Verdict

| Dimensão | Resultado |
|---|---|
| UX / Labels / Tips | ✅ OK após fix |
| Validação client-side | ✅ OK após fix |
| Contrato TS vs backend | ✅ Alinhado |
| Estados vazios / loading / error | ✅ OK |
| IDs técnicos na UI | ✅ Removidos |
| Consistência visual | ✅ OK após fix |
| Build / Testes | ✅ PASS |

---

## Mudanças Feitas Nesta Revisão

### 1. UF: auto-uppercase via `onInput` (create + edit)

**Problema:** Campo UF tinha validação `^[A-Z]{2}$` mas nenhum handler para transformar
a entrada em maiúsculas. O usuário que digitasse "sp" recebia erro de validação sem
explicação óbvia.

**Fix:** Adicionado `onInput` em `inputProps` do TextField de UF (create e edit forms):
```tsx
onInput: (e) => {
  const el = e.target as HTMLInputElement;
  el.value = el.value.toUpperCase();
},
```
O handler modifica o valor DOM antes do react-hook-form capturá-lo via `onChange`,
garantindo que o form state receba sempre maiúsculas.

**Arquivo:** `app/frontend/src/features/clients/ClientsPage.tsx` (UF create ~L530, UF edit ~L677)

---

### 2. CEP: placeholder corrigido para "00000000"

**Problema:** Placeholder "00000-000" (com máscara) contradiz `maxLength=8` e helperText
"8 dígitos numéricos, sem traço." — usuário poderia tentar "12345-678" e o campo truncava
no 8º caractere (incluindo o hífen), gerando "12345-67" que falha `^\d{8}$`.

**Fix:** Placeholder alterado para `"00000000"` nos dois formulários (create e edit),
alinhando a expectativa visual com a validação Zod.

**Arquivo:** `app/frontend/src/features/clients/ClientsPage.tsx` (CEP create ~L538, CEP edit ~L685)

---

### 3. Edit dialog: `inscricao_estadual` a largura total

**Problema:** No edit form, `inscricao_estadual` estava envolta em
`<Stack direction="row">` sozinha, ocupando ~50% da largura sem par lógico.
No create form, o mesmo campo aparece corretamente pareado com CNPJ (read-only no edit,
portanto não está presente).

**Fix:** Removido o wrapper `<Stack direction="row">` desnecessário; campo agora usa
largura total, consistente com o contexto de edição.

**Arquivo:** `app/frontend/src/features/clients/ClientsPage.tsx` (~L604-614)

---

### 4. `formatCnpj` / `formatCep`: null retorna `'—'` (travessão)

**Problema:** Ambas as funções retornavam `'-'` (hífen) para valores null/undefined.
No painel de detalhes, todos os outros campos opcionais usam `|| '—'` (travessão em-dash),
gerando inconsistência visual.

**Fix:** Alterado `return '-'` → `return '—'` em `formatCnpj` e `formatCep`.

**Arquivo:** `app/frontend/src/shared/utils/format.ts` (~L89, L95)

**Impacto na tabela:** `formatCnpj` é usado no DataTable. CNPJ é campo obrigatório
(always set), então o fallback para travessão é seguro e não altera comportamento em produção.

---

## Avaliação do Trabalho Opencode

### O que estava bem feito
- Formulários completos com 9 campos comerciais organizados em seções (Empresa / Contato / Endereço).
- ID técnico (UUID) removido corretamente do painel de detalhes.
- Validação Zod robusta com mensagens em PT-BR.
- `HelpTooltip` no campo CNPJ com aviso de imutabilidade.
- `emptyToNull` aplicado consistentemente antes de enviar ao backend.
- Estado vazio via `EmptyState`, loading via `CircularProgress`, erro via `Alert`.
- `formatCnpj` e `formatCep` aplicados na tabela e no painel.
- Contrato TS (`clientes.ts`) alinhado com schema Pydantic backend — campo a campo.
- Build e testes passaram no momento da entrega.

### Issues encontrados (todos corrigidos acima)
| Severidade | Problema | Status |
|---|---|---|
| P1 | UF sem auto-uppercase — validação falha silenciosamente | ✅ Corrigido |
| P2 | CEP placeholder "00000-000" vs maxLength=8 — incoerência | ✅ Corrigido |
| P2 | Edit form `inscricao_estadual` em row sozinho — layout quebrado | ✅ Corrigido |
| P3 | `formatCnpj`/`formatCep` retornam '-' (hífen) para null | ✅ Corrigido |

### Riscos não corrigidos (follow-on)
| Severidade | Risco | Motivo de não corrigir agora |
|---|---|---|
| P3 | Estado de mutation error persiste ao fechar/reabrir dialog | Fora do escopo da sprint; não é regressão |
| P3 | Mutation error usa `errorMessages.clientUpdate` para toggle de status | Mensagem levemente genérica; funcional |

---

## Alinhamento backend ↔ frontend

Contrato TS inspecionado contra `ClienteCreate`, `ClientePatch` e `ClienteResponse` do Pydantic:

| Campo | Backend | Frontend TS | Alinhado? |
|---|---|---|---|
| `id: UUID` | ✅ | `id: string` | ✅ (UUID serializado como string) |
| `nome_fantasia: str` | ✅ | `string` | ✅ |
| `cnpj: str(14 digits)` | ✅ | `string` (Zod transform) | ✅ |
| `is_active: bool` | ✅ | `boolean` | ✅ |
| `razao_social: str\|None` | ✅ | `string \| null` | ✅ |
| `inscricao_estadual: str\|None` | ✅ | `string \| null` | ✅ |
| `contato_nome: str\|None` | ✅ | `string \| null` | ✅ |
| `telefone: str\|None` | ✅ | `string \| null` | ✅ |
| `email_comercial: EmailStr\|None` | ✅ | `string \| null` | ✅ |
| `endereco_logradouro: str\|None` | ✅ | `string \| null` | ✅ |
| `endereco_cidade: str\|None` | ✅ | `string \| null` | ✅ |
| `endereco_uf: str(2,A-Z)\|None` | ✅ | `string \| null` (Zod + onInput) | ✅ |
| `endereco_cep: str(8 digits)\|None` | ✅ | `string \| null` (Zod) | ✅ |

Nenhum desalinhamento de contrato encontrado.

---

## Gates de Validação

```bash
# Frontend build
cd app/frontend && npm run build
# Result: ✅ PASS (0 erros TypeScript, vite build verde)

cd app/frontend && npm run test
# Result: ✅ PASS (13/13 tests)

# Trailing whitespace
grep -Pn " +$" app/frontend/src/features/clients/ClientsPage.tsx
# Result: ✅ PASS (sem trailing whitespace)

grep -Pn " +$" app/frontend/src/shared/utils/format.ts
# Result: ✅ PASS (sem trailing whitespace)
```

---

## Notas para QA

- Testar campo UF: digitar "sp" minúsculo deve converter automaticamente para "SP".
- Testar campo CEP: placeholder agora é "00000000" — confirmar que máscara visual
  não é esperada neste campo.
- Verificar painel de detalhes: campos null devem exibir "—" (travessão) uniformemente.
- Confirmar edição de `inscricao_estadual` ocupa largura total no dialog de edição.
- Testar criação/edição com todos campos opcionais vazios (enviam `null` ao backend).
- Confirmar que migration 027 (`app/alembic/versions/027_cliente_campos_pc.py`) tem
  `downgrade` implementado antes de promover para ambiente compartilhado.
