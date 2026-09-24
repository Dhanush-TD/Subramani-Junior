from tools.web_tools import web_search


query = input("Search: ")

result = web_search.invoke({
    "query": query
})

print("\n" + "=" * 80)
print("WEB SEARCH RESULTS")
print("=" * 80)

print(result)