from google import genai
import os
import requests
import json

# client=genai.Client(api_key="AIzaSyBxImVoBCyPUFvUKohZFU2_Pg6iE7B0prU")
# #client=genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# response = client.models.generate_content(
#     model="gemini-3-flash-preview",
#     contents="Explain how AI works in a few words",
# )

# print(response.text)

result=requests.post(
    "http://localhost:8000/scan-repo",
    json={"repo_url":"https://github.com/maticfilip/PDFEditor"}
).json()

with open("output.json","w") as json_file:
    json.dump(result, json_file, indent=4)

