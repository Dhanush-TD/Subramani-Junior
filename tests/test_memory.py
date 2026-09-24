from memory.long_term_memory import LongTermMemory


memory = LongTermMemory()


print("\nSaving memory...")


result1 = memory.save(
    "The user's project folder is D:\\local-file-agent",
    category="project"
)

result2 = memory.save(
    "The user prefers Kiro for development",
    category="preference"
)


print(
    "\nProject memory saved:",
    result1
)

print(
    "Preference memory saved:",
    result2
)


print("\nStored memories:")

for item in memory.get_all():

    print(item)


print("\nMemory text:")

print(
    memory.to_text()
)