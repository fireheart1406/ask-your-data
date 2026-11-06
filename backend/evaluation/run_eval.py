import json
import os
import sys
import time
from datetime import date, datetime
from decimal import Decimal
from agent import ask
from db import run_readonly_query
HERE = os.path.dirname(os.path.abspath(__file__))
DELAY_SECONDS = float(os.getenv("EVAL_DELAY_SECONDS", "8"))   # pause between questions
COOLDOWN_SECONDS = 60                                         # longer pause after a service error
MAX_CONSECUTIVE_SERVICE_ERRORS = 3
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
def parse_args():
    args = sys.argv[1:]
    positional = [a for a in args if not a.startswith("--")]
    label = positional[0] if positional else "run"
    resume = "--resume" in args
    limit = None
    if "--limit" in args:
        limit = int(args[args.index("--limit") + 1])
        if str(limit) in positional and positional[0] == str(limit):
            label = "run"
    return label, resume, limit
def is_service_error(record):
    """True when the AI never produced an answer (quota, busy server, etc.)."""
    return record.get("service_error", record.get("attempts", 0) == 0)
def save(path, results):
    ordered = sorted(results.values(), key=lambda r: r["id"])
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ordered, f, indent=2)
def main():
    label, resume, limit = parse_args()
    out_path = os.path.join(HERE, f"results_{label}.json")

    with open(os.path.join(HERE, "questions.json"), encoding="utf-8") as f:
        questions = json.load(f)
    if limit:
        questions = questions[:limit]
    results = {}
    if resume and os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            for r in json.load(f):
                if not is_service_error(r):
                    results[r["id"]] = r
        print(f"Resuming: keeping {len(results)} questions that already have answers.\n")
    consecutive_errors = 0
    for q in questions:
        if q["id"] in results:
            continue
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
        service_error = result["attempt_count"] == 0
        passed = False
        first_try = False
        if service_error:
            consecutive_errors += 1
            print(f"[{q['id']:>2}] NO ANSWER (AI service problem): {str(result.get('error'))[:200]}")
        else:
            consecutive_errors = 0
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
        results[q["id"]] = {
            "id": q["id"], "level": q["level"], "question": q["question"],
            "passed": passed, "first_try": first_try,
            "attempts": result["attempt_count"], "service_error": service_error,
            "predicted_sql": result["sql"], "gold_sql": q["gold_sql"],
            "error": result.get("error"),
        }
        save(out_path, results)#the progress is saved here
        if consecutive_errors >= MAX_CONSECUTIVE_SERVICE_ERRORS:
            print("\nStopping early: the AI service failed 3 times in a row.")
            print("Your progress is saved. Run again later with --resume.")
            break
        time.sleep(COOLDOWN_SECONDS if service_error else DELAY_SECONDS)
    ids = {q["id"] for q in questions}
    scored = [r for r in results.values() if r["id"] in ids]
    answered = [r for r in scored if not is_service_error(r)]
    total = len(questions)
    passed = sum(r["passed"] for r in answered)
    first = sum(r["first_try"] for r in answered)
    missing = total - len(answered)
    print("\n=== SUMMARY ===")
    print(f"Questions answered by the AI: {len(answered)} of {total}")
    if answered:
        print(f"Accuracy on answered questions (with retries): {passed}/{len(answered)} = {100 * passed / len(answered):.1f}%")
        print(f"Accuracy on answered questions (first try):    {first}/{len(answered)} = {100 * first / len(answered):.1f}%")
        for level in ("easy", "medium", "hard"):
            subset = [r for r in answered if r["level"] == level]
            if subset:
                print(f"  {level}: {sum(r['passed'] for r in subset)}/{len(subset)}")
    if missing:
        print(f"\nWARNING: {missing} question(s) got no answer, so this is NOT a valid final score.")
        print("Run again with --resume when the AI service is available.")
    print(f"Saved details to {out_path}")
if __name__ == "__main__":
    main()