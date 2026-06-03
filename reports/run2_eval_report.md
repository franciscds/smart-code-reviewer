# Eval Report — Smart Code Reviewer

_Generated: 2026-06-03 18:03 · model: `claude-sonnet-4-6` · cases: 6_

## Aggregate

| metric | value |
| --- | --- |
| detection_rate (recall) | **88%** (14/16) |
| severity_weighted_recall | 92% (24/26) |
| false_positive_signal | 63% (24/38) |
| should_not_flag hits | 1 |

## By dimension

| dimension | detection_rate | false_positive_signal |
| --- | --- | --- |
| readability | 83% (5/6) | 64% (9/14) |
| structure | 67% (2/3) | 50% (2/4) |
| maintainability | 100% (7/7) | 65% (13/20) |

## Per case

| case | expected | matched | recall | findings | fp_signal | snf hits |
| --- | --- | --- | --- | --- | --- | --- |
| payment_secrets | 4 | 4 | 100% | 10 | 60% | 1 |
| deep_nesting | 3 | 2 | 67% | 8 | 75% | 0 |
| duplication_naming | 3 | 3 | 100% | 9 | 67% | 0 |
| mutable_default | 2 | 2 | 100% | 3 | 33% | 0 |
| dead_code_style | 4 | 3 | 75% | 8 | 62% | 0 |
| clean_baseline | 0 | 0 | n/a | 0 | n/a | 0 |

## Misses — what to fix next

- **deep_nesting**: structure/complex_conditional (low) lines [6]
- **dead_code_style**: readability/long_line (low) lines [6]
