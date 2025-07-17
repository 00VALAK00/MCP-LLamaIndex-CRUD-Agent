import asyncio
import sys
from scripts.workflow import DatabaseWorkflow
from llama_index.core.workflow import Context
import mlflow


mlflow.llama_index.autolog()
mlflow.set_tracking_uri("http://localhost:5000")

async def main():
    workflow = DatabaseWorkflow()
    await workflow.initialize()


    while True:
        try:
            user_input = input("What would you like to do?")
            ret = await workflow.run(input=user_input)
            print(f" final result >>>>>>>> {ret}")
        except KeyboardInterrupt:
            print("Exiting...")
            break

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)








