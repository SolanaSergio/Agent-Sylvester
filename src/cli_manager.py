import click
import questionary
from typing import Dict, List, Optional
import logging
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import asyncio

from .agents.meta_agent import MetaAgent
from .utils.types import AgentStatus
from .managers.ui_manager import UIManager

console = Console()

class CLIManager:
    """Manages the CLI interface and user interactions"""
    
    def __init__(self):
        self.ui = UIManager()
        self.agent: Optional[MetaAgent] = None
        self.main_menu_items = {
            "🆕 New Project": self.handle_new_project,
            "🔨 Build/Update Project": self.handle_build_project,
            "📊 Project Status": self.display_agent_status,
            "👋 Exit": lambda: False
        }
        
    def display_welcome(self):
        """Display welcome message"""
        console.print(Panel.fit(
            "[bold blue]Welcome to Auto Agent[/bold blue]\n"
            "Your AI-powered development assistant",
            border_style="blue",
            title="🤖 Auto Agent"
        ))
        
    async def display_main_menu(self) -> bool:
        """Display the main menu and handle selection"""
        choices = list(self.main_menu_items.keys())
        
        answer = await questionary.select(
            "Select an option:",
            choices=choices,
            style=questionary.Style([
                ('qmark', 'fg:cyan bold'),
                ('question', 'bold'),
                ('answer', 'fg:cyan bold'),
                ('pointer', 'fg:cyan bold'),
                ('highlighted', 'fg:cyan bold'),
            ])
        ).ask_async()
        
        if answer:
            action = self.main_menu_items[answer]
            if asyncio.iscoroutinefunction(action):
                return await action()
            return action()
        return True

    async def handle_new_project(self) -> bool:
        """Handle new project creation"""
        questions = [
            {
                "type": "text",
                "name": "project_name",
                "message": "Project name:",
                "validate": lambda text: len(text) >= 3
            },
            {
                "type": "text",
                "name": "description",
                "message": "Brief project description:"
            },
            {
                "type": "select",
                "name": "type",
                "message": "Project type:",
                "choices": [
                    "Web Application (Next.js)",
                    "API Service (Node/Express)",
                    "Full Stack (Next.js + API)",
                    "Static Website"
                ]
            }
        ]
        
        answers = await questionary.prompt(questions)
        if answers:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                task = progress.add_task("Creating project...", total=None)
                await self.initialize_agent(str(answers))
                console.print(f"[green]✅ Project '{answers['project_name']}' created successfully![/green]")
        return True

    async def handle_build_project(self) -> bool:
        """Handle project building/updating"""
        if not self.agent:
            console.print("[red]No active project. Please create a new project first.[/red]")
            return True
            
        description = await questionary.text(
            "What would you like to add or modify in the project?",
            style=questionary.Style([
                ('qmark', 'fg:cyan bold'),
                ('question', 'bold'),
                ('answer', 'fg:cyan bold'),
            ])
        ).ask_async()
        
        if description:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                task = progress.add_task("Processing request...", total=None)
                await self.agent.process_user_input(description)
        return True

    def display_agent_status(self) -> bool:
        """Display current agent status"""
        if not self.agent:
            console.print("[yellow]No active project. Use 'New Project' to get started.[/yellow]")
            return True
            
        status_panel = Panel(
            f"[bold]Project:[/bold] {self.agent.project_name}\n"
            f"[bold]Status:[/bold] {self.agent.progress.status}\n"
            f"[bold]Current Task:[/bold] {self.agent.progress.current_task}",
            title="🤖 Project Status",
            border_style="blue"
        )
        console.print(status_panel)
        return True

async def run_cli(debug: bool = False, output_dir: str = "./projects"):
    """Run the CLI application"""
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
        
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    cli_manager = CLIManager()
    cli_manager.display_welcome()
    
    while True:
        try:
            should_continue = await cli_manager.display_main_menu()
            if not should_continue:
                console.print("[yellow]👋 Goodbye![/yellow]")
                break
        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'Exit' option to quit.[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            if debug:
                logging.exception("Error in main menu")

@click.command()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--output-dir', default="./projects", help='Output directory for generated projects')
def main(debug: bool, output_dir: str):
    """Auto Agent - Your AI-powered development assistant"""
    asyncio.run(run_cli(debug, output_dir))
    
if __name__ == "__main__":
    main() 