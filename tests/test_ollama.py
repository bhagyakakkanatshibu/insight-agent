import ollama

r = ollama.chat(
    model="phi3:mini",
    messages=[{"role":"user","content":"Say OK"}],
    options={"temperature":0.2}
)
print(r["message"]["content"])
