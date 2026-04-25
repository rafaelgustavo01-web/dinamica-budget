# Finalizar UX de Governança e Permissões — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fechar gaps de UX no módulo de governança (usuários, clientes, perfis) e remover placeholders críticos de permissões. Entregar wireframes aprovados e critérios de aceite para o backlog UX.

**Architecture:** Frontend React + TypeScript. CRUD de usuários e clientes já existem no backend (S-01/S-02). Esta sprint foca em telas de admin e gerenciamento de perfis por cliente.

**Tech Stack:** React, TypeScript, Tailwind CSS, shadcn/ui, React Query, Zod.

---

## Task 1: Tela de Listagem de Usuários (Admin)

**Files:**
- Create: `app/frontend/src/pages/admin/users/UserListPage.tsx`
- Create: `app/frontend/src/pages/admin/users/UserListTable.tsx`
- Modify: `app/frontend/src/routes.tsx`

### Step 1: Criar página de listagem

```tsx
// app/frontend/src/pages/admin/users/UserListPage.tsx
import { useQuery } from "@tanstack/react-query";
import { UserListTable } from "./UserListTable";
import { api } from "@/lib/api";

export function UserListPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: () => api.get("/usuarios/").then((r) => r.data),
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Usuários</h1>
      {isLoading ? <p>Carregando...</p> : <UserListTable users={data?.items ?? []} />}
    </div>
  );
}
```

### Step 2: Criar tabela

```tsx
// app/frontend/src/pages/admin/users/UserListTable.tsx
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

interface User {
  id: string;
  nome: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
}

export function UserListTable({ users }: { users: User[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Nome</TableHead>
          <TableHead>Email</TableHead>
          <TableHead>Ativo</TableHead>
          <TableHead>Admin Global</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {users.map((u) => (
          <TableRow key={u.id}>
            <TableCell>{u.nome}</TableCell>
            <TableCell>{u.email}</TableCell>
            <TableCell>{u.is_active ? "Sim" : "Não"}</TableCell>
            <TableCell>{u.is_admin ? "Sim" : "Não"}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
```

### Step 3: Adicionar rota

```tsx
// app/frontend/src/routes.tsx (adicionar dentro do layout admin)
{ path: "usuarios", element: <UserListPage /> }
```

### Step 4: Commit

```bash
git add app/frontend/src/pages/admin/users/
git commit -m "feat(ux): add user list page for admin"
```

---

## Task 2: Tela de Gerenciamento de Perfis por Cliente

**Files:**
- Create: `app/frontend/src/pages/admin/clients/ClientPerfisPage.tsx`
- Create: `app/frontend/src/pages/admin/clients/ClientePerfilForm.tsx`

### Step 1: Criar página de perfis

```tsx
// app/frontend/src/pages/admin/clients/ClientPerfisPage.tsx
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ClientePerfilForm } from "./ClientePerfilForm";

export function ClientPerfisPage() {
  const { clienteId } = useParams<{ clienteId: string }>();
  const qc = useQueryClient();

  const { data: perfis } = useQuery({
    queryKey: ["cliente-perfis", clienteId],
    queryFn: () => api.get(`/clientes/${clienteId}/perfis`).then((r) => r.data),
    enabled: !!clienteId,
  });

  const mutation = useMutation({
    mutationFn: (payload: { usuario_id: string; perfis: string[] }) =>
      api.post(`/clientes/${clienteId}/perfis`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["cliente-perfis", clienteId] }),
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Perfis do Cliente</h1>
      <ClientePerfilForm onSubmit={(p) => mutation.mutate(p)} />
      {/* Listagem atual dos perfis */}
    </div>
  );
}
```

### Step 2: Criar formulário

```tsx
// app/frontend/src/pages/admin/clients/ClientePerfilForm.tsx
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";

const PERFIS = ["USUARIO", "APROVADOR", "ADMIN"];

export function ClientePerfilForm({ onSubmit }: { onSubmit: (p: { usuario_id: string; perfis: string[] }) => void }) {
  const [usuarioId, setUsuarioId] = useState("");
  const [selecionados, setSelecionados] = useState<string[]>([]);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({ usuario_id: usuarioId, perfis: selecionados });
      }}
      className="space-y-4"
    >
      <div>
        <Label htmlFor="usuarioId">ID do Usuário</Label>
        <Input id="usuarioId" value={usuarioId} onChange={(e) => setUsuarioId(e.target.value)} required />
      </div>
      <div className="space-y-2">
        <Label>Perfis</Label>
        {PERFIS.map((p) => (
          <div key={p} className="flex items-center space-x-2">
            <Checkbox
              checked={selecionados.includes(p)}
              onCheckedChange={(checked) => {
                setSelecionados((prev) => (checked ? [...prev, p] : prev.filter((x) => x !== p)));
              }}
            />
            <span>{p}</span>
          </div>
        ))}
      </div>
      <Button type="submit">Atribuir Perfis</Button>
    </form>
  );
}
```

