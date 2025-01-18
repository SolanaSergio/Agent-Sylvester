import asyncio
from src.cli_manager import CLIManager
import logging

async def main():
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start CLI manager
    cli = CLIManager()
    await cli.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye! 👋")
    except Exception as e:
        logging.exception("Application error")
        print(f"Error: {str(e)}") 