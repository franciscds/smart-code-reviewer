# Eval Report — Smart Code Reviewer

_Generated: 2026-06-03 18:09 · model: `claude-sonnet-4-6` · cases: 6_

## Aggregate

| metric | value |
| --- | --- |
| detection_rate (recall) | **81%** (13/16) |
| severity_weighted_recall | 88% (23/26) |
| false_positive_signal | 64% (23/36) |
| should_not_flag hits | 0 |

## By dimension

| dimension | detection_rate | false_positive_signal |
| --- | --- | --- |
| readability | 67% (4/6) | 69% (9/13) |
| structure | 67% (2/3) | 50% (2/4) |
| maintainability | 100% (7/7) | 63% (12/19) |

## Per case

| case | expected | matched | recall | findings | fp_signal | snf hits |
| --- | --- | --- | --- | --- | --- | --- |
| payment_secrets | 4 | 4 | 100% | 10 | 60% | 0 |
| deep_nesting | 3 | 2 | 67% | 8 | 75% | 0 |
| duplication_naming | 3 | 3 | 100% | 9 | 67% | 0 |
| mutable_default | 2 | 2 | 100% | 3 | 33% | 0 |
| dead_code_style | 4 | 2 | 50% | 6 | 67% | 0 |
| clean_baseline | 0 | 0 | n/a | 0 | n/a | 0 |

## Misses — what to fix next

- **deep_nesting**: structure/complex_conditional (low) lines [6]
- **dead_code_style**: readability/inconsistent_style (low) lines [6]
- **dead_code_style**: readability/long_line (low) lines [6]
