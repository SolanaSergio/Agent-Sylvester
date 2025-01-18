import click
import questionary
from typing import Dict, List, Optional
import logging
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
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
            "🚀 Initialize New Project": self.handle_init,
            "🔍 Analyze Code": lambda: self.handle_analysis_menu(),
            "⚡ Generate Code": lambda: self.handle_generation_menu(),
            "🛠️ Build & Deploy": lambda: self.handle_build_menu(),
            "📝 Documentation": lambda: self.handle_docs_menu(),
            "📊 View Status": self.display_agent_status,
            "❓ Help": self.display_help,
            "👋 Exit": lambda: False
        }
        
    def display_welcome(self):
        """Display welcome message and agent status"""
        console.print(Panel.fit(
            "[bold blue]Welcome to Auto Agent[/bold blue]\n"
            "Your AI-powered development assistant\n"
            "[dim]Select an option from the menu below[/dim]",
            border_style="blue",
            title="🤖 Auto Agent",
            subtitle="v1.0.0"
        ))
        
    def display_help(self):
        """Display help information"""
        help_text = """
[bold blue]🤖 Auto Agent Help[/bold blue]

[bold]Main Features:[/bold]
• Project Initialization - Create new projects with various frameworks
• Code Analysis - Analyze code quality, patterns, and requirements
• Code Generation - Generate components, APIs, and more
• Build & Deploy - Build projects and deploy to various platforms
• Documentation - Generate comprehensive documentation

[bold]Tips:[/bold]
• Use arrow keys to navigate menus
• Press Enter to select an option
• Press Ctrl+C to go back or exit
"""
        console.print(Panel(help_text, border_style="blue"))
        return True

    async def display_main_menu(self) -> bool:
        """Display the main menu and handle selection"""
        choices = list(self.main_menu_items.keys())
        
        answer = await questionary.select(
            "What would you like to do?",
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

    async def handle_analysis_menu(self) -> bool:
        """Handle code analysis options"""
        if not self.agent:
            console.print("[red]Please initialize a project first[/red]")
            return True
            
        choices = [
            "🔍 Analyze Code Quality",
            "🎯 Analyze Requirements",
            "🧩 Analyze Components",
            "🔒 Security Analysis",
            "♿ Accessibility Analysis",
            "⬅️ Back to Main Menu"
        ]
        
        answer = await questionary.select(
            "Select analysis type:",
            choices=choices
        ).ask_async()
        
        if answer and "Back" not in answer:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                progress.add_task(f"Running {answer}...", total=None)
                await self.agent.process_user_input(f"analyze {answer}")
        return True

    async def handle_generation_menu(self) -> bool:
        """Handle code generation options"""
        if not self.agent:
            console.print("[red]Please initialize a project first[/red]")
            return True
            
        choices = [
            "🧩 Generate Component",
            "🔌 Generate API",
            "📝 Generate Documentation",
            "📊 Generate Schema",
            "🔄 Generate Migration",
            "⬅️ Back to Main Menu"
        ]
        
        answer = await questionary.select(
            "What would you like to generate?",
            choices=choices
        ).ask_async()
        
        if answer and "Back" not in answer:
            await self.handle_generation_type(answer)
        return True

    async def handle_build_menu(self) -> bool:
        """Handle build and deployment options"""
        if not self.agent:
            console.print("[red]Please initialize a project first[/red]")
            return True
            
        choices = [
            "🏗️ Build Project",
            "🚀 Deploy Project",
            "🐳 Build Docker Container",
            "🔄 Run Tests",
            "⬅️ Back to Main Menu"
        ]
        
        answer = await questionary.select(
            "Select build/deploy action:",
            choices=choices
        ).ask_async()
        
        if answer and "Back" not in answer:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                progress.add_task(f"Processing {answer}...", total=None)
                await self.agent.process_user_input(f"build {answer}")
        return True

    async def handle_docs_menu(self) -> bool:
        """Handle documentation options"""
        if not self.agent:
            console.print("[red]Please initialize a project first[/red]")
            return True
            
        choices = [
            "📚 Generate Project Documentation",
            "📘 Generate API Documentation",
            "🧩 Generate Component Documentation",
            "📋 Generate Usage Guide",
            "⬅️ Back to Main Menu"
        ]
        
        answer = await questionary.select(
            "Select documentation type:",
            choices=choices
        ).ask_async()
        
        if answer and "Back" not in answer:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                progress.add_task(f"Generating {answer}...", total=None)
                await self.agent.process_user_input(f"docs {answer}")
        return True

    async def handle_init(self) -> bool:
        """Handle project initialization"""
        questions = [
            {
                "type": "text",
                "name": "project_name",
                "message": "Project name:",
                "validate": lambda text: len(text) >= 3
            },
            {
                "type": "select",
                "name": "project_type",
                "message": "Select project type:",
                "choices": ["Next.js", "React", "Vue", "Angular"]
            },
            {
                "type": "checkbox",
                "name": "features",
                "message": "Select features:",
                "choices": [
                    "Authentication",
                    "Database",
                    "API",
                    "Testing",
                    "Documentation",
                    "Docker",
                    "CI/CD"
                ]
            }
        ]
        
        answers = await questionary.prompt(questions, style=questionary.Style([
            ('qmark', 'fg:cyan bold'),
            ('question', 'bold'),
            ('answer', 'fg:cyan bold'),
        ]))
        
        if answers:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                progress.add_task("Initializing project...", total=None)
                await self.initialize_agent(str(answers))
                console.print("[green]✅ Project initialized successfully![/green]")
        return True

    async def handle_generation_type(self, gen_type: str):
        """Handle specific generation type"""
        type_questions = {
            "🧩 Generate Component": [
                {"type": "text", "name": "name", "message": "Component name:"},
                {"type": "select", "name": "style", "message": "Styling solution:", 
                 "choices": ["Tailwind", "CSS Modules", "Styled Components", "CSS-in-JS"]}
            ],
            "🔌 Generate API": [
                {"type": "text", "name": "endpoint", "message": "API endpoint:"},
                {"type": "select", "name": "method", "message": "HTTP Method:",
                 "choices": ["GET", "POST", "PUT", "DELETE"]}
            ],
            "📊 Generate Schema": [
                {"type": "text", "name": "name", "message": "Schema name:"},
                {"type": "select", "name": "type", "message": "Schema type:",
                 "choices": ["Database", "API", "Validation"]}
            ]
        }
        
        questions = type_questions.get(gen_type, [])
        if questions:
            answers = await questionary.prompt(questions)
            if answers:
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                    progress.add_task(f"Generating {gen_type}...", total=None)
                    await self.agent.process_user_input(f"generate {gen_type} {answers}")

    def display_agent_status(self) -> bool:
        """Display current agent status"""
        if not self.agent:
            console.print("[red]Agent not initialized. Please initialize a project first.[/red]")
            return True
            
        status_panel = Panel(
            f"[bold]Current Status:[/bold] {self.agent.progress.status}\n"
            f"[bold]Current Task:[/bold] {self.agent.progress.current_task}\n"
            f"[bold]Progress:[/bold] {self.agent.progress.progress}%",
            title="🤖 Agent Status",
            border_style="blue"
        )
        console.print(status_panel)
        return True

@click.command()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--output-dir', default="./projects", help='Output directory for generated projects')
def main(debug: bool, output_dir: str):
    """Auto Agent - Your AI-powered development assistant"""
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
        
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    async def run_cli():
        cli_manager = CLIManager()
        cli_manager.display_welcome()
        
        while True:
            try:
                should_continue = await cli_manager.display_main_menu()
                if not should_continue:
                    console.print("[yellow]👋 Goodbye![/yellow]")
                    break
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted by user. Use the Exit option to quit.[/yellow]")
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
                if debug:
                    logging.exception("Error in main menu")
                    
    asyncio.run(run_cli())
    
if __name__ == "__main__":
    main() 