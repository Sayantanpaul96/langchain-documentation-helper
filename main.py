import os
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv

load_dotenv()

llm = ChatAnthropic(
    model_name=os.environ["FCC_MODEL"],
    base_url=os.environ["FCC_BASE_URL"].removesuffix('/v1'),
    api_key=os.environ["FCC_API_KEY"],
    temperature=0
)

agent = create_agent(model=llm)

def main():
    print("Hello from langchain-documentation-helper!")
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "What is langsmith"
                }
            ]
        }
    )


if __name__ == "__main__":
    main()
