# Verification matrix — Phase B execution status

Dashboard único de progresso. Cada linha registra os gates passados em cada task ao executar.

| Task | Pre-flight | Run | Verify | Output sanity | Commit | Status |
|---|---|---|---|---|---|---|
| **Pre-flight** | — | — | ✅ APIs (4/4) + PHI (0 reais) + backup | ✅ | `aa17c1d` + `79f6e8d` | DONE |
| **T12** | ✅ Atlas schema definido | ✅ build glossário + collect variantes | ✅ verify_backward_compat exit 0 + verify_morphology exit 0 | ✅ 103 termos / 270 variantes / 25 forms; 14/14 tests passed; 18 termos novos mapeados | `4506368` | **DONE** |
| T12.5 | 🔲 — | 🔲 | 🔲 smoke 20 laudos C1 (alvo: redução ≥70% FP) | 🔲 | 🔲 | PENDING |
| T12.6 | 🔲 | 🔲 smoke 5 | 🔲 severity overrides funcionando | 🔲 | 🔲 | PENDING |
| T13 | 🔲 Step 0 (audit Phase A — feito offline em `19ffd2b`) | 🔲 smoke 1.5 + full nohup | 🔲 verify cross-source | 🔲 | 🔲 | PENDING |
| T13 Step 5 | 🔲 | 🔲 calibração GPT-4o-mini ~250 | 🔲 kappa por critério | 🔲 | 🔲 | PENDING |
| T14.A | 🔲 | 🔲 fix client.py + models.yaml retroativo | 🔲 thoughts contados | 🔲 | 🔲 | PENDING |
| T14.B | 🔲 smoke 10 | 🔲 BT amostral ~250 | 🔲 calibração thresholds | 🔲 | 🔲 | PENDING |
| T15 | 🔲 | 🔲 | 🔲 sanity (median ≥ 0.90) | 🔲 | 🔲 | PENDING |
| T16 | 🔲 | 🔲 | 🔲 regex coverage | 🔲 | 🔲 | PENDING |
| T17 | 🔲 | 🔲 | 🔲 acceptable_rate ≥ 0.99 | 🔲 | 🔲 | PENDING |
| T18 | 🔲 | 🔲 | 🔲 coverage ≥ 70% | 🔲 | 🔲 | PENDING |
| T19 | 🔲 | 🔲 | 🔲 4 camadas distinguidas | 🔲 | 🔲 | PENDING |
| T20 | 🔲 TDD 11 | 🔲 | 🔲 verify cross-source | 🔲 | 🔲 | PENDING |
| T21 | 🔲 TDD 6 | 🔲 | 🔲 kappa pareada 6 fontes | 🔲 | 🔲 | PENDING |
| T22 | 🔲 Step 0 protocol (placeholder a preencher) | 🔲 amostra n=50 + revisão externa | 🔲 extract_mqm | 🔲 | 🔲 | PENDING |
| T23 | 🔲 TDD 5 | 🔲 notebook | 🔲 Holm-Bonferroni | 🔲 | 🔲 | PENDING |

## Nomenclatura

- ✅ = passou
- 🔲 = pendente
- ❌ = falhou (registrar incidente em `incidents.md`)

## Gates ativos no momento

- `verify_atlas_backward_compat.py` — invariante T12 (rodar antes de qualquer commit que toque o Atlas)
- `verify_atlas_morphology.py` — invariante T12 (idem)
- pytest `tests/test_evaluation/` — 14 testes (rodar antes de cada commit Phase B)

## Commits Phase B

```
4506368  feat(evaluation): T12 bootstrap eval module + Atlas BI-RADS glossario
79f6e8d  docs(plan): pre-flight checklist atualizado pos-smoke test
aa17c1d  chore(infra): pre-flight Phase B (backup + APIs validadas + models.yaml corrigido)
19ffd2b  chore(evaluation): T13 Step 0 - audit Phase A correcoes (PROCEED_NORMALLY)
8eb164b  data(translation): outputs Phase A (4357 laudos PT-br + audit results sessao final)
aeac246  docs(evaluation): plano + spec Phase B (12 tasks, 8 hipoteses, 6 lacunas governance)
```
