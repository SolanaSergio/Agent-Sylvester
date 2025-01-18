import asyncio
import sys
from rich.console import Console
from src.managers.cli_manager import CLIManager
from src.utils.system_checker import SystemChecker

console = Console()

async def main():
    try:
        # Check system requirements first
        requirements = SystemChecker.check_requirements()
        
        # Check if any requirements are missing
        missing_requirements = [req for req, installed in requirements.items() if not installed]
        
        if missing_requirements:
            console.print("[red]Error: The following required tools are not available:[/red]")
            for req in missing_requirements:
                console.print(f"[red]- {req}[/red]")
            console.print("\n[yellow]Please ensure these tools are installed and available in your system PATH:[/yellow]")
            console.print("1. Python 3.6 or higher")
            console.print("2. Node.js and npm (https://nodejs.org)")
            console.print("3. Git (https://git-scm.com)")
            sys.exit(1)
        
        # All requirements met, start the CLI
        cli = CLIManager()
        await cli.start()
    except Exception as e:
        console.print(f"[red]Error during startup: {str(e)}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye! 👋[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1) 