

from tools.rag_tools import find_file_with_rag


query = "test file"

result = find_file_with_rag(query)

print()
print("========================================")
print("FINAL RESULT")
print("========================================")
print(result)