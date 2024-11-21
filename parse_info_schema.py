# flake8: noqa --E501

import bigframes as bf
import bigframes.pandas as bpd

import vertexai
from vertexai.generative_models import (
    GenerativeModel,
)

from json_repair import repair_json

import os
from pathlib import Path
import shutil
import magika
import requests

m = magika.Magika()

project_id = "scg-l200-genai2"
location = "us-west1"

vertexai.init(project=project_id, location=location)

MODEL_ID = "gemini-1.5-pro-002"  # @param {type:"string"}

model = GenerativeModel(
    MODEL_ID,
    system_instruction=[
        "You are a coding expert.",
        "Your mission is to answer all code related questions with given context and instructions.",
    ],
)


def extract_code():
    query = """
        SELECT
            STRING_AGG(query) AS query
        FROM
            `region-us-west1`.INFORMATION_SCHEMA.JOBS
        WHERE
            creation_time BETWEEN TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 60 DAY) AND TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
            AND query LIKE "%JOIN%"
    """

    query_json = bpd.read_gbq(
        query).to_dict(orient="records")[0]
    return query_json



repo_dir = "./"

# code_index, code_text = extract_code(repo_dir)

code_text = extract_code()


def get_code_prompt_overview(question):
    """Generates a prompt to interpret SQL queries."""

    prompt = f"""
    Questions: {question}

    Context:
    - Replace any table aliases in the queries to their actual table names.
    - If a query involves multiple tables, output all the pairwise relationships.
    - The SQL queries are concatenated together. You will find all of the code you need here:
      \n```\n{code_text}\n```\n


    Answer:
  """
    return prompt


question = """
Analyze these queries and describe the relationships between the tables.
Define which tables are joined together and how they are joined, even when there are multiple joins within a single query.
"""

overview_prompt = get_code_prompt_overview(question)
overview_contents = [overview_prompt]
overview_response = model.generate_content(overview_contents)
with open("erd_description.txt", "w") as file:
    file.write(overview_response.text)


def get_code_prompt_json(question):
    """Generates a prompt to interpret SQL queries."""

    prompt = f"""
    Questions: {question}

    Context:
    - Resolve any table aliases to their actual table names.
    - If a query involves multiple tables, output all the pairwise relationships.
    - Do not define the JOIN for UNNEST conditions.
    - Format the output as JSON. Output a list of relationships with the following structure for each relationship:
    {{
        "table1": "actual_table_name_1",
        "table2": "actual_table_name_2",
        "join_type": "join_type",
        "on": "join_condition"
    }}
    - The SQL queries are concatenated together. You will find all of the code you need here:
      \n```\n{code_text}\n```\n


    Answer:
  """
    return prompt


json_prompt = get_code_prompt_json(question)
json_contents = [json_prompt]
json_response = model.generate_content(json_contents)
cleaned_json_response = repair_json(json_response.text)
with open("erd_output.json", "w") as file:
    file.write(cleaned_json_response)
print("File written")

overview_prompt = get_code_prompt_overview(question)
overview_contents = [overview_prompt]
overview_response = model.generate_content(overview_contents)
with open("erd_description.md", "w") as file:
    file.write(overview_response.text)

print(f"\nAnswer:\n{overview_response.text}")
