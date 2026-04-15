# Brand Guide — Dinâmica Budget

> Sistema de orçamentação inteligente para construção civil  
> Construtora Dinâmica (Dinâmica Engenharia) — Minas Gerais, Brasil

**Versão:** 1.0  
**Data:** 26 de março de 2026  
**Stack:** React 19 + MUI 7 + Emotion + TypeScript

---

## Sumário

1. [Paleta de Cores](#1-paleta-de-cores)
2. [Tipografia](#2-tipografia)
3. [Espaçamento e Layout](#3-espaçamento-e-layout)
4. [Componentes — Design Tokens](#4-componentes--design-tokens)
5. [Iconografia e Elementos Visuais](#5-iconografia-e-elementos-visuais)
6. [Dark Mode](#6-dark-mode)
7. [Tema MUI Pronto](#7-tema-mui-pronto)

---

## 1. Paleta de Cores

Toda a paleta é derivada das duas cores institucionais da Construtora Dinâmica: **azul marinho** (confiança, solidez) e **amarelo/dourado** (dinamismo, progresso). O estilo é corporativo e sóbrio — a cor é usada com intenção, nunca como decoração.

### 1.1 Cores Primárias

| Variável CSS | Hex | Role MUI | Uso | Contraste sobre branco |
|---|---|---|---|---|
| `--color-primary-900` | `#0E1525` | — | Backgrounds ultra-escuros | 18.70:1 ✅ |
| `--color-primary-800` | `#1B2A4A` | `palette.primary.dark` | Sidebar, AppBar, headers | 14.22:1 ✅ |
| `--color-primary-700` | `#243660` | — | Hover sobre primary.dark | 11.18:1 ✅ |
| `--color-primary-600` | `#2D4276` | — | Active states em nav | 8.52:1 ✅ |
| `--color-primary-main` | `#1B3A6B` | `palette.primary.main` | Botões, links, ações primárias | 11.37:1 ✅ |
| `--color-primary-400` | `#3A5490` | — | Ícones secundários | 7.37:1 ✅ |
| `--color-primary-300` | `#5A7AB5` | `palette.primary.light` | Borders com ênfase, tags | 4.30:1 (AA large ✅) |
| `--color-primary-200` | `#8AA4D0` | — | Backgrounds de ênfase suave | 3.04:1 (decorativo) |
| `--color-primary-100` | `#B5C7E3` | — | Backgrounds sutis | decorativo |
| `--color-primary-50` | `#EDF1F8` | — | Row hover em tabelas, tints | decorativo |

**`palette.primary.contrastText`: `#FFFFFF`** — branco sobre qualquer primary de 400+.

### 1.2 Cores Secundárias / Accent (Dourado)

| Variável CSS | Hex | Role MUI | Uso | Contraste |
|---|---|---|---|---|
| `--color-secondary-dark` | `#8B6209` | `palette.secondary.dark` | Texto accent acessível sobre branco | 5.46:1 ✅ AA |
| `--color-secondary-main` | `#E8A623` | `palette.secondary.main` | Badges, highlights, accent decorativo | Use apenas sobre navy (6.71:1 ✅) |
| `--color-secondary-light` | `#F0C05C` | `palette.secondary.light` | Backgrounds accent suaves | decorativo |
| `--color-secondary-50` | `#FDF3DD` | — | Background de alertas/destaque | decorativo |

**`palette.secondary.contrastText`: `#1B2A4A`** — navy sobre dourado.

> ⚠️ **Regra de acessibilidade:** O dourado `#E8A623` NÃO tem contraste suficiente sobre branco (2.12:1). Nunca use como cor de texto sobre fundo claro. Para texto dourado acessível, use `#8B6209`. O dourado principal funciona como accent sobre fundo navy (6.71:1).

### 1.3 Cores Neutras — Light Mode

| Variável CSS | Hex | Role MUI | Uso |
|---|---|---|---|
| `--color-bg-default` | `#F8F9FA` | `palette.background.default` | Background da aplicação |
| `--color-bg-paper` | `#FFFFFF` | `palette.background.paper` | Cards, modais, surfaces |
| `--color-bg-subtle` | `#F1F3F5` | — | Alternância em tabelas, sections |
| `--color-border-light` | `#DEE2E6` | `palette.divider` | Borders, dividers |
| `--color-border-default` | `#ADB5BD` | — | Borders de inputs |
| `--color-text-primary` | `#212529` | `palette.text.primary` | Texto principal (15.43:1 ✅) |
| `--color-text-secondary` | `#495057` | `palette.text.secondary` | Subtítulos, labels (8.18:1 ✅) |
| `--color-text-disabled` | `#6C757D` | `palette.text.disabled` | Placeholders, disabled (4.69:1 ✅) |
| `--color-action-hover` | `rgba(27,42,74,0.04)` | `palette.action.hover` | Hover state genérico |
| `--color-action-selected` | `rgba(27,42,74,0.08)` | `palette.action.selected` | Item selecionado |
| `--color-action-disabled-bg` | `#E9ECEF` | `palette.action.disabledBackground` | Botões disabled |

### 1.4 Cores Semânticas

| Variável CSS | Hex | Role MUI | Uso | Contraste sobre branco |
|---|---|---|---|---|
| `--color-success-main` | `#1B7A3D` | `palette.success.main` | Aprovações, confirmações | 5.39:1 ✅ |
| `--color-success-light` | `#D4EDDA` | `palette.success.light` | Background de chips/alerts | — |
| `--color-success-dark` | `#155724` | `palette.success.dark` | Texto sobre success.light | 6.99:1 ✅ |
| `--color-warning-main` | `#E8A623` | `palette.warning.main` | Pendências, atenção | Use sobre navy |
| `--color-warning-light` | `#FFF3CD` | `palette.warning.light` | Background de chips/alerts | — |
| `--color-warning-dark` | `#856404` | `palette.warning.dark` | Texto sobre warning.light | 4.96:1 ✅ |
| `--color-error-main` | `#C62828` | `palette.error.main` | Erros, rejeições, exclusões | 5.62:1 ✅ |
| `--color-error-light` | `#F8D7DA` | `palette.error.light` | Background de chips/alerts | — |
| `--color-error-dark` | `#721C24` | `palette.error.dark` | Texto sobre error.light | 8.25:1 ✅ |
| `--color-info-main` | `#1565C0` | `palette.info.main` | Links informativos, dicas | 5.75:1 ✅ |
| `--color-info-light` | `#D1ECF1` | `palette.info.light` | Background informativo | — |
| `--color-info-dark` | `#0D47A1` | `palette.info.dark` | Texto sobre info.light | — |

### 1.5 Data Visualization — Light Mode

Paleta de 8 cores otimizada para gráficos, derivada da identidade navy/gold. Use na ordem abaixo para séries de dados. Todas passam WCAG AA para texto grande (3:1+) sobre branco.

| # | Nome | Hex | Uso sugerido | Contraste sobre `#FFFFFF` |
|---|---|---|---|---|
| 1 | Navy | `#1B2A4A` | Série primária | 14.22:1 ✅ AA |
| 2 | Teal | `#1A7A7A` | Série secundária | 5.11:1 ✅ AA |
| 3 | Gold | `#C48A1A` | Destaque, accent | 3.00:1 ✅ AA large |
| 4 | Terracotta | `#A85232` | Categorias alternativas | 5.36:1 ✅ AA |
| 5 | Steel Blue | `#3A6EA5` | Variação de azul | 5.31:1 ✅ AA |
| 6 | Olive | `#5C7A3D` | Dados naturais/positivos | 4.88:1 ✅ AA |
| 7 | Plum | `#7A3D6E` | Dados categóricos | 7.72:1 ✅ AA |
| 8 | Slate | `#546E7A` | Dados neutros/inativos | 5.40:1 ✅ AA |

### 1.6 Data Visualization — Dark Mode

| # | Nome | Hex Light | Hex Dark | Contraste sobre `#0E1420` |
|---|---|---|---|---|
| 1 | Navy | `#1B2A4A` | `#7A9AD0` | 6.46:1 ✅ AA |
| 2 | Teal | `#1A7A7A` | `#4DB8B8` | 7.78:1 ✅ AA |
| 3 | Gold | `#C48A1A` | `#F0B942` | 10.29:1 ✅ AA |
| 4 | Terracotta | `#A85232` | `#D4845A` | 6.36:1 ✅ AA |
| 5 | Steel Blue | `#3A6EA5` | `#6FA3D4` | 6.90:1 ✅ AA |
| 6 | Olive | `#5C7A3D` | `#8AB566` | 7.79:1 ✅ AA |
| 7 | Plum | `#7A3D6E` | `#B86FA5` | 5.14:1 ✅ AA |
| 8 | Slate | `#546E7A` | `#90A4AE` | 7.11:1 ✅ AA |

> **Regra para gráficos:** máximo 5 séries por gráfico. Acima disso, use small multiples. Dados sequenciais: uma única matiz variando lightness. Dados divergentes: teal para positivo, terracotta/error para negativo. Sempre inclua labels diretos — nunca dependa só de cor.

---

## 2. Tipografia

### 2.1 Fontes

| Papel | Fonte | Fallback Stack | Justificativa |
|---|---|---|---|
| **Primária (headings + body)** | **Inter** | `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif` | Profissional, excelente legibilidade em tabelas numéricas, suporte a `tabular-nums`. Ampla variedade de pesos. Google Fonts. |
| **Secundária (headings display)** | **DM Sans** | `'DM Sans', 'Inter', sans-serif` | Geométrica, sóbria, complementa Inter para títulos. Ecoa a tipografia geométrica do logo da Construtora Dinâmica. Google Fonts. |
| **Monoespaçada (dados, código)** | **JetBrains Mono** | `'JetBrains Mono', 'Fira Code', 'Consolas', monospace` | Para valores numéricos tabulares, IDs, códigos TCPO. |

> **Google Fonts import:**  
> `@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=DM+Sans:wght@500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');`

### 2.2 Escala Tipográfica Completa

Todas as medidas em pixels, otimizadas para uma aplicação corporativa densa em dados.

| Variante MUI | Fonte | Tamanho (px) | Peso | Line-Height | Letter-Spacing | Uso |
|---|---|---|---|---|---|---|
| `h1` | DM Sans | 32 | 700 | 1.2 | -0.5px | Títulos de página (Dashboard, Orçamentos) |
| `h2` | DM Sans | 26 | 700 | 1.25 | -0.3px | Títulos de seção |
| `h3` | DM Sans | 22 | 600 | 1.3 | -0.2px | Subtítulos de seção |
| `h4` | Inter | 20 | 600 | 1.35 | -0.1px | Títulos de cards |
| `h5` | Inter | 18 | 600 | 1.4 | 0px | Subtítulos de cards |
| `h6` | Inter | 16 | 600 | 1.4 | 0.15px | Títulos menores, labels de grupo |
| `subtitle1` | Inter | 16 | 500 | 1.5 | 0.15px | Subtítulos, labels enfatizados |
| `subtitle2` | Inter | 14 | 500 | 1.5 | 0.1px | Subtítulos menores |
| `body1` | Inter | 15 | 400 | 1.6 | 0px | Texto padrão da aplicação |
| `body2` | Inter | 13 | 400 | 1.55 | 0.1px | Texto secundário, descrições |
| `caption` | Inter | 12 | 400 | 1.5 | 0.4px | Rodapés, timestamps, notas |
| `overline` | Inter | 11 | 600 | 1.5 | 1.5px (uppercase) | Labels de categorias, tags de seção |
| `button` | Inter | 14 | 600 | 1.15 | 0.4px (uppercase) | Texto de botões |

### 2.3 Regras de Uso

- **Números tabulares:** em tabelas de orçamento, composições e relatórios, usar `font-variant-numeric: tabular-nums lining-nums` para alinhamento perfeito de colunas
- **Caixa alta:** apenas em `overline`, `button`, e labels de seção. Nunca em body text
- **Peso máximo na UI:** 700 apenas para h1/h2. Evitar bold desnecessário
- **Tamanho mínimo:** 11px (overline). Nunca abaixo disso
- **Medida ideal:** 60-75 caracteres por linha para body text

---

## 3. Espaçamento e Layout

### 3.1 Spacing Unit

Base: **8px** (padrão MUI). Todos os espaçamentos são múltiplos de 8.

| Token | Valor | Uso |
|---|---|---|
| `spacing(0.5)` | 4px | Gaps mínimos, padding de chips |
| `spacing(1)` | 8px | Espaçamento entre ícone e texto |
| `spacing(1.5)` | 12px | Padding interno de inputs |
| `spacing(2)` | 16px | Padding de cards, gap entre itens de lista |
| `spacing(3)` | 24px | Margem entre seções, padding de containers |
| `spacing(4)` | 32px | Margem maior entre blocos |
| `spacing(5)` | 40px | Padding de modais e dialogs |
| `spacing(6)` | 48px | Margem entre seções de página |
| `spacing(8)` | 64px | Margem de topo de página |

### 3.2 Border Radius

| Token | Valor | Uso |
|---|---|---|
| `shape.borderRadius` | **8px** | Padrão global (cards, containers) |
| `--radius-sm` | 4px | Chips, badges, tags |
| `--radius-md` | 8px | Cards, inputs, selects |
| `--radius-lg` | 12px | Modais, dialogs, menus |
| `--radius-xl` | 16px | Cards de destaque, tooltips grandes |
| `--radius-full` | 9999px | Avatares, botões circulares |
| `--radius-button` | 6px | Botões (levemente mais compacto que cards) |

### 3.3 Sombras (Elevation)

5 níveis, derivados de um tom azul escuro para manter coerência com a paleta navy.

| Nível | Valor | Uso |
|---|---|---|
| **elevation-0** | `none` | Elementos flat, dentro de containers |
| **elevation-1** | `0px 1px 3px rgba(27,42,74,0.08), 0px 1px 2px rgba(27,42,74,0.06)` | Cards em repouso, surfaces |
| **elevation-2** | `0px 4px 6px rgba(27,42,74,0.08), 0px 2px 4px rgba(27,42,74,0.06)` | Cards hover, dropdowns |
| **elevation-3** | `0px 10px 20px rgba(27,42,74,0.10), 0px 4px 8px rgba(27,42,74,0.06)` | Modais, dialogs, popovers |
| **elevation-4** | `0px 20px 40px rgba(27,42,74,0.14), 0px 8px 16px rgba(27,42,74,0.08)` | Overlays, menus flutuantes |

### 3.4 Breakpoints

| Nome | Valor | Uso |
|---|---|---|
| `xs` | 0px | Mobile (raro para este sistema) |
| `sm` | 600px | Tablet portrait |
| `md` | 900px | Tablet landscape |
| `lg` | 1200px | Desktop padrão |
| `xl` | 1536px | Desktop wide |
| `xxl` | 1920px | Monitores ultrawide (custom) |

### 3.5 Container / Layout Widths

| Elemento | Width | Observação |
|---|---|---|
| **Sidebar (Drawer)** | 260px (expandida), 72px (colapsada) | Fixo à esquerda |
| **Main content** | `100% - sidebar` | Fluido |
| **Container máximo** | 1440px | Para conteúdo centralizado |
| **Tabelas** | 100% do container | Com scroll horizontal |
| **Modais sm** | 440px | Confirmações, alertas |
| **Modais md** | 600px | Formulários simples |
| **Modais lg** | 900px | Formulários complexos, composições |
| **Modais xl** | 1200px | Tabelas, relatórios |

---

## 4. Componentes — Design Tokens

### 4.1 Buttons

#### Contained (Primary)

| Propriedade | Valor |
|---|---|
| Background | `#1B3A6B` (primary.main) |
| Color | `#FFFFFF` |
| Border Radius | 6px |
| Padding | 8px 20px |
| Font | Inter 14px / 600 / uppercase / 0.4px spacing |
| Min Height | 40px |
| **Hover** | Background `#1B2A4A` (primary.dark) |
| **Active** | Background `#0E1525` |
| **Disabled** | Background `#E9ECEF`, Color `#ADB5BD` |
| **Focus** | Ring `0 0 0 3px rgba(27,58,107,0.3)` |

#### Contained (Secondary/Gold)

| Propriedade | Valor |
|---|---|
| Background | `#E8A623` (secondary.main) |
| Color | `#1B2A4A` (navy — contrastText) |
| **Hover** | Background `#C48A1A` |
| **Active** | Background `#8B6209` |

#### Outlined

| Propriedade | Valor |
|---|---|
| Background | transparent |
| Border | 1px solid `#1B3A6B` |
| Color | `#1B3A6B` |
| **Hover** | Background `rgba(27,58,107,0.04)`, Border `#1B2A4A` |
| **Disabled** | Border `#DEE2E6`, Color `#ADB5BD` |

#### Text Button

| Propriedade | Valor |
|---|---|
| Background | transparent |
| Color | `#1B3A6B` |
| Padding | 8px 12px |
| **Hover** | Background `rgba(27,58,107,0.04)` |

#### Danger Button (contained)

| Propriedade | Valor |
|---|---|
| Background | `#C62828` |
| Color | `#FFFFFF` |
| **Hover** | Background `#A11C1C` |

### 4.2 Cards

| Propriedade | Valor |
|---|---|
| Background | `#FFFFFF` (paper) |
| Border | 1px solid `#E9ECEF` |
| Border Radius | 8px |
| Padding | 24px |
| Shadow | elevation-1 em repouso |
| **Hover (clicável)** | elevation-2, border `#DEE2E6` |
| **Card Header** | Padding-bottom 16px, border-bottom `1px solid #E9ECEF` (quando necessário) |
| **KPI Cards** | Valor em DM Sans 28px/700, label em Inter 13px/400 `#495057` |

### 4.3 Inputs / TextFields

| Propriedade | Valor |
|---|---|
| Variante MUI | `outlined` (padrão) |
| Border | 1px solid `#ADB5BD` |
| Border Radius | 8px |
| Padding | 12px 14px |
| Font | Inter 15px/400 |
| Label Color | `#495057` (text.secondary) |
| Placeholder Color | `#6C757D` (text.disabled) |
| **Focus** | Border `#1B3A6B` (2px), Label `#1B3A6B`, Shadow `0 0 0 3px rgba(27,58,107,0.12)` |
| **Error** | Border `#C62828`, Label `#C62828`, Helper text `#C62828` |
| **Disabled** | Background `#F8F9FA`, Border `#DEE2E6`, Color `#ADB5BD` |
| **Filled (readonly)** | Background `#F1F3F5`, Border none |

### 4.4 Tables

| Propriedade | Valor |
|---|---|
| Header Background | `#1B2A4A` (primary.dark) |
| Header Text | `#FFFFFF`, Inter 13px/600/uppercase/0.5px spacing |
| Row Background | `#FFFFFF` alternando com `#F8F9FA` |
| Row Hover | `#EDF1F8` (primary-50) |
| Row Selected | `#DAE3F1` (primary-100) |
| Cell Padding | 12px 16px |
| Border | 1px solid `#E9ECEF` horizontal entre rows |
| Cell Font | Inter 14px/400, números em `tabular-nums` |
| Sorted Column Header | Com ícone de seta, text `#E8A623` (gold accent) |

> **Variante alternativa:** header `#F1F3F5` com texto `#1B2A4A` para tabelas dentro de cards que já têm bastante peso visual.

### 4.5 Chips / Badges por Status

Para workflows de homologação, composições e associações:

| Status | Background | Text Color | Border | Ícone |
|---|---|---|---|---|
| **Aprovado** | `#D4EDDA` | `#155724` | none | `CheckCircle` |
| **Pendente** | `#FFF3CD` | `#856404` | none | `Schedule` |
| **Rejeitado** | `#F8D7DA` | `#721C24` | none | `Cancel` |
| **Rascunho** | `#E9ECEF` | `#495057` | none | `Edit` |
| **Em Revisão** | `#D1ECF1` | `#0D47A1` | none | `RateReview` |
| **Ativo** | `#1B3A6B` | `#FFFFFF` | none | `CheckCircle` |
| **Inativo** | `#E9ECEF` | `#6C757D` | none | `Block` |

Todos os chips:
- Border Radius: 4px
- Font: Inter 12px/600/uppercase
- Padding: 4px 10px
- Height: 24px
- Todos passam WCAG AA (verificados)

### 4.6 Modais / Dialogs

| Propriedade | Valor |
|---|---|
| Overlay | `rgba(14,21,37,0.5)` (navy ultra-dark com 50% opacity) |
| Background | `#FFFFFF` |
| Border Radius | 12px |
| Padding | 32px (body), 24px (title area), 24px (actions area) |
| Max Width | sm: 440px, md: 600px, lg: 900px |
| Shadow | elevation-4 |
| Title | DM Sans 20px/600, `#212529` |
| Close Button | Ícone `Close` em `#6C757D`, hover `#212529` |
| Actions | Alinhados à direita, gap 12px, botão primário à direita |
| Divider | Linha `#E9ECEF` entre title e body, body e actions |

#### Dialog de Confirmação Destrutiva

| Propriedade | Valor |
|---|---|
| Ícone | `WarningAmber` em `#C62828`, 48px, centralizado |
| Botão Confirmar | Contained danger (`#C62828`) |
| Botão Cancelar | Outlined |

### 4.7 Sidebar / Navigation (Drawer)

| Propriedade | Valor |
|---|---|
| Background | `#1B2A4A` (navy primary) |
| Width | 260px (expandida), 72px (mini) |
| Logo Area | Padding 20px 24px, border-bottom `1px solid rgba(255,255,255,0.1)` |
| Nav Item Padding | 10px 20px |
| Nav Item Font | Inter 14px/500 |
| Nav Item Color | `rgba(255,255,255,0.7)` |
| **Hover** | Background `rgba(255,255,255,0.08)`, Color `#FFFFFF` |
| **Active** | Background `rgba(232,166,35,0.15)`, Color `#FFFFFF`, border-left 3px solid `#E8A623` |
| **Active Icon** | `#E8A623` (gold) |
| **Inactive Icon** | `rgba(255,255,255,0.5)` |
| Section Label | Inter 11px/600/uppercase, `rgba(255,255,255,0.4)`, padding-top 24px |
| Divider | `rgba(255,255,255,0.08)` |
| User Area (bottom) | Avatar + nome, border-top `rgba(255,255,255,0.1)` |

### 4.8 AppBar

| Propriedade | Valor |
|---|---|
| Background | `#FFFFFF` |
| Height | 64px |
| Border Bottom | 1px solid `#E9ECEF` |
| Shadow | none (flat) ou elevation-1 |
| Title | Inter 16px/600, `#212529` |
| Breadcrumbs | Inter 13px/400, `#6C757D`, separador `/`, último item `#212529` |
| Action Icons | `#495057`, hover `#1B3A6B` |
| Notification Badge | `#C62828` (error) com counter branco |

### 4.9 Alerts / Toasts (Snackbars)

| Tipo | Background | Border-Left | Icon Color | Text Color |
|---|---|---|---|---|
| **Success** | `#D4EDDA` | 4px solid `#1B7A3D` | `#1B7A3D` | `#155724` |
| **Warning** | `#FFF3CD` | 4px solid `#E8A623` | `#856404` | `#856404` |
| **Error** | `#F8D7DA` | 4px solid `#C62828` | `#C62828` | `#721C24` |
| **Info** | `#D1ECF1` | 4px solid `#1565C0` | `#1565C0` | `#0D47A1` |

Todos os alerts:
- Border Radius: 8px
- Padding: 14px 16px
- Font: Inter 14px/400
- Ícone: 20px, alinhado ao topo
- Close button: ícone `Close` 18px, `#6C757D`

---

## 5. Iconografia e Elementos Visuais

### 5.1 Biblioteca de Ícones

**Biblioteca principal:** MUI Icons — variante **Outlined**

- Estilo outlined transmite leveza e profissionalismo, evitando peso visual excessivo
- Tamanho padrão: 20px (small), 24px (medium/default), 32px (large)
- Cor padrão: herda `text.secondary` (`#495057`), ou `primary.main` quando interativo
- Ícones na sidebar: 24px, cor conforme estado (ativo: gold, inativo: branco 50%)

**Biblioteca secundária (opcional):** Phosphor Icons — variante `regular` (quando MUI Icons não tiver o ícone necessário)

### 5.2 Motif do Chevron/Seta

O chevron duplo da marca é o principal elemento decorativo e pode ser usado como motif na aplicação:

| Uso | Especificação |
|---|---|
| **Loading/Splash** | Chevron animado (pulse ou slide-in) centralizado, navy + gold |
| **Empty states** | Chevron outline em `#DEE2E6` como background decorativo sutil (20% opacity) |
| **Login page** | Chevron grande como background decorativo à direita, navy escuro sobre navy |
| **Watermark em relatórios** | Chevron outline em 5% opacity sobre o conteúdo |
| **Separador visual** | Mini chevron `›` em gold como bullet alternativo em listas de features |
| **Background pattern** | Chevrons repetidos em grid diagonal, 3% opacity, para seções hero |

> **Nunca** distorcer, rotacionar mais de 15°, ou usar o chevron como ícone funcional (botão, link). Ele é sempre decorativo.

### 5.3 Logo na Aplicação

| Contexto | Versão | Tamanho |
|---|---|---|
| **Sidebar expandida** | Logo completo (ícone + "CONSTRUTORA DINÂMICA") horizontal, em branco | Altura 32px |
| **Sidebar colapsada** | Apenas ícone chevron (navy + gold) | 36px × 36px |
| **Login page** | Logo completo centralizado, versão colorida (navy + gold) | Altura 48px |
| **Favicon** | Ícone chevron simplificado | 32×32, 16×16 |
| **Relatórios/PDF** | Logo completo, versão colorida | Altura 28px |

**Subtítulo do produto:** Abaixo do logo principal, adicionar "Budget" em Inter 14px/300 com letter-spacing 4px, uppercase, `#8AA4D0` (na sidebar escura) ou `#3A5490` (em fundo claro).

**Clear space:** Manter ao redor do logo uma margem mínima equivalente à altura do "D" de DINÂMICA.

### 5.4 Empty States

| Elemento | Especificação |
|---|---|
| **Ilustração** | Ícone MUI Outlined relevante em 64px, `#ADB5BD`, sobre fundo circular `#F1F3F5` de 120px |
| **Chevron decorativo** | Atrás do ícone, chevron outline em `#E9ECEF`, 160px, rotação -15° |
| **Título** | DM Sans 18px/600, `#212529` — ex: "Nenhum orçamento encontrado" |
| **Descrição** | Inter 14px/400, `#6C757D`, max-width 360px, centralizado |
| **CTA** | Botão contained primary — ex: "Criar primeiro orçamento" |

---

## 6. Dark Mode

### 6.1 Paleta Dark Mode

Derivada das cores da marca. O navy escuro evolui para tons mais profundos; o dourado fica levemente mais claro para manter contraste.

| Role | Variável | Hex Light | Hex Dark | Observação |
|---|---|---|---|---|
| Background default | `--color-bg-default` | `#F8F9FA` | `#0E1420` | Base ultra-dark com tom navy |
| Background paper | `--color-bg-paper` | `#FFFFFF` | `#152032` | Cards, surfaces |
| Surface alt | — | `#F1F3F5` | `#1B2A44` | Áreas de destaque, alternância |
| Border/Divider | `--color-border` | `#DEE2E6` | `#2A3A56` | Borders sutis |
| Border input | — | `#ADB5BD` | `#3D5070` | Borders de inputs |
| Text primary | `--color-text-primary` | `#212529` | `#E1E5EB` | 14.57:1 ✅ |
| Text secondary | `--color-text-secondary` | `#495057` | `#8A95A8` | 6.09:1 ✅ |
| Text disabled | `--color-text-disabled` | `#6C757D` | `#5A6578` | 3.14:1 (AA large ✅) |
| Primary main | `--color-primary` | `#1B3A6B` | `#5A8AD0` | Botões, links |
| Primary dark | — | `#1B2A4A` | `#1B3A6B` | Hover |
| Primary light | — | `#5A7AB5` | `#8AB0E8` | Tints |
| Secondary main | — | `#E8A623` | `#F0B942` | Gold accent (10.29:1 ✅) |
| Secondary dark | — | `#8B6209` | `#E8A623` | — |
| Action hover | — | `rgba(27,42,74,0.04)` | `rgba(255,255,255,0.05)` | — |
| Action selected | — | `rgba(27,42,74,0.08)` | `rgba(255,255,255,0.10)` | — |

### 6.2 Semânticas — Dark Mode

| Role | Hex Light | Hex Dark |
|---|---|---|
| Success main | `#1B7A3D` | `#4CAF6E` |
| Success light (bg) | `#D4EDDA` | `rgba(76,175,110,0.12)` |
| Warning main | `#E8A623` | `#F0B942` |
| Warning light (bg) | `#FFF3CD` | `rgba(240,185,66,0.12)` |
| Error main | `#C62828` | `#EF5350` |
| Error light (bg) | `#F8D7DA` | `rgba(239,83,80,0.12)` |
| Info main | `#1565C0` | `#5C9CE6` |
| Info light (bg) | `#D1ECF1` | `rgba(92,156,230,0.12)` |

### 6.3 Sidebar — Dark Mode

A sidebar já é navy escuro em light mode. Em dark mode, fica ainda mais integrada:

| Propriedade | Light Mode | Dark Mode |
|---|---|---|
| Background | `#1B2A4A` | `#0A101A` (mais escuro que o bg) |
| Border right | none | `1px solid #1A2640` |
| Active item bg | `rgba(232,166,35,0.15)` | `rgba(240,185,66,0.15)` |
| Active border | `#E8A623` | `#F0B942` |

### 6.4 Chips/Badges — Dark Mode

| Status | Background (Dark) | Text (Dark) |
|---|---|---|
| Aprovado | `rgba(76,175,110,0.15)` | `#4CAF6E` |
| Pendente | `rgba(240,185,66,0.15)` | `#F0B942` |
| Rejeitado | `rgba(239,83,80,0.15)` | `#EF5350` |
| Rascunho | `rgba(255,255,255,0.08)` | `#8A95A8` |
| Em Revisão | `rgba(92,156,230,0.15)` | `#5C9CE6` |

---

## 7. Tema MUI Pronto

```typescript
// theme.ts — Dinâmica Budget MUI 7 Theme
// Instale: @mui/material @emotion/react @emotion/styled

import { createTheme, type ThemeOptions, type PaletteMode } from '@mui/material/styles';

// ─── Color Tokens ──────────────────────────────────────────────
const tokens = {
  primary: {
    900: '#0E1525',
    800: '#1B2A4A',
    700: '#243660',
    600: '#2D4276',
    main: '#1B3A6B',
    400: '#3A5490',
    300: '#5A7AB5',
    200: '#8AA4D0',
    100: '#B5C7E3',
    50: '#EDF1F8',
  },
  secondary: {
    dark: '#8B6209',
    main: '#E8A623',
    light: '#F0C05C',
    50: '#FDF3DD',
  },
  neutral: {
    50: '#F8F9FA',
    100: '#F1F3F5',
    200: '#E9ECEF',
    300: '#DEE2E6',
    400: '#ADB5BD',
    500: '#6C757D',
    600: '#495057',
    700: '#343A40',
    800: '#212529',
    900: '#121518',
  },
  success: { main: '#1B7A3D', light: '#D4EDDA', dark: '#155724' },
  warning: { main: '#E8A623', light: '#FFF3CD', dark: '#856404' },
  error: { main: '#C62828', light: '#F8D7DA', dark: '#721C24' },
  info: { main: '#1565C0', light: '#D1ECF1', dark: '#0D47A1' },
} as const;

const darkTokens = {
  bg: { default: '#0E1420', paper: '#152032', alt: '#1B2A44' },
  border: { default: '#2A3A56', input: '#3D5070' },
  text: { primary: '#E1E5EB', secondary: '#8A95A8', disabled: '#5A6578' },
  primary: { main: '#5A8AD0', dark: '#1B3A6B', light: '#8AB0E8' },
  secondary: { main: '#F0B942', dark: '#E8A623' },
  success: { main: '#4CAF6E', light: 'rgba(76,175,110,0.12)' },
  warning: { main: '#F0B942', light: 'rgba(240,185,66,0.12)' },
  error: { main: '#EF5350', light: 'rgba(239,83,80,0.12)' },
  info: { main: '#5C9CE6', light: 'rgba(92,156,230,0.12)' },
} as const;

// ─── Custom Shadows ────────────────────────────────────────────
const customShadows = [
  'none', // 0
  '0px 1px 3px rgba(27,42,74,0.08), 0px 1px 2px rgba(27,42,74,0.06)', // 1
  '0px 2px 4px rgba(27,42,74,0.08), 0px 1px 3px rgba(27,42,74,0.06)', // 2
  '0px 4px 6px rgba(27,42,74,0.08), 0px 2px 4px rgba(27,42,74,0.06)', // 3
  '0px 6px 10px rgba(27,42,74,0.08), 0px 3px 6px rgba(27,42,74,0.06)', // 4
  '0px 8px 16px rgba(27,42,74,0.08), 0px 4px 8px rgba(27,42,74,0.06)', // 5
  '0px 10px 20px rgba(27,42,74,0.10), 0px 4px 8px rgba(27,42,74,0.06)', // 6
  '0px 12px 24px rgba(27,42,74,0.10), 0px 5px 10px rgba(27,42,74,0.06)', // 7
  '0px 14px 28px rgba(27,42,74,0.10), 0px 6px 12px rgba(27,42,74,0.06)', // 8
  '0px 16px 32px rgba(27,42,74,0.12), 0px 6px 14px rgba(27,42,74,0.06)', // 9
  '0px 18px 36px rgba(27,42,74,0.12), 0px 7px 16px rgba(27,42,74,0.06)', // 10
  '0px 20px 40px rgba(27,42,74,0.12), 0px 8px 16px rgba(27,42,74,0.06)', // 11
  '0px 20px 40px rgba(27,42,74,0.14), 0px 8px 16px rgba(27,42,74,0.08)', // 12
  ...Array(12).fill('0px 20px 40px rgba(27,42,74,0.14), 0px 8px 16px rgba(27,42,74,0.08)'), // 13-24
] as unknown as ThemeOptions['shadows'];

// ─── Typography ────────────────────────────────────────────────
const fontFamily = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
const fontFamilyDisplay = "'DM Sans', 'Inter', sans-serif";
const fontFamilyMono = "'JetBrains Mono', 'Fira Code', Consolas, monospace";

const typography: ThemeOptions['typography'] = {
  fontFamily,
  h1: { fontFamily: fontFamilyDisplay, fontSize: '2rem', fontWeight: 700, lineHeight: 1.2, letterSpacing: '-0.5px' }, // 32px
  h2: { fontFamily: fontFamilyDisplay, fontSize: '1.625rem', fontWeight: 700, lineHeight: 1.25, letterSpacing: '-0.3px' }, // 26px
  h3: { fontFamily: fontFamilyDisplay, fontSize: '1.375rem', fontWeight: 600, lineHeight: 1.3, letterSpacing: '-0.2px' }, // 22px
  h4: { fontFamily, fontSize: '1.25rem', fontWeight: 600, lineHeight: 1.35, letterSpacing: '-0.1px' }, // 20px
  h5: { fontFamily, fontSize: '1.125rem', fontWeight: 600, lineHeight: 1.4, letterSpacing: '0px' }, // 18px
  h6: { fontFamily, fontSize: '1rem', fontWeight: 600, lineHeight: 1.4, letterSpacing: '0.15px' }, // 16px
  subtitle1: { fontFamily, fontSize: '1rem', fontWeight: 500, lineHeight: 1.5, letterSpacing: '0.15px' },
  subtitle2: { fontFamily, fontSize: '0.875rem', fontWeight: 500, lineHeight: 1.5, letterSpacing: '0.1px' },
  body1: { fontFamily, fontSize: '0.9375rem', fontWeight: 400, lineHeight: 1.6, letterSpacing: '0px' }, // 15px
  body2: { fontFamily, fontSize: '0.8125rem', fontWeight: 400, lineHeight: 1.55, letterSpacing: '0.1px' }, // 13px
  caption: { fontFamily, fontSize: '0.75rem', fontWeight: 400, lineHeight: 1.5, letterSpacing: '0.4px' }, // 12px
  overline: { fontFamily, fontSize: '0.6875rem', fontWeight: 600, lineHeight: 1.5, letterSpacing: '1.5px', textTransform: 'uppercase' }, // 11px
  button: { fontFamily, fontSize: '0.875rem', fontWeight: 600, lineHeight: 1.15, letterSpacing: '0.4px', textTransform: 'uppercase' },
};

// ─── Shared Component Overrides ────────────────────────────────
const getComponentOverrides = (mode: PaletteMode): ThemeOptions['components'] => ({
  MuiCssBaseline: {
    styleOverrides: {
      body: {
        fontVariantNumeric: 'tabular-nums lining-nums',
      },
    },
  },

  MuiButton: {
    defaultProps: {
      disableElevation: true,
    },
    styleOverrides: {
      root: {
        borderRadius: 6,
        padding: '8px 20px',
        minHeight: 40,
        fontWeight: 600,
        fontSize: '0.875rem',
        letterSpacing: '0.4px',
        textTransform: 'uppercase' as const,
        transition: 'all 150ms ease-in-out',
      },
      containedPrimary: {
        '&:hover': {
          backgroundColor: mode === 'light' ? tokens.primary[800] : darkTokens.primary.dark,
        },
      },
      containedSecondary: {
        color: tokens.primary[800],
        '&:hover': {
          backgroundColor: '#C48A1A',
        },
      },
      outlined: {
        borderWidth: 1,
        '&:hover': {
          borderWidth: 1,
        },
      },
      sizeSmall: {
        padding: '6px 14px',
        fontSize: '0.8125rem',
        minHeight: 34,
      },
      sizeLarge: {
        padding: '10px 28px',
        fontSize: '0.9375rem',
        minHeight: 48,
      },
    },
  },

  MuiCard: {
    defaultProps: {
      elevation: 0,
    },
    styleOverrides: {
      root: {
        borderRadius: 8,
        border: `1px solid ${mode === 'light' ? tokens.neutral[200] : darkTokens.border.default}`,
        boxShadow: customShadows?.[1] as string,
        transition: 'box-shadow 150ms ease-in-out, border-color 150ms ease-in-out',
      },
    },
  },

  MuiCardContent: {
    styleOverrides: {
      root: {
        padding: 24,
        '&:last-child': { paddingBottom: 24 },
      },
    },
  },

  MuiTextField: {
    defaultProps: {
      variant: 'outlined',
      size: 'medium',
    },
  },

  MuiOutlinedInput: {
    styleOverrides: {
      root: {
        borderRadius: 8,
        '&:hover .MuiOutlinedInput-notchedOutline': {
          borderColor: mode === 'light' ? tokens.neutral[500] : darkTokens.border.input,
        },
        '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
          borderWidth: 2,
          borderColor: mode === 'light' ? tokens.primary.main : darkTokens.primary.main,
        },
        '&.Mui-error .MuiOutlinedInput-notchedOutline': {
          borderColor: mode === 'light' ? tokens.error.main : darkTokens.error.main,
        },
      },
      notchedOutline: {
        borderColor: mode === 'light' ? tokens.neutral[400] : darkTokens.border.input,
      },
      input: {
        padding: '12px 14px',
      },
    },
  },

  MuiInputLabel: {
    styleOverrides: {
      root: {
        fontSize: '0.9375rem',
        '&.Mui-focused': {
          color: mode === 'light' ? tokens.primary.main : darkTokens.primary.main,
        },
      },
    },
  },

  MuiChip: {
    styleOverrides: {
      root: {
        borderRadius: 4,
        fontWeight: 600,
        fontSize: '0.75rem',
        letterSpacing: '0.5px',
        textTransform: 'uppercase' as const,
        height: 24,
      },
      sizeSmall: {
        height: 20,
        fontSize: '0.6875rem',
      },
    },
  },

  MuiAppBar: {
    defaultProps: {
      elevation: 0,
      color: 'default',
    },
    styleOverrides: {
      root: {
        backgroundColor: mode === 'light' ? '#FFFFFF' : darkTokens.bg.paper,
        borderBottom: `1px solid ${mode === 'light' ? tokens.neutral[200] : darkTokens.border.default}`,
        color: mode === 'light' ? tokens.neutral[800] : darkTokens.text.primary,
      },
    },
  },

  MuiDrawer: {
    styleOverrides: {
      paper: {
        backgroundColor: mode === 'light' ? tokens.primary[800] : '#0A101A',
        color: '#FFFFFF',
        borderRight: mode === 'dark' ? `1px solid #1A2640` : 'none',
        width: 260,
      },
    },
  },

  MuiDialog: {
    styleOverrides: {
      paper: {
        borderRadius: 12,
        boxShadow: customShadows?.[12] as string,
      },
    },
  },

  MuiDialogTitle: {
    styleOverrides: {
      root: {
        fontFamily: fontFamilyDisplay,
        fontSize: '1.25rem',
        fontWeight: 600,
        padding: '24px 32px 16px',
      },
    },
  },

  MuiDialogContent: {
    styleOverrides: {
      root: {
        padding: '16px 32px',
      },
    },
  },

  MuiDialogActions: {
    styleOverrides: {
      root: {
        padding: '16px 32px 24px',
        gap: 12,
      },
    },
  },

  MuiTableHead: {
    styleOverrides: {
      root: {
        '& .MuiTableCell-head': {
          backgroundColor: mode === 'light' ? tokens.primary[800] : darkTokens.bg.alt,
          color: mode === 'light' ? '#FFFFFF' : darkTokens.text.primary,
          fontWeight: 600,
          fontSize: '0.8125rem',
          letterSpacing: '0.5px',
          textTransform: 'uppercase' as const,
          padding: '12px 16px',
          borderBottom: 'none',
          whiteSpace: 'nowrap' as const,
        },
      },
    },
  },

  MuiTableBody: {
    styleOverrides: {
      root: {
        '& .MuiTableRow-root': {
          '&:nth-of-type(even)': {
            backgroundColor: mode === 'light' ? tokens.neutral[50] : 'rgba(255,255,255,0.02)',
          },
          '&:hover': {
            backgroundColor: mode === 'light' ? tokens.primary[50] : 'rgba(255,255,255,0.05)',
          },
          transition: 'background-color 100ms ease',
        },
        '& .MuiTableCell-body': {
          padding: '12px 16px',
          fontSize: '0.875rem',
          borderColor: mode === 'light' ? tokens.neutral[200] : darkTokens.border.default,
          fontVariantNumeric: 'tabular-nums lining-nums',
        },
      },
    },
  },

  MuiTableCell: {
    styleOverrides: {
      root: {
        borderColor: mode === 'light' ? tokens.neutral[200] : darkTokens.border.default,
      },
    },
  },

  MuiAlert: {
    styleOverrides: {
      root: {
        borderRadius: 8,
        padding: '14px 16px',
        fontSize: '0.875rem',
        alignItems: 'center',
      },
      standardSuccess: {
        backgroundColor: mode === 'light' ? tokens.success.light : darkTokens.success.light,
        color: mode === 'light' ? tokens.success.dark : darkTokens.success.main,
        borderLeft: `4px solid ${mode === 'light' ? tokens.success.main : darkTokens.success.main}`,
        '& .MuiAlert-icon': {
          color: mode === 'light' ? tokens.success.main : darkTokens.success.main,
        },
      },
      standardWarning: {
        backgroundColor: mode === 'light' ? tokens.warning.light : darkTokens.warning.light,
        color: mode === 'light' ? tokens.warning.dark : darkTokens.warning.main,
        borderLeft: `4px solid ${mode === 'light' ? tokens.warning.main : darkTokens.warning.main}`,
        '& .MuiAlert-icon': {
          color: mode === 'light' ? tokens.warning.main : darkTokens.warning.main,
        },
      },
      standardError: {
        backgroundColor: mode === 'light' ? tokens.error.light : darkTokens.error.light,
        color: mode === 'light' ? tokens.error.dark : darkTokens.error.main,
        borderLeft: `4px solid ${mode === 'light' ? tokens.error.main : darkTokens.error.main}`,
        '& .MuiAlert-icon': {
          color: mode === 'light' ? tokens.error.main : darkTokens.error.main,
        },
      },
      standardInfo: {
        backgroundColor: mode === 'light' ? tokens.info.light : darkTokens.info.light,
        color: mode === 'light' ? tokens.info.dark : darkTokens.info.main,
        borderLeft: `4px solid ${mode === 'light' ? tokens.info.main : darkTokens.info.main}`,
        '& .MuiAlert-icon': {
          color: mode === 'light' ? tokens.info.main : darkTokens.info.main,
        },
      },
    },
  },

  MuiTooltip: {
    styleOverrides: {
      tooltip: {
        backgroundColor: tokens.primary[800],
        color: '#FFFFFF',
        fontSize: '0.75rem',
        fontWeight: 500,
        borderRadius: 6,
        padding: '6px 12px',
      },
      arrow: {
        color: tokens.primary[800],
      },
    },
  },

  MuiTab: {
    styleOverrides: {
      root: {
        fontWeight: 600,
        fontSize: '0.875rem',
        letterSpacing: '0.3px',
        textTransform: 'uppercase' as const,
        minHeight: 48,
        '&.Mui-selected': {
          color: mode === 'light' ? tokens.primary.main : darkTokens.primary.main,
        },
      },
    },
  },

  MuiTabs: {
    styleOverrides: {
      indicator: {
        height: 3,
        borderRadius: '3px 3px 0 0',
        backgroundColor: mode === 'light' ? tokens.primary.main : darkTokens.primary.main,
      },
    },
  },

  MuiBadge: {
    styleOverrides: {
      colorError: {
        backgroundColor: tokens.error.main,
        color: '#FFFFFF',
        fontWeight: 600,
        fontSize: '0.6875rem',
      },
    },
  },

  MuiListItemButton: {
    styleOverrides: {
      root: {
        borderRadius: 6,
        margin: '2px 8px',
        padding: '10px 12px',
        '&.Mui-selected': {
          backgroundColor: mode === 'light'
            ? 'rgba(232,166,35,0.15)'
            : 'rgba(240,185,66,0.15)',
          borderLeft: `3px solid ${mode === 'light' ? tokens.secondary.main : darkTokens.secondary.main}`,
          '&:hover': {
            backgroundColor: mode === 'light'
              ? 'rgba(232,166,35,0.22)'
              : 'rgba(240,185,66,0.22)',
          },
        },
        '&:hover': {
          backgroundColor: 'rgba(255,255,255,0.08)',
        },
      },
    },
  },

  MuiLinearProgress: {
    styleOverrides: {
      root: {
        borderRadius: 4,
        height: 6,
        backgroundColor: mode === 'light' ? tokens.neutral[200] : darkTokens.border.default,
      },
    },
  },

  MuiSkeleton: {
    styleOverrides: {
      root: {
        borderRadius: 6,
      },
    },
  },

  MuiBreadcrumbs: {
    styleOverrides: {
      root: {
        fontSize: '0.8125rem',
      },
      separator: {
        color: mode === 'light' ? tokens.neutral[400] : darkTokens.text.disabled,
      },
    },
  },

  MuiPaper: {
    styleOverrides: {
      root: {
        backgroundImage: 'none', // Remove MUI default gradient overlay in dark mode
      },
    },
  },

  MuiSwitch: {
    styleOverrides: {
      switchBase: {
        '&.Mui-checked': {
          color: mode === 'light' ? tokens.primary.main : darkTokens.primary.main,
          '& + .MuiSwitch-track': {
            backgroundColor: mode === 'light' ? tokens.primary[300] : darkTokens.primary.main,
            opacity: 0.6,
          },
        },
      },
    },
  },

  MuiDivider: {
    styleOverrides: {
      root: {
        borderColor: mode === 'light' ? tokens.neutral[200] : darkTokens.border.default,
      },
    },
  },
});

// ─── Theme Factory ─────────────────────────────────────────────
export const createDinamicaTheme = (mode: PaletteMode = 'light') => {
  const isLight = mode === 'light';

  return createTheme({
    palette: {
      mode,
      primary: {
        main: isLight ? tokens.primary.main : darkTokens.primary.main,
        dark: isLight ? tokens.primary[800] : darkTokens.primary.dark,
        light: isLight ? tokens.primary[300] : darkTokens.primary.light,
        contrastText: '#FFFFFF',
      },
      secondary: {
        main: isLight ? tokens.secondary.main : darkTokens.secondary.main,
        dark: isLight ? tokens.secondary.dark : darkTokens.secondary.dark,
        light: tokens.secondary.light,
        contrastText: tokens.primary[800],
      },
      success: {
        main: isLight ? tokens.success.main : darkTokens.success.main,
        light: isLight ? tokens.success.light : darkTokens.success.light,
        dark: tokens.success.dark,
        contrastText: '#FFFFFF',
      },
      warning: {
        main: isLight ? tokens.warning.main : darkTokens.warning.main,
        light: isLight ? tokens.warning.light : darkTokens.warning.light,
        dark: tokens.warning.dark,
        contrastText: tokens.primary[800],
      },
      error: {
        main: isLight ? tokens.error.main : darkTokens.error.main,
        light: isLight ? tokens.error.light : darkTokens.error.light,
        dark: tokens.error.dark,
        contrastText: '#FFFFFF',
      },
      info: {
        main: isLight ? tokens.info.main : darkTokens.info.main,
        light: isLight ? tokens.info.light : darkTokens.info.light,
        dark: tokens.info.dark,
        contrastText: '#FFFFFF',
      },
      background: {
        default: isLight ? tokens.neutral[50] : darkTokens.bg.default,
        paper: isLight ? '#FFFFFF' : darkTokens.bg.paper,
      },
      text: {
        primary: isLight ? tokens.neutral[800] : darkTokens.text.primary,
        secondary: isLight ? tokens.neutral[600] : darkTokens.text.secondary,
        disabled: isLight ? tokens.neutral[500] : darkTokens.text.disabled,
      },
      divider: isLight ? tokens.neutral[300] : darkTokens.border.default,
      action: {
        hover: isLight ? 'rgba(27,42,74,0.04)' : 'rgba(255,255,255,0.05)',
        selected: isLight ? 'rgba(27,42,74,0.08)' : 'rgba(255,255,255,0.10)',
        disabled: isLight ? tokens.neutral[400] : darkTokens.text.disabled,
        disabledBackground: isLight ? tokens.neutral[200] : 'rgba(255,255,255,0.08)',
      },
    },
    typography,
    shape: {
      borderRadius: 8,
    },
    shadows: customShadows,
    spacing: 8,
    breakpoints: {
      values: {
        xs: 0,
        sm: 600,
        md: 900,
        lg: 1200,
        xl: 1536,
      },
    },
    components: getComponentOverrides(mode),
  });
};

// ─── Export default themes ─────────────────────────────────────
export const lightTheme = createDinamicaTheme('light');
export const darkTheme = createDinamicaTheme('dark');

// ─── Data Visualization Palette ────────────────────────────────
export const chartColors = {
  light: ['#1B2A4A', '#1A7A7A', '#C48A1A', '#A85232', '#3A6EA5', '#5C7A3D', '#7A3D6E', '#546E7A'],
  dark: ['#7A9AD0', '#4DB8B8', '#F0B942', '#D4845A', '#6FA3D4', '#8AB566', '#B86FA5', '#90A4AE'],
};

// ─── Status Chip Color Map (Helper) ───────────────────────────
export const statusColors = {
  light: {
    aprovado: { bg: '#D4EDDA', color: '#155724' },
    pendente: { bg: '#FFF3CD', color: '#856404' },
    rejeitado: { bg: '#F8D7DA', color: '#721C24' },
    rascunho: { bg: '#E9ECEF', color: '#495057' },
    'em-revisao': { bg: '#D1ECF1', color: '#0D47A1' },
    ativo: { bg: '#1B3A6B', color: '#FFFFFF' },
    inativo: { bg: '#E9ECEF', color: '#6C757D' },
  },
  dark: {
    aprovado: { bg: 'rgba(76,175,110,0.15)', color: '#4CAF6E' },
    pendente: { bg: 'rgba(240,185,66,0.15)', color: '#F0B942' },
    rejeitado: { bg: 'rgba(239,83,80,0.15)', color: '#EF5350' },
    rascunho: { bg: 'rgba(255,255,255,0.08)', color: '#8A95A8' },
    'em-revisao': { bg: 'rgba(92,156,230,0.15)', color: '#5C9CE6' },
    ativo: { bg: 'rgba(90,138,208,0.2)', color: '#5A8AD0' },
    inativo: { bg: 'rgba(255,255,255,0.05)', color: '#5A6578' },
  },
} as const;

// ─── Font Family Exports (for non-MUI usage) ──────────────────
export const fonts = {
  primary: fontFamily,
  display: fontFamilyDisplay,
  mono: fontFamilyMono,
};

// ─── Token Exports (for CSS-in-JS or CSS vars) ────────────────
export { tokens, darkTokens };
```

### 7.1 Uso no App

```typescript
// App.tsx
import { ThemeProvider, CssBaseline } from '@mui/material';
import { useMemo, useState, createContext, useContext } from 'react';
import { createDinamicaTheme } from './theme';

type ColorMode = 'light' | 'dark';

interface ColorModeContextType {
  mode: ColorMode;
  toggleColorMode: () => void;
}

export const ColorModeContext = createContext<ColorModeContextType>({
  mode: 'light',
  toggleColorMode: () => {},
});

export const useColorMode = () => useContext(ColorModeContext);

function App() {
  const [mode, setMode] = useState<ColorMode>(() => {
    return (localStorage.getItem('theme-mode') as ColorMode) || 'light';
  });

  const theme = useMemo(() => createDinamicaTheme(mode), [mode]);

  const colorMode: ColorModeContextType = useMemo(
    () => ({
      mode,
      toggleColorMode: () => {
        setMode((prev) => {
          const next = prev === 'light' ? 'dark' : 'light';
          localStorage.setItem('theme-mode', next);
          return next;
        });
      },
    }),
    [mode],
  );

  return (
    <ColorModeContext.Provider value={colorMode}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {/* ...app routes */}
      </ThemeProvider>
    </ColorModeContext.Provider>
  );
}
```

### 7.2 Google Fonts — HTML Head

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=DM+Sans:wght@500;600;700&family=JetBrains+Mono:wght@400;500&display=swap"
  rel="stylesheet"
/>
```

---

## Apêndice: Resumo de Tokens Rápidos

```
┌─────────────────────────────────────────────────────────────┐
│  DINÂMICA BUDGET — Quick Reference                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PRIMARY       #1B3A6B (main)  #1B2A4A (dark)             │
│  SECONDARY     #E8A623 (gold)  #8B6209 (text-safe)        │
│  SUCCESS       #1B7A3D         ERROR    #C62828            │
│  WARNING       #E8A623         INFO     #1565C0            │
│                                                             │
│  BG DEFAULT    #F8F9FA         PAPER    #FFFFFF            │
│  TEXT PRIMARY  #212529         SECONDARY #495057           │
│  BORDER        #DEE2E6         INPUT    #ADB5BD            │
│                                                             │
│  FONT PRIMARY  Inter                                        │
│  FONT DISPLAY  DM Sans                                      │
│  FONT MONO     JetBrains Mono                               │
│                                                             │
│  RADIUS        8px (default)   6px (buttons)               │
│  SPACING       8px base                                     │
│                                                             │
│  SIDEBAR       260px / 72px    BG: #1B2A4A                 │
│  APPBAR        64px height     BG: #FFFFFF (flat)          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

*Brand Guide v1.0 — Dinâmica Budget — Construtora Dinâmica (Dinâmica Engenharia)*  
*Gerado em 26 de março de 2026*  
*Stack: React 19 + MUI 7 + Emotion + TypeScript*
