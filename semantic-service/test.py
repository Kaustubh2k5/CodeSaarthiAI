from app.llm.loader import llm

print("Generating test output...")

output = llm.generate("Explain what a Python function is in one sentence.")

print(output)