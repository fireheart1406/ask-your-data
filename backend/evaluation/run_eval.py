import json
import os
import sys
import time
from datetime import date, datetime
from decimal import Decimal
from agent import ask
from db import run_readonly_query
HERE = os.path.dirname(os.path.abspath(__file__))
DELAY_SECONDS = float(os.getenv("EVAL_DELAY_SECONDS", "6"))   # keeps you under free-tier rate limits
def norm_value(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, (int, float, Decimal)):
        return round(float(v), 2)
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    return str(v).strip()
def norm_rows(rows):
    return sorted((tuple(norm_value(v) for v in r) for r in rows), key=repr)
def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "run"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    with open(os.path.join(HERE, "questions.json"), encoding="utf-8") as f:
        questions = json.load(f)
    if limit:
        questions = questions[:limit]
    results = []
    for q in questions:
        try:
            _, gold_rows, _ = run_readonly_query(q["gold_sql"])
            gold = norm_rows(gold_rows)
        except Exception as e:
            print(f"[{q['id']:>2}] GOLD SQL BROKEN: {e}")
            continue
        try:
            result = ask(q["question"])
        except Exception as e:
            result = {"ok": False, "sql": "", "rows": [], "attempt_count": 0, "error": str(e)}
        predicted = norm_rows(result["rows"]) if result["ok"] else None
        passed = predicted is not None and predicted == gold
        first_try = passed and result["attempt_count"] == 1
        mark = "PASS" if passed else "FAIL"
        print(f"[{q['id']:>2}] {mark} ({q['level']}, tries={result['attempt_count']}) {q['question']}")
        if not passed:
            print(f"       predicted SQL: {result['sql']}")
            print(f"       gold SQL:      {q['gold_sql']}")
            print(f"       predicted rows: {str(predicted)[:150]}")
            print(f"       gold rows:      {str(gold)[:150]}")
        results.append({
            "id": q["id"], "level": q["level"], "question": q["question"],
            "passed": passed, "first_try": first_try,
            "attempts": result["attempt_count"], "predicted_sql": result["sql"],
            "gold_sql": q["gold_sql"], "error": result.get("error"),
        })
        time.sleep(DELAY_SECONDS)
    total = len(results)
    passed = sum(r["passed"] for r in results)
    first = sum(r["first_try"] for r in results)
    print("\n=== SUMMARY ===")
    print(f"Accuracy (with retries): {passed}/{total} = {100 * passed / total:.1f}%")
    print(f"Accuracy (first try):    {first}/{total} = {100 * first / total:.1f}%")
    for level in ("easy", "medium", "hard"):
        subset = [r for r in results if r["level"] == level]
        if subset:
            print(f"  {level}: {sum(r['passed'] for r in subset)}/{len(subset)}")
    out_path = os.path.join(HERE, f"results_{label}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved details to {out_path}")
if __name__ == "__main__":
    main()