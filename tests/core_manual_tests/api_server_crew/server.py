import os

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

import agentops
from fastapi import FastAPI
import uvicorn
from dotenv import load_dotenv
from openai import OpenAI
import json
import logging
from crewai import Agent, Crew, Task

load_dotenv()

openai = OpenAI()
agentops.init()
app = FastAPI()

agentops.init(auto_start_session=False)


@app.get("/completion")
def completion():
    session = agentops.start_session(tags=["api-server-test"])

    # llm = ChatOpenAI(model_name="gpt-4", temperature=0.7)

    llm = ChatGroq(
        temperature=0,
        groq_api_key=os.environ.get("GROQ_API_KEY"),
        model_name="llama3-70b-8192",
    )

    agent = Agent(
        role="greeter",
        goal="make sure every person feels welcomed",
        backstory="you partied too much in school and now you're trying to turn your life around. you applied for a "
        "job at walmart as a greeter and you want to do as well as possible at greeting as your first rung "
        "on the climb up the corporate ladder.",
        verbose=False,
        llm=llm,
    )

    tasks = []
    task1 = Task(
        description="a man in a blue coat walks through the door",
        agent=agent,
        expected_output="a script of what the greeter will say",
    )
    tasks.append(task1)

    task2 = Task(
        description="a woman with a small dog in her arms rushes through the door, seemingly in a hurry",
        agent=agent,
        expected_output="a script of what the greeter will say",
    )
    tasks.append(task2)

    task3 = Task(
        description="a tall, grizzled looking man with a sour look on his face enters the store. he appears to be in a bad "
        "mood.",
        agent=agent,
        expected_output="a script of what the greeter will say",
    )
    tasks.append(task3)

    crew = Crew(agents=[agent], tasks=tasks, verbose=True)

    # Crew Execution
    output = crew.kickoff()

    # End session

    session.end_session(end_state="Success")

    print(output)
    return {"response": output}


uvicorn.run(app, host="0.0.0.0", port=9696)
