"""Phase 2 acceptance: review one sample snippet and print the validated ReviewResult."""
from __future__ import annotations

from src.reviewer import review

SAMPLE = '''\
def process_payment(amount, user):
    api_key = "sk_live_51H8xQ2eZvKYlo"
    total = amount + amount * 0.0825
    if total > 10000:
        total = total - 100
    try:
        return charge(total, api_key)
    except:
        return None
'''


def main() -> None:
    result = review(SAMPLE)
    print(result.model_dump_json(indent=2))
    print(f"\nfindings: {len(result.findings)} · positive_note: {result.positive_note!r}")
    assert result.findings, "expected at least one finding"
    assert result.positive_note, "expected a positive note"
    print("Phase 2 acceptance: OK")


if __name__ == "__main__":
    main()
