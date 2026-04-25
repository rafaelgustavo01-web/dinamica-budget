# UX Frontend do Módulo de Orçamentos — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar telas React funcionais para o fluxo completo de Orçamentos: criar proposta, listar propostas, importar PQ, executar match, visualizar CPU, e aprovar/reprovar proposta.

**Architecture:** Feature-based React com React Query para cache, Zod para validação de formulários, shadcn/ui para componentes base. Reusa padrões existentes (auth, admin, clientes).

**Tech Stack:** React 18, TypeScript, Tailwind CSS, shadcn/ui, React Query, Zod, React Router, Axios.

---

## Task 1: Estrutura de Features e Rotas

**Files:**
- Create: `app/frontend/src/features/proposals/routes.tsx`
- Create: `app/frontend/src/features/proposals/types.ts`
- Modify: `app/frontend/src/App.tsx` ou router principal

### Step 1: Criar tipos

```typescript
// app/frontend/src/features/proposals/types.ts
export interface Proposta {
  id: string;
  codigo: string;
  titulo: string | null;
  descricao: string | null;
  status: "RASCUNHO" | "EM_ANALISE" | "CPU_GERADA" | "APROVADA" | "REPROVADA" | "ARQUIVADA";
  cliente_id: string;
  total_geral: number | null;
  data_criacao: string;
}

export interface PropostaFormData {
  titulo?: string;
  descricao?: string;
}

export interface PqItem {
  id: string;
  descricao_original: string;
  quantidade_original: number;
  match_status: string;
  match_confidence: number | null;
}

export interface CpuItem {
  id: string;
  codigo: string;
  descricao: string;
  quantidade: number;
  preco_unitario: number;
  preco_total: number;
}
```

### Step 2: Criar rotas

```tsx
// app/frontend/src/features/proposals/routes.tsx
import { Route } from "react-router-dom";
import { ProposalsListPage } from "./pages/ProposalsListPage";
import { ProposalCreatePage } from "./pages/ProposalCreatePage";
import { ProposalDetailPage } from "./pages/ProposalDetailPage";
import { ProposalImportPage } from "./pages/ProposalImportPage";
import { ProposalCpuPage } from "./pages/ProposalCpuPage";

export const proposalRoutes = [
  <Route key="proposals" path="/propostas">
    <Route index element={<ProposalsListPage />} />
    <Route path="nova" element={<ProposalCreatePage />} />
    <Route path=":id" element={<ProposalDetailPage />} />
    <Route path=":id/importar" element={<ProposalImportPage />} />
    <Route path=":id/cpu" element={<ProposalCpuPage />} />
  </Route>,
];
```

### Step 3: Commit

```bash
git add app/frontend/src/features/proposals/
git commit -m "feat(ux): add proposal feature structure and types"
```

---

## Task 2: Tela — Listagem de Propostas

**Files:**
- Create: `app/frontend/src/features/proposals/pages/ProposalsListPage.tsx`
- Create: `app/frontend/src/features/proposals/components/ProposalsTable.tsx`

### Step 1: Página de listagem

```tsx
// app/frontend/src/features/proposals/pages/ProposalsListPage.tsx
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/shared/components/PageHeader";
import { ProposalsTable } from "../components/ProposalsTable";
import { api } from "@/lib/api";

export function ProposalsListPage() {
  const navigate = useNavigate();
  const { data, isLoading } = useQuery({
    queryKey: ["propostas"],
    queryFn: () => api.get("/propostas/").then((r) => r.data),
  });

  return (
    <div className="space-y-4">
      <PageHeader title="Orçamentos" subtitle="Gerencie suas propostas comerciais">
        <Button onClick={() => navigate("/propostas/nova")}>Nova Proposta</Button>
      </PageHeader>
      {isLoading ? <p>Carregando...</p> : <ProposalsTable propostas={data?.items ?? []} />}
    </div>
  );
}
```

### Step 2: Tabela

```tsx
// app/frontend/src/features/proposals/components/ProposalsTable.tsx
import { useNavigate } from "react-router-dom";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { StatusBadge } from "@/shared/components/StatusBadge";
import type { Proposta } from "../types";

export function ProposalsTable({ propostas }: { propostas: Proposta[] }) {
  const navigate = useNavigate();
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Código</TableHead>
          <TableHead>Título</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Total</TableHead>
          <TableHead>Criada em</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {propostas.map((p) => (
          <TableRow key={p.id} onClick={() => navigate(`/propostas/${p.id}`)} className="cursor-pointer">
            <TableCell>{p.codigo}</TableCell>
            <TableCell>{p.titulo || "—"}</TableCell>
            <TableCell><StatusBadge status={p.status} /></TableCell>
            <TableCell>{p.total_geral?.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) || "—"}</TableCell>
            <TableCell>{new Date(p.data_criacao).toLocaleDateString("pt-BR")}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
```

