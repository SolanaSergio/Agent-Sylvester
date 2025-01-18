from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from dataclasses import dataclass

@dataclass
class UIMessage:
    text: str
    type: str = "info"  # info, warning, error, success

class UIManager:
    """Manages UI interactions and display."""
    
    def __init__(self):
        self.console = Console()
        
    def display_welcome(self):
        """Display welcome message"""
        welcome_text = """
        # 🤖 Autonomous Agent Development Studio
        
        Welcome! I'm here to help you build amazing software.
        Type your request or 'exit' to quit.
        """
        self.console.print(Markdown(welcome_text))
        
    def display_status(self, message: str, status_type: str = "info"):
        """Display a status message"""
        style = {
            "info": "blue",
            "warning": "yellow",
            "error": "red",
            "success": "green"
        }.get(status_type, "white")
        
        self.console.print(f"[{style}]{message}[/{style}]")
        
    def display_error(self, error: str):
        """Display an error message"""
        self.console.print(Panel(
            f"[red]Error:[/red] {error}",
            border_style="red"
        ))
        
    def display_success(self, message: str):
        """Display a success message"""
        self.console.print(Panel(
            f"[green]✓[/green] {message}",
            border_style="green"
        ))
        
    def display_components(self, components: List[dict]):
        """Display component information in a table"""
        table = Table(title="Components")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Status", style="green")
        
        for component in components:
            table.add_row(
                component.get('name', 'Unknown'),
                component.get('type', 'Unknown'),
                component.get('status', 'Pending')
            )
            
        self.console.print(table)
        
    def prompt_user(self, message: str) -> str:
        """Prompt user for input"""
        return self.console.input(f"\n[bold blue]?[/bold blue] {message}: ") 