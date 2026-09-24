from .auth import create_google_oauth_provider


provider = create_google_oauth_provider()

print("Google MCP OAuth provider created successfully")
print(type(provider).__name__)