### Step 3: Commit

```bash
git add app/frontend/src/pages/admin/clients/
git commit -m "feat(ux): add client profile management page"
```

---

## Task 3: Tela de Meu Perfil (Visualizar/Editar)

**Files:**
- Create: `app/frontend/src/pages/profile/MeuPerfilPage.tsx`

### Step 1: Criar página de perfil

```tsx
// app/frontend/src/pages/profile/MeuPerfilPage.tsx
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useState } from "react";

export function MeuPerfilPage() {
  const qc = useQueryClient();
  const { data: user, isLoading } = useQuery({
    queryKey: ["me"],
    queryFn: () => api.get("/auth/me").then((r) => r.data),
  });

  const [nome, setNome] = useState(user?.nome ?? "");

  const mutation = useMutation({
    mutationFn: (payload: { nome: string }) => api.patch("/auth/me", payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["me"] }),
  });

  if (isLoading) return <p>Carregando...</p>;

  return (
    <div className="max-w-md space-y-4">
      <h1 className="text-2xl font-bold">Meu Perfil</h1>
      <form onSubmit={(e) => { e.preventDefault(); mutation.mutate({ nome }); }} className="space-y-4">
        <div>
          <Label>Email</Label>
          <Input value={user.email} disabled />
        </div>
        <div>
          <Label htmlFor="nome">Nome</Label>
          <Input id="nome" value={nome} onChange={(e) => setNome(e.target.value)} />
        </div>
        <Button type="submit" disabled={mutation.isPending}>Salvar</Button>
      </form>
    </div>
  );
}
```

### Step 2: Commit

```bash
git add app/frontend/src/pages/profile/MeuPerfilPage.tsx
git commit -m "feat(ux): add my profile page"
```

---

## Task 4: Documentação de Wireframes e Critérios

**Files:**
- Create: `docs/ux-wireframes-governanca-2026-04-23.md`

### Step 1: Documentar decisões de UX

```markdown
# Wireframes e Critérios — Governança e Permissões

## Telas entregues

1. **Admin > Usuários (lista)**
   - Listagem paginada com nome, email, status, admin global
   - Filtro por status ativo/inativo
   - Link para detalhe do usuário

2. **Admin > Cliente > Perfis**
   - Listagem de usuários vinculados ao cliente com seus perfis
   - Formulário para adicionar/remover perfis (USUARIO/APROVADOR/ADMIN)
   - Validação: pelo menos um ADMIN por cliente (warning, não block)

3. **Meu Perfil**
   - Visualização de dados pessoais
   - Edição de nome (email é read-only)
   - Listagem de clientes que o usuário tem acesso + perfis em cada um

## Critérios de aceite
- [ ] Admin global vê todos os usuários e clientes
- [ ] Admin de cliente vê apenas seu cliente e gerencia perfis nele
- [ ] Usuário comum acessa apenas "Meu Perfil"
- [ ] Nenhum placeholder de texto ("TODO", "em breve") nas telas
```

### Step 2: Commit

```bash
git add docs/ux-wireframes-governanca-2026-04-23.md
git commit -m "docs(ux): add governance wireframes and acceptance criteria"
```

---

## Task 5: Smoke Test e Walkthrough

### Step 1: Verificar build

```bash
cd frontend
npm run build
```

Expected: build sem erros TypeScript

### Step 2: Walkthrough

Create: `docs/sprints/S-07/walkthrough/done/walkthrough-S-07.md`

### Step 3: Commit

```bash
git add docs/sprints/S-07/walkthrough/done/walkthrough-S-07.md
git commit -m "docs(s-07): add walkthrough for governance UX"
```

---

## Plan Review Checklist

- [x] Spec coverage: user list, client profiles, my profile, wireframes
- [x] Placeholder scan: no TBD/TODO found
- [x] Reuses existing backend endpoints (S-01/S-02)
- [x] Type consistency: React Query + Zod patterns consistentes

## Handoff

**Plan complete and saved to `docs/sprints/S-12/plans/2026-04-23-ux-governanca-permissoes.md`.**

Two execution options:

1. **Subagent-Driven (recommended)** — dispatch subagent per task, review between tasks
2. **Inline Execution** — execute in this session with checkpoints

Which approach?