### Step 3: Commit

```bash
git add app/frontend/src/features/proposals/pages/ app/frontend/src/features/proposals/components/
git commit -m "feat(ux): add proposals list page"
```

---

## Task 3: Tela — Criar Proposta

**Files:**
- Create: `app/frontend/src/features/proposals/pages/ProposalCreatePage.tsx`
- Create: `app/frontend/src/features/proposals/components/ProposalForm.tsx`

### Step 1: Formulário

```tsx
// app/frontend/src/features/proposals/components/ProposalForm.tsx
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { PropostaFormData } from "../types";

interface Props {
  onSubmit: (data: PropostaFormData) => void;
  isLoading?: boolean;
}

export function ProposalForm({ onSubmit, isLoading }: Props) {
  const [titulo, setTitulo] = useState("");
  const [descricao, setDescricao] = useState("");

  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit({ titulo, descricao }); }} className="space-y-4 max-w-lg">
      <div>
        <Label htmlFor="titulo">Título</Label>
        <Input id="titulo" value={titulo} onChange={(e) => setTitulo(e.target.value)} />
      </div>
      <div>
        <Label htmlFor="descricao">Descrição</Label>
        <Textarea id="descricao" value={descricao} onChange={(e) => setDescricao(e.target.value)} />
      </div>
      <Button type="submit" disabled={isLoading}>Criar Proposta</Button>
    </form>
  );
}
```

### Step 2: Página

```tsx
// app/frontend/src/features/proposals/pages/ProposalCreatePage.tsx
import { useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { PageHeader } from "@/shared/components/PageHeader";
import { ProposalForm } from "../components/ProposalForm";
import { api } from "@/lib/api";

export function ProposalCreatePage() {
  const navigate = useNavigate();
  const qc = useQueryClient();

  const mutation = useMutation({
    mutationFn: (data: { titulo?: string; descricao?: string }) => api.post("/propostas/", data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["propostas"] });
      navigate("/propostas");
    },
  });

  return (
    <div className="space-y-4">
      <PageHeader title="Nova Proposta" />
      <ProposalForm onSubmit={(d) => mutation.mutate(d)} isLoading={mutation.isPending} />
    </div>
  );
}
```

### Step 3: Commit

```bash
git add app/frontend/src/features/proposals/pages/ProposalCreatePage.tsx app/frontend/src/features/proposals/components/ProposalForm.tsx
git commit -m "feat(ux): add proposal create page"
```

---

## Task 4: Tela — Importar PQ e Match

**Files:**
- Create: `app/frontend/src/features/proposals/pages/ProposalImportPage.tsx`

### Step 1: Página de importação

```tsx
// app/frontend/src/features/proposals/pages/ProposalImportPage.tsx
import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/shared/components/PageHeader";
import { api } from "@/lib/api";

export function ProposalImportPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [file, setFile] = useState<File | null>(null);

  const uploadMutation = useMutation({
    mutationFn: async (f: File) => {
      const formData = new FormData();
      formData.append("arquivo", f);
      return api.post(`/propostas/${id}/importar/planilha`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["proposta", id] }),
  });

  const matchMutation = useMutation({
    mutationFn: () => api.post(`/propostas/${id}/importar/match`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["proposta", id] }),
  });

  return (
    <div className="space-y-4">
      <PageHeader title="Importar Planilha Quantitativa" />
      <div className="space-y-2">
        <input type="file" accept=".xlsx,.csv" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        <Button onClick={() => file && uploadMutation.mutate(file)} disabled={!file || uploadMutation.isPending}>
          {uploadMutation.isPending ? "Enviando..." : "Enviar Planilha"}
        </Button>
      </div>
      <Button onClick={() => matchMutation.mutate()} disabled={matchMutation.isPending}>
        {matchMutation.isPending ? "Executando match..." : "Executar Match Inteligente"}
      </Button>
    </div>
  );
}
```

### Step 2: Commit

```bash
git add app/frontend/src/features/proposals/pages/ProposalImportPage.tsx
git commit -m "feat(ux): add proposal import and match page"
```

