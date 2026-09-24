from tools.file_tools import search_file
from tools.folder_tools import search_folder


print(
    "FILE TEST"
)

print(
    search_file.invoke(
        {
            "filename": "good"
        }
    )
)


print(
    "\nFOLDER TEST"
)

print(
    search_folder.invoke(
        {
            "folder_name": "hi"
        }
    )
)