# Decision log — Phase B evaluation framework

Decisões metodológicas centralizadas. Cada linha aponta para a task que tomou a decisão e justifica brevemente.

## Glossário

| Decisão | Task | Justificativa | Referência |
|---|---|---|---|
| Atlas tem 18 termos novos vs 95 do antigo | T12 | 10 categorias BI-RADS oficiais (0–6 + 4A/B/C); 5 associated_features (retração cutânea/mamilar, espessamento, linfadenopatia); 1 morfologia "grosera heterogênea"; 1 mass_shape "oval" CBR. Glossário antigo cobria pouco essas dimensões | ACR BI-RADS Atlas 5th ed |
| `oval` como pt_canonical, `ovalado/a` em variants_acceptable | T12 (Ajuste 5) | CBR/SBM oficial usa `oval`. Tradutor recebeu glossário antigo com `ovalado/a` — não punir retroativamente | (Ajuste 5 cenário T12) |
| Retrocompatibilidade verificada por gate `verify_atlas_backward_compat.py` | T12 Step 4 | Exit 0 antes de commit T12. Status: gate manual, não pre-commit hook automatizado | (gate manual) |
| 25 adjetivos com `forms_pt`/`forms_es` (T18 prereq) | T12 Step 3.7 | Cobre M-SING/F-SING/M-PLUR/F-PLUR. 22/25 com >=1 ocorrência no corpus | (verificação empírica 2026-04-29) |
| 3 adjetivos com 0 ocorrências no corpus PT (lobulado, retraído, espessado) | T12 | T18 vota abstain (`n_compared=0`) nesses casos. Categoria expressa via substantivos próximos (retração, espessamento) que têm entries próprias | (verificação empírica 2026-04-29) |

## Auditor C1 (T12.5 — derivação programática)

| Decisão | Task | Justificativa | Referência |
|---|---|---|---|
| **Categorias do Atlas que entram em C1** | T12.5 | C1 audita "descritores BI-RADS". Categorias do Atlas mapeadas: `mass_shape`, `mass_margin`, `mass_density`, `calcifications_morphology`, `calcifications_distribution`, `associated_features`. Excluídas: `breast_composition` (composição mamária — descritor estrutural, não BI-RADS finding), `anatomy` (âncoras — não modificadores), `findings_mass` (substantivos — separadamente em C5/C7), `categories_birads` (auditado em C2), `assessment_terms` (palavras de juízo — não descritores), `procedures` (procedimento — não descritor), `asymmetry_distortion` (substantivos — em C5/C7). 6 categorias × ~5 termos = ~30 termos canônicos no bloco C1. | (decisão T12.5) |
| **Política de variantes aceitáveis no C1** | T12.5 | C1 aceita **TODAS as variantes em `pt_variants_acceptable`** (canonical + ovalada + ovalado etc), não apenas `pt_canonical`. Listar separadas por `/` no prompt: `oval/ovalada/ovalado`. Revisor LLM deve marcar passou se a forma usada está em qualquer variante listada — independente de gênero/número. **Justificativa:** evita falso positivo retroativo (tradutor recebeu glossário antigo); + alinha com retrocompat de T12. T18 cobre concordância morfológica em outra dimensão. | (decisão T12.5 + Ajuste 5 cenário T12) |

## Métricas

| Decisão | Task | Justificativa | Referência |
|---|---|---|---|
| Cortar BLEU do par ES↔PT | T15 | n-gramas de palavra inflam erro em línguas próximas; flexão equivalente subestima | Freitag et al. 2022 (WMT22 Metrics) |
| Manter BLEU em F2 (back-translation) | T14.B | Comparação ES↔ES_bt é monolingual — caso de uso clássico de BLEU | (decisão de design) |
| chrF++ como métrica lexical principal | T15 | Apropriada para línguas próximas (chars partilhados) | Popović 2017 |
| BERTScore-F1 como headline semântico | T15 | Padrão atual em MT evaluation, embeddings contextuais XLM-Roberta | Zhang et al. 2020 |
| Threshold modifier 0.95 (piso 0.90) | T18 Step 6 | Calibração empírica via p5 das duplicatas T19 | (calibração interna) |
| n=250 BT amostral | T14.B | Suficiente para H6 estratificado (≥7 por categoria); custo $0.20 vs $3.05 full | (decisão pragmática) |
| Holm-Bonferroni para H1–H8 | T23 Step 3 | FWER controlado em α=0.05 com 8 hipóteses confirmatórias | Holm 1979 |
| Hipóteses exploratórias separadas (sem correção) | T23 Step 3 | Defesa anti-p-hacking: confirmatórias pré-declaradas; exploratórias surgem post-hoc com flag | (princípio metodológico) |