---

## Task 5: Tela — Visualizar CPU

**Files:**
- Create: `app/frontend/src/features/proposals/pages/ProposalCpuPage.tsx`
- Create: `app/frontend/src/features/proposals/components/CpuTable.tsx`

### Step 1: Tabela de CPU

```tsx
// app/frontend/src/features/proposals/components/CpuTable.tsx
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { CpuItem } from "../types";

export function CpuTable({ itens }: { itens: CpuItem[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Código</TableHead>
          <TableHead>Descrição</TableHead>
          <TableHead>Qtd</TableHead>
          <TableHead>Preço Unit.</TableHead>
          <TableHead>Preço Total</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {itens.map((i) => (
          <TableRow key={i.id}>
            <TableCell>{i.codigo}</TableCell>
            <TableCell>{i.descricao}</TableCell>
            <TableCell>{i.quantidade}</TableCell>
            <TableCell>{i.preco_unitario.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}</TableCell>
            <TableCell>{i.preco_total.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
```

### Step 2: Página de CPU

```tsx
// app/frontend/src/features/proposals/pages/ProposalCpuPage.tsx
import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/shared/components/PageHeader";
import { CpuTable } from "../components/CpuTable";
import { api } from "@/lib/api";

export function ProposalCpuPage() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const [bdi, setBdi] = useState("0");

  const { data: itens, isLoading } = useQuery({
    queryKey: ["proposta-cpu", id],
    queryFn: () => api.get(`/propostas/${id}/cpu/itens`).then((r) => r.data),
    enabled: !!id,
  });

  const gerarMutation = useMutation({
    mutationFn: () => api.post(`/propostas/${id}/cpu/gerar`, null, { params: { percentual_bdi: parseFloat(bdi) } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["proposta-cpu", id] }),
  });

  return (
    <div className="space-y-4">
      <PageHeader title="Composição de Preços Unitários" />
      <div className="flex items-center space-x-2">
        <label>BDI (%):</label>
        <input type="number" value={bdi} onChange={(e) => setBdi(e.target.value)} className="border rounded px-2 py-1 w-24" />
        <Button onClick={() => gerarMutation.mutate()} disabled={gerarMutation.isPending}>
          {gerarMutation.isPending ? "Gerando..." : "Gerar CPU"}
        </Button>
      </div>
      {isLoading ? <p>Carregando...</p> : <CpuTable itens={itens ?? []} />}
    </div>
  );
}
```

### Step 3: Commit

```bash
git add app/frontend/src/features/proposals/pages/ProposalCpuPage.tsx app/frontend/src/features/proposals/components/CpuTable.tsx
git commit -m "feat(ux): add CPU visualization page"
```

---

## Task 6: Integrar Rotas e Smoke Test

**Files:**
- Modify: `app/frontend/src/App.tsx` (ou arquivo de rotas principal)

### Step 1: Adicionar rotas ao router

```tsx
// Importar no router principal
import { proposalRoutes } from "./features/proposals/routes";

// Dentro do Routes/Route tree
{proposalRoutes}
```

### Step 2: Smoke test

```bash
cd frontend
npm run build
```

Expected: build sem erros TypeScript

### Step 3: Commit

```bash
git add app/frontend/src/App.tsx
git commit -m "feat(ux): integrate proposal routes into main router"
```

---

## Task 7: Walkthrough

**Files:**
- Create: `docs/sprints/S-12/walkthrough/done/walkthrough-S-12.md`

### Step 1: Documentar entrega

Resumo das telas entregues, decisões de UX, e instruções de uso.

### Step 2: Commit

```bash
git add docs/sprints/S-12/walkthrough/done/walkthrough-S-12.md
git commit -m "docs(s-12): add walkthrough for proposal frontend UX"
```

---

## Plan Review Checklist

- [x] Spec coverage: listagem, criação, importação, match, CPU, rotas
- [x] Placeholder scan: no TBD/TODO found
- [x] Reuses existing UI components (PageHeader, Table, Button, StatusBadge)
- [x] Type consistency: React Query + Zod patterns consistentes com codebase

## Handoff

**Plan complete and saved to `docs/sprints/S-11/plans/2026-04-23-ux-frontend-modulo-orcamentos.md`.**

Two execution options:

1. **Subagent-Driven (recommended)** — dispatch subagent per task, review between tasks
2. **Inline Execution** — execute in this session with checkpoints

Which approach?



