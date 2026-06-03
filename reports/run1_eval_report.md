# Eval Report — Smart Code Reviewer

_Generated: 2026-06-03 16:18 · model: `claude-sonnet-4-6` · cases: 6_

## Aggregate

| metric | value |
| --- | --- |
| detection_rate (recall) | **75%** (12/16) |
| severity_weighted_recall | 85% (22/26) |
| false_positive_signal | 61% (19/31) |
| should_not_flag hits | 3 |

## By dimension

| dimension | detection_rate | false_positive_signal |
| --- | --- | --- |
| readability | 67% (4/6) | 64% (7/11) |
| structure | 67% (2/3) | 50% (2/4) |
| maintainability | 86% (6/7) | 62% (10/16) |

## Per case

| case | expected | matched | recall | findings | fp_signal | snf hits |
| --- | --- | --- | --- | --- | --- | --- |
| payment_secrets | 4 | 3 | 75% | 7 | 57% | 0 |
| deep_nesting | 3 | 2 | 67% | 8 | 75% | 0 |
| duplication_naming | 3 | 3 | 100% | 7 | 57% | 1 |
| mutable_default | 2 | 2 | 100% | 3 | 33% | 0 |
| dead_code_style | 4 | 2 | 50% | 6 | 67% | 2 |
| clean_baseline | 0 | 0 | n/a | 0 | n/a | 0 |

## Misses — what to fix next

- **payment_secrets**: maintainability/missing_type_hints (low) lines [5]
- **deep_nesting**: structure/complex_conditional (low) lines [6]
- **dead_code_style**: readability/inconsistent_style (low) lines [6]
- **dead_code_style**: readability/long_line (low) lines [6]