## Schema e arquitetura

| Decisão | Task | Justificativa | Referência |
|---|---|---|---|
| Schema `validation_results` v1 | T20 Step 0 | Schema unificado consumido por T21/T22/T23; 3 estados de "valor" (passed/null/in_sample) | (arquitetural) |
| `audit_final_status="review"` → `passed=True` | T20 build_audit | Evita dupla penalização (Q_audit já pega has_critical) | (decisão pré-registrada) |
| `clinical_pass` separado de `overall_passed` | T20 schema | Modifier-only failure não é erro clínico — vira warning | (decisão metodológica) |
| `duplicate_stability` nunca em `overall_passed` | T19 / T20 | Fonte de priorização (T22), não de aprovação | (decisão arquitetural) |
| BERTScore não decide erro clínico | T15 escopo | Métricas semânticas globais não captam troca local de token | (limitação de escopo) |

## Pré-registro e governança

| Decisão | Task | Justificativa | Referência |
|---|---|---|---|
| Tag pré-registro `composite-score-formula` | T20 Step 6 | Anti-p-hacking via timestamp git imutável | Nosek et al. 2018 |
| Tag pré-registro `mqm-protocol` | T22 Step 0 | Mesma estratégia anti-p-hacking | Nosek et al. 2018 |
| Override mecânico C2/C3/C4/C6 → severity=critical | T12.6 | LLM calibra severidade instavelmente; objetivo elimina viés | (decisão de design) |
| Cegamento físico em 2 arquivos (não sheet oculta) | T22 Step 3 (Cenário C) | Sheet oculta no Excel é trivial de revelar; arquivos separados elim risco técnico | (decisão metodológica) |
| Revisor MQM externo + termo de confidencialidade | T22 Step 0 | Independência metodológica; LGPD compliance | (decisão metodológica) |
| 6 dimensões MQM essenciais (não 10) | T22 | Reduz fadiga 500→300 julgamentos; cobre H1/H2/H3 | Lommel et al. 2014 (MQM core) |
| BT prompt minimalista (sem glossário) | T14.B | Mitigação de family bias (Gemini ↔ Gemini) | (decisão metodológica) |
| Dados são anônimos verificados | T22 Step 3.6 | LGPD + ética em pesquisa; verificação automatizada via `verify_anonymization.py` | (compliance) |
| PHI base PT-br: 0 matches | Pre-flight T12 | 7 padrões testados; 0 ocorrências reais | (verificação empírica 2026-04-29) |
| PHI base ES: 21 falso-positivos confirmados visualmente | Pre-flight T12 | "PACIENTE PORTADORA/CON ANTECEDENTE/EN CONTROL" — descrições clínicas, não nomes | (verificação empírica 2026-04-29) |

## Custos

| Decisão | Task | Justificativa | Referência |
|---|---|---|---|
| Phase A custou ~R$160 (vs $0.20 reportado) | T14.A retroativo | (a) stats.json escopo só última sessão (b) thoughts não contado (c) preços yaml errados | (diagnóstico empírico) |
| Phase B prevista ~$0.64 USD | Sumário | DeepSeek $0.27 + GPT-4o-mini $0.17 + BT $0.20 | (estimativa) |
| Backup pré-Phase B em `backups/` | Pre-flight T12 | 9.7M total; protegido via .gitignore | (operacional) |
