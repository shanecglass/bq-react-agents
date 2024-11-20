# flake8: noqa --E501


from model_mgmt import testing
import bigframes as bf
import bigframes.pandas as bpd

import vertexai
from vertexai.generative_models import (
    FunctionDeclaration,
    GenerationConfig,
    GenerativeModel,
    Tool,
)

import os
from pathlib import Path
import shutil
import magika
import requests

m = magika.Magika()

vertexai.init(project=testing.project_id, location=testing.location)

MODEL_ID = "gemini-1.5-pro-002"  # @param {type:"string"}

model = GenerativeModel(
    MODEL_ID,
    system_instruction=[
        "You are a coding expert.",
        "Your mission is to answer all code related questions with given context and instructions.",
    ],
)


def extract_code(repo_dir):
    query = """
        SELECT
        query
        FROM `region-us-west1`.INFORMATION_SCHEMA.JOBS
        WHERE
        (creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 60 DAY)) = TRUE
    """

    hotel_json = bpd.read_gbq(
    hotel_search_query).to_dict(orient="records")[0]



repo_dir = "./"

code_index, code_text = extract_code(repo_dir)


def get_code_prompt(question):
    """Generates a prompt to a code related question."""

    prompt = f"""
    Questions: {question}

    Context:
    - The entire codebase is provided below.
    - Here is an index of all of the files in the codebase:
      \n\n{code_index}\n\n.
    - Then each of the files is concatenated together. You will find all of the code you need:
      \n\n{code_text}\n\n

    Answer:
  """
    return prompt


question = """
I have built a travel planning chatbot using Gemini 1.5 Flash to generate customized itineraries based on user_preferences stored in a database.
Currently, the app makes the `get_user_preferences` function call that returns `user_preferences`. These include:
    `first_name`: First name of the user. Use this to refer to the user going forward.
    `location`: The city and state where the user lives. This is where their trip will start.
    `budget_range`: The user's preferred budget for a trip on a scale of 1 to 5, where 1 is the lowest and 5 is the highest.
    `dest_types`: A comma-separated list of the types of destination the user generally likes to visit (e.g., "Historical Sites", "Beaches").
    `trip_length`: Preferred trip length in days.
    `travel_companions`: Whether the user typically travels by themself (Solo), with a partner (Couple), with friends (Friends), or with family (Family).
    `closest_airports`: Comma-separated list of commerical airports closest to the user's location. Suggest flights from the first airport in the list unless the user specifies otherwise.
After this step, the user should confirm their destination and required points of interest.
I am getting an error when the user submits their email. Please suggest corrections to the prompt as needed
Here is my prompt:

    You are the chatbot for TravelChat, a company that specializes in developing custom travel itineraries.
Your end goal is to create a trip itinerary based on the user's request and their existing preferences.

1. **Get User Preferences:** Extract the `user_email` from the user's request.  Call the `get_user_preferences` function with the `user_email` to retrieve the user's stored preferences:

```tool_code
{{'User_Preferences': get_user_preferences(user_email=user_email)}}
```

2. **Confirm Trip Details:** Greet the user using their first name (from User_Preferences) and confirm the following trip details. If any information is missing or ambiguous, politely ask clarifying questions.  Refer to the retrieved User_Preferences to avoid asking for information you already have.

* **Destination:** Confirm the user's desired destination for this trip. For example: "Okay {{User_Preferences.first_name}}, to confirm, you want to travel to {{User_Destination}}, correct?"  If no destination is provided, ask "Where would you like to travel, {{User_Preferences.first_name}}?"

* **Points of Interest:**  Ask the user to list any specific points of interest they want to visit at their destination. For example: "Are there any specific places in {{User_Destination}} you'd like to visit, {{User_Preferences.first_name}}?  Perhaps a museum, historical site, or a particular restaurant?" If the User_Preferences include `dest_types`, suggest relevant points of interest based on those preferences. For example: "Since you enjoy {{User_Preferences.dest_types}}, you might be interested in [suggest relevant POIs in the chosen destination]."


3. **Generate Itinerary:** Create a personalized itinerary incorporating the confirmed trip details and the retrieved User_Preferences.

* **Destination Summary:** Start with a brief (2-sentence) summary of the destination.
* **Structured Itinerary:** Organize the itinerary by day, with clear headings and bullet points.  Tailor the itinerary to the `trip_length` specified in the User_Preferences.
* **Detailed Information:** Include suggested timings for activities, potential costs (considering the `budget_range` from User_Preferences), and alternative suggestions where appropriate.  Consider the `travel_companions` preference when making suggestions.
* **Flights:** Suggest flights from the first airport listed in the `closest_airports` within User_Preferences, unless the user requests otherwise.


User_Request: {input}

Here is the error message:
The model response did not complete successfully.
Finish reason: 9.
Finish message: Malformed function call:
user_email = "sophia_anderson@example.com"
user_preferences = get_user_preferences(User_Email=user_email)
print(user_preferences)
.
Safety ratings: [].
To protect the integrity of the chat session, the request and response were not added to chat history.
To skip the response validation, specify model.start_chat(response_validation=False).
Note that letting blocked or otherwise incomplete responses into chat history might lead to future interactions being blocked by the service.
"""

prompt = get_code_prompt(question)
contents = [question]

response = model.generate_content(contents)
print(f"\nAnswer:\n{response.text}")
