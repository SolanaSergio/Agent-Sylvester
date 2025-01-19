import click
import questionary
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.logging import RichHandler
import asyncio
from questionary import Style

from src.agents.meta_agent import MetaAgent
from src.utils.types import AgentStatus
from src.managers.ui_manager import UIManager
from src.utils.project_config import ProjectConfig

# Set up rich console and logging
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, show_path=False)]
)
logger = logging.getLogger("auto_agent")

class CLIManager:
    """Manages the CLI interface and user interactions"""
    
    def __init__(self):
        self.ui = UIManager()
        self.agent: Optional[MetaAgent] = None
        self.progress = None
        self.task_id = None
        self.main_menu_items = {
            "🆕 Create New Project": self.handle_new_project,
            "🔨 Build/Update Project": self.handle_build_project,
            "📊 Project Status": self.display_agent_status,
            "👋 Exit": lambda: False
        }
        
        # Define project types with descriptions
        self.project_types = [
            questionary.Choice("🌟 Full Stack (Next.js + API) - Complete web application with frontend and backend", "fullstack"),
            questionary.Choice("🎨 Frontend Only (React) - Client-side application with modern UI", "frontend"),
            questionary.Choice("⚙️ Backend Only (Node.js) - API server with database integration", "backend"),
            questionary.Choice("📱 Mobile-First Web App - Responsive design optimized for mobile", "mobile"),
            questionary.Choice("🛠️ Admin Dashboard - Management interface with data visualization", "admin"),
            questionary.Choice("🏪 E-commerce Site - Online store with product management", "ecommerce"),
            questionary.Choice("📝 Blog Platform - Content management system", "blog"),
            questionary.Choice("🎮 Interactive Application - Rich user interactions and animations", "interactive")
        ]

        # Define common project features with auto-selection based on project type
        self.feature_options = {
            "auth": questionary.Choice("🔐 User Authentication (Login/Register)", "auth"),
            "database": questionary.Choice("💾 Database Integration", "database"),
            "ui": questionary.Choice("🎨 Modern UI Components", "ui"),
            "api": questionary.Choice("🔄 API Endpoints", "api"),
            "responsive": questionary.Choice("📱 Responsive Design", "responsive"),
            "dark_mode": questionary.Choice("🌙 Dark Mode Support", "dark_mode"),
            "search": questionary.Choice("🔍 Search Functionality", "search"),
            "charts": questionary.Choice("📊 Data Visualization", "charts"),
            "file_upload": questionary.Choice("📁 File Upload", "file_upload"),
            "social": questionary.Choice("🌐 Social Media Integration", "social"),
            "email": questionary.Choice("📧 Email Notifications", "email"),
            "rbac": questionary.Choice("🔒 Role-based Access Control", "rbac"),
            "pwa": questionary.Choice("📱 Progressive Web App (PWA)", "pwa"),
            "i18n": questionary.Choice("🌍 Internationalization (i18n)", "i18n"),
            "testing": questionary.Choice("🧪 Testing Setup", "testing")
        }

        # Define styling preferences with auto-selection based on project type
        self.styling_options = {
            "tailwind": questionary.Choice("🎨 Tailwind CSS (Utility-first CSS)", "tailwind"),
            "styled-components": questionary.Choice("💅 Styled Components (CSS-in-JS)", "styled-components"),
            "sass": questionary.Choice("📝 SASS/SCSS (CSS with superpowers)", "sass"),
            "css-modules": questionary.Choice("🔄 CSS Modules (Scoped CSS)", "css-modules"),
            "mui": questionary.Choice("🎯 Material UI (Component library)", "mui"),
            "chakra": questionary.Choice("⚡ Chakra UI (Component library)", "chakra")
        }

        # Define automatic feature selection based on project type
        self.auto_features = {
            "fullstack": ["auth", "database", "ui", "api", "responsive", "testing"],
            "frontend": ["ui", "responsive", "dark_mode", "testing"],
            "backend": ["auth", "database", "api", "rbac", "testing"],
            "mobile": ["ui", "responsive", "pwa", "dark_mode", "testing"],
            "admin": ["auth", "database", "ui", "api", "charts", "rbac", "testing"],
            "ecommerce": ["auth", "database", "ui", "api", "file_upload", "search", "testing"],
            "blog": ["auth", "database", "ui", "api", "search", "testing"],
            "interactive": ["ui", "responsive", "dark_mode", "testing"]
        }

        # Define automatic styling selection based on project type
        self.auto_styling = {
            "fullstack": "tailwind",
            "frontend": "styled-components",
            "backend": None,
            "mobile": "tailwind",
            "admin": "mui",
            "ecommerce": "tailwind",
            "blog": "tailwind",
            "interactive": "styled-components"
        }
        
    def display_welcome(self):
        """Display welcome message"""
        console.print(Panel.fit(
            "[bold blue]Welcome to Auto Agent[/bold blue]\n"
            "Your AI-powered development assistant",
            border_style="blue",
            title="🤖 Auto Agent"
        ))

    async def prompt_with_back(self, question_func) -> Tuple[Optional[str], bool]:
        """Wrapper for questions that adds Back/Cancel options"""
        while True:
            answer = await question_func()
            if answer == "<< Back":
                return None, True
            elif answer == "Cancel":
                return None, False
            return answer, True

    def start_progress(self, description: str) -> None:
        """Start a new progress indicator"""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        )
        self.progress.start()
        self.task_id = self.progress.add_task(description, total=100)

    def update_progress(self, description: str, advance: float = None) -> None:
        """Update progress with new description and percentage"""
        if self.progress and self.task_id is not None:
            update_kwargs = {"description": description}
            if advance is not None:
                update_kwargs["advance"] = advance
            self.progress.update(self.task_id, **update_kwargs)

    def stop_progress(self) -> None:
        """Stop the progress indicator"""
        if self.progress:
            self.progress.stop()
            self.progress = None
            self.task_id = None

    async def handle_new_project(self) -> bool:
        """Handle new project creation"""
        try:
            while True:  # Loop to allow retrying with a different name
                # Get project name
                project_name, should_continue = await self.prompt_with_back(
                    lambda: questionary.text(
                        "Project name:",
                        validate=lambda text: len(text) >= 3 and all(c.isalnum() or c in '-_' for c in text),
                        instruction="(Press Enter when done. Min 3 chars, letters, numbers, - and _ only)"
                    ).ask_async()
                )
                if not should_continue:
                    return True
                if not project_name:
                    continue

                # Get project purpose/description
                project_purpose, should_continue = await self.prompt_with_back(
                    lambda: questionary.text(
                        "What would you like to build? Describe your project:",
                        instruction="(e.g., 'A music player website with playlist management and audio visualization')"
                    ).ask_async()
                )
                if not should_continue:
                    return True
                if not project_purpose:
                    continue

                # Get project location
                default_location = str(Path.cwd())
                location_type, should_continue = await self.prompt_with_back(
                    lambda: questionary.select(
                        "Where would you like to create the project?",
                        choices=[
                            questionary.Choice(f"Current directory ({default_location})", default_location),
                            questionary.Choice("Inside Auto Agent directory", "agent"),
                            questionary.Choice("Choose different location", "custom"),
                            questionary.Choice("<< Back", "back"),
                            questionary.Choice("Cancel", "cancel")
                        ],
                        style=Style([
                            ('qmark', 'fg:cyan bold'),
                            ('question', 'bold'),
                            ('answer', 'fg:cyan bold'),
                            ('pointer', 'fg:cyan bold'),
                            ('highlighted', 'fg:cyan bold'),
                        ])
                    ).ask_async()
                )
                if not should_continue:
                    return True
                if not location_type:
                    continue

                project_location = None
                if location_type == "custom":
                    project_location, should_continue = await self.prompt_with_back(
                        lambda: questionary.path(
                            "Enter the directory path:",
                            default=str(Path.home() / "Desktop"),
                            validate=lambda p: Path(p).exists(),
                            only_directories=True
                        ).ask_async()
                    )
                    if not should_continue:
                        return True
                    if not project_location:
                        continue
                else:
                    project_location = location_type

                # Get project type with descriptions
                project_type, should_continue = await self.prompt_with_back(
                    lambda: questionary.select(
                        "What type of project would you like to create?",
                        choices=[*self.project_types, questionary.Choice("<< Back", "back"), questionary.Choice("Cancel", "cancel")],
                        style=Style([
                            ('qmark', 'fg:cyan bold'),
                            ('question', 'bold'),
                            ('answer', 'fg:cyan bold'),
                            ('pointer', 'fg:cyan bold'),
                            ('highlighted', 'fg:cyan bold'),
                        ])
                    ).ask_async()
                )
                if not should_continue:
                    return True
                if not project_type:
                    continue

                # Auto-select features based on project type but allow customization
                default_features = self.auto_features.get(project_type, [])
                feature_choices = [
                    questionary.Choice(
                        f"{self.feature_options[feature].title} {'[Auto-selected]' if feature in default_features else ''}",
                        feature,
                        checked=feature in default_features
                    ) for feature in self.feature_options.keys()
                ]

                selected_features, should_continue = await self.prompt_with_back(
                    lambda: questionary.checkbox(
                        "Confirm or modify the selected features:",
                        choices=[*feature_choices, questionary.Choice("<< Back", "back"), questionary.Choice("Cancel", "cancel")],
                        style=Style([
                            ('qmark', 'fg:cyan bold'),
                            ('question', 'bold'),
                            ('answer', 'fg:cyan bold'),
                            ('pointer', 'fg:cyan bold'),
                            ('highlighted', 'fg:cyan bold'),
                            ('checked', 'fg:green'),
                        ])
                    ).ask_async()
                )
                if not should_continue:
                    return True
                if not selected_features:
                    continue

                # Auto-select styling based on project type but allow override
                default_styling = self.auto_styling.get(project_type)
                if default_styling:
                    styling_message = f"Confirm the recommended styling solution (based on project type):"
                    styling_default = default_styling
                else:
                    styling_message = "Select your preferred styling solution:"
                    styling_default = None

                styling, should_continue = await self.prompt_with_back(
                    lambda: questionary.select(
                        styling_message,
                        choices=[
                            *[
                                questionary.Choice(
                                    f"{choice.title} {'[Recommended]' if choice.value == default_styling else ''}",
                                    choice.value
                                ) for choice in self.styling_options.values()
                            ],
                            questionary.Choice("<< Back", "back"),
                            questionary.Choice("Cancel", "cancel")
                        ],
                        default=styling_default,
                        style=Style([
                            ('qmark', 'fg:cyan bold'),
                            ('question', 'bold'),
                            ('answer', 'fg:cyan bold'),
                            ('pointer', 'fg:cyan bold'),
                            ('highlighted', 'fg:cyan bold'),
                        ])
                    ).ask_async()
                )
                if not should_continue:
                    return True
                if not styling:
                    continue

                # Create project configuration
                config = ProjectConfig(
                    name=project_name,
                    project_type=project_type,
                    description=project_purpose,
                    project_location=project_location,
                    features=selected_features,
                    styling=styling
                )

                # Initialize agent if needed
                if not self.agent:
                    self.agent = MetaAgent()

                # Start progress display with initial status
                self.start_progress("Initializing project creation...")

                try:
                    # Subscribe to progress updates from the agent
                    def progress_callback(status: str, percentage: float):
                        self.update_progress(status, percentage - self.progress.tasks[self.task_id].completed)

                    # Register the callback with the agent's progress tracker
                    self.agent.progress_tracker.register_callback(progress_callback)
                    
                    # Initialize the project
                    await self.agent.initialize_project(config)
                    
                    self.update_progress("Project created successfully!", 100)
                    console.print("[green]✓[/green] Project created successfully!")
                    return True

                except Exception as e:
                    self.stop_progress()
                    error_msg = str(e)
                    console.print(f"[red]Error creating project:[/red] {error_msg}")
                    retry = await questionary.confirm("Would you like to try again?").ask_async()
                    return retry

        except Exception as e:
            self.stop_progress()
            console.print(f"[red]Error:[/red] {str(e)}")
            return False

        finally:
            if self.agent and self.agent.progress_tracker:
                self.agent.progress_tracker.unregister_callback(progress_callback)
            self.stop_progress()

    async def handle_build_project(self) -> bool:
        """Handle project building/updating"""
        if not self.agent:
            console.print("[red]No active project. Please create a new project first.[/red]")
            return True
            
        try:
            description = await questionary.text(
                "What would you like to add or modify in the project?",
                style=Style([
                    ('qmark', 'fg:cyan bold'),
                    ('question', 'bold'),
                    ('answer', 'fg:cyan bold'),
                ])
            ).ask_async()
            
            if description:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task("Processing request...", total=None)
                    try:
                        await self.agent.process_user_input(description)
                        progress.update(task, description="Request processed successfully!")
                    except Exception as e:
                        progress.update(task, description=f"Error: {str(e)}")
                        console.print(f"[red]Error processing request: {str(e)}[/red]")
                        logging.exception("Request processing failed")
            
            return True
            
        except Exception as e:
            console.print(f"[red]Error during build: {str(e)}[/red]")
            logging.exception("Build failed")
            return True

    def display_agent_status(self) -> bool:
        """Display current agent status"""
        if not self.agent:
            console.print("[yellow]No active project. Use 'Create New Project' to get started.[/yellow]")
            return True
            
        if not self.agent.current_project:
            console.print("[yellow]No active project configuration.[/yellow]")
            return True

        status_panel = Panel(
            f"[bold]Project:[/bold] {self.agent.current_project.name}\n"
            f"[bold]Framework:[/bold] {self.agent.current_project.framework}\n"
            f"[bold]Status:[/bold] {self.agent.progress_tracker.current_status if self.agent.progress_tracker else 'Not started'}\n",
            title="🤖 Project Status",
            border_style="blue"
        )
        console.print(status_panel)
        return True

    def log_info(self, message: str) -> None:
        """Log info message with clean formatting"""
        logger.info(f"[blue]•[/blue] {message}")

    def log_error(self, message: str) -> None:
        """Log error message with clean formatting"""
        logger.error(f"[red]✗[/red] {message}")

    def log_success(self, message: str) -> None:
        """Log success message with clean formatting"""
        logger.info(f"[green]✓[/green] {message}")

    def log_warning(self, message: str) -> None:
        """Log warning message with clean formatting"""
        logger.warning(f"[yellow]![/yellow] {message}")

    async def display_main_menu(self) -> bool:
        """Display the main menu"""
        self.display_welcome()
        
        try:
            choice = await questionary.select(
                "Select an option:",
                choices=list(self.main_menu_items.keys()),
                style=Style([
                    ('qmark', 'fg:cyan bold'),
                    ('question', 'bold'),
                    ('answer', 'fg:cyan bold'),
                    ('pointer', 'fg:cyan bold'),
                    ('highlighted', 'fg:cyan bold'),
                ])
            ).ask_async()

            if choice == "👋 Exit":
                return False

            handler = self.main_menu_items[choice]
            return await handler()

        except Exception as e:
            self.log_error(f"An error occurred: {str(e)}")
            return False

    async def start(self) -> None:
        """Start the CLI interface"""
        while True:
            try:
                should_continue = await self.display_main_menu()
                if not should_continue:
                    console.print("👋 Goodbye!")
                    break
            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'Exit' option to quit.[/yellow]")
                continue
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
                logging.exception("Error in main menu")
                break

async def run_cli(debug: bool = False, output_dir: str = "./projects"):
    """Run the CLI application"""
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
        
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    cli_manager = CLIManager()
    await cli_manager.start()

@click.command()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--output-dir', default="./projects", help='Output directory for generated projects')
def main(debug: bool, output_dir: str):
    """Auto Agent - Your AI-powered development assistant"""
    asyncio.run(run_cli(debug, output_dir))
    
if __name__ == "__main__":
    main() 