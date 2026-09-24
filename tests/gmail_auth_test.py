from tools.gmail_tools import get_gmail_service


print("=" * 50)
print("Gmail Authentication Test")
print("=" * 50)

try:
    service = get_gmail_service()

    profile = service.users().getProfile(
        userId="me"
    ).execute()

    print("\nGmail authentication successful!")
    print(f"Email: {profile.get('emailAddress')}")
    print(f"Messages: {profile.get('messagesTotal')}")
    print(f"Threads: {profile.get('threadsTotal')}")

except Exception as e:
    print("\nGmail authentication failed.")
    print(e)