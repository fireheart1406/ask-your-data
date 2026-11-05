from agent import ask
print("Ask Your Data (type 'quit' to stop)\n")
while True:
    question = input("Question> ").strip()
    if question.lower() in ("quit", "exit", ""):
        break
    result = ask(question)
    print("\nSQL:", result["sql"])
    print("Tries:", result["attempt_count"])
    if result["ok"]:
        print("Columns:", result["columns"])
        for row in result["rows"][:10]:
            print("  ", row)
        if result["row_count"] > 10:
            print(f"   ... {result['row_count']} rows in total")
    else:
        print("FAILED:", result["error"])
    print()