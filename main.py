import asyncio
import logging
import sys
from scripts.workflow import DatabaseWorkflow
from llama_index.core.workflow import Context
import argparse


async def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--docker", action="store_true", help="Sets the url to the ollama server (default is docker)")
    args = parser.parse_args()

    logging.info(f"Url to ollama server has been set to: {'docker' if args.docker else 'local'}")

    workflow = DatabaseWorkflow()
    await workflow.initialize(is_docker=args.docker)


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








