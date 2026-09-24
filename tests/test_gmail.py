from tools.gmail_tools import check_emails


print("Testing Gmail...")

result = check_emails.invoke({
    "count": 5
})

print("\n========== GMAIL RESULT ==========\n")
print(result)