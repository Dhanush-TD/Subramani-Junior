from tools.terminal_tool import terminal_tool


while True:

    command = input("\nPowerShell> ")

    if command.lower() in ("exit", "quit"):
        break

    result = terminal_tool(command)

    print("\n--- OUTPUT ---")
    print(result)