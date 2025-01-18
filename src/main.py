import asyncio
from src.managers.cli_manager import CLIManager

async def main():
    cli_manager = CLIManager()
    await cli_manager.start() 