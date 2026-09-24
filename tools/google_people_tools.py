from google_auth import get_google_credentials
from googleapiclient.discovery import build
from langchain_core.tools import tool


# =========================
# CONFIG
# =========================

SCOPES = [
    "https://www.googleapis.com/auth/contacts.readonly"
]


# =========================
# GOOGLE PEOPLE SERVICE
# =========================

def get_people_service():

    credentials = get_google_credentials(
        SCOPES
    )

    service = build(
        "people",
        "v1",
        credentials=credentials
    )

    return service


# =========================
# LIST CONTACTS
# =========================

@tool
def list_google_contacts(page_size: int = 20):
    """
    List contacts from Google Contacts.
    """

    service = get_people_service()

    page_size = min(max(page_size, 1), 100)

    result = service.people().connections().list(
        resourceName="people/me",
        pageSize=page_size,
        personFields="names,emailAddresses,phoneNumbers,organizations"
    ).execute()

    connections = result.get("connections", [])

    if not connections:
        return "No contacts found."

    contacts = []

    for person in connections:

        names = person.get("names", [])
        emails = person.get("emailAddresses", [])
        phones = person.get("phoneNumbers", [])
        organizations = person.get("organizations", [])

        name = (
            names[0].get("displayName", "")
            if names else ""
        )

        email = (
            emails[0].get("value", "")
            if emails else ""
        )

        phone = (
            phones[0].get("value", "")
            if phones else ""
        )

        organization = (
            organizations[0].get("name", "")
            if organizations else ""
        )

        contacts.append({
            "resource_name": person.get("resourceName", ""),
            "name": name,
            "email": email,
            "phone": phone,
            "organization": organization
        })

    return contacts


# =========================
# SEARCH CONTACTS
# =========================

@tool
def search_google_contacts(query: str, page_size: int = 20):
    """
    Search Google Contacts by name, email, or other contact information.
    """

    service = get_people_service()

    query = query.strip()

    if not query:
        return "Search query cannot be empty."

    page_size = min(max(page_size, 1), 30)

    result = service.people().searchContacts(
        query=query,
        pageSize=page_size,
        readMask="names,emailAddresses,phoneNumbers,organizations"
    ).execute()

    results = result.get("results", [])

    if not results:
        return "No matching contacts found."

    contacts = []

    for item in results:

        person = item.get("person", {})

        names = person.get("names", [])
        emails = person.get("emailAddresses", [])
        phones = person.get("phoneNumbers", [])
        organizations = person.get("organizations", [])

        name = (
            names[0].get("displayName", "")
            if names else ""
        )

        email = (
            emails[0].get("value", "")
            if emails else ""
        )

        phone = (
            phones[0].get("value", "")
            if phones else ""
        )

        organization = (
            organizations[0].get("name", "")
            if organizations else ""
        )

        contacts.append({
            "resource_name": person.get("resourceName", ""),
            "name": name,
            "email": email,
            "phone": phone,
            "organization": organization
        })

    return contacts


# =========================
# GET CONTACT
# =========================

@tool
def get_google_contact(resource_name: str):
    """
    Get detailed information about a Google Contact.

    Example resource name:
    people/c123456789
    """

    service = get_people_service()

    person = service.people().get(
        resourceName=resource_name,
        personFields="names,emailAddresses,phoneNumbers,organizations,birthdays,addresses"
    ).execute()

    return person


# =========================
# EXPORT TOOLS
# =========================

google_people_tools = [
    list_google_contacts,
    search_google_contacts,
    get_google_contact,
]