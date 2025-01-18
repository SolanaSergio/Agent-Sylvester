import asyncio
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from src.utils.types import ProjectConfig

class CLIManager:
    def __init__(self):
        self.console = Console()
        self._initialize_agent()

    def _initialize_agent(self):
        # Lazy import to avoid circular dependency
        from src.agents.meta_agent import MetaAgent
        self.agent = MetaAgent()

    async def start(self):
        self.console.print(
            Panel(
                "[bold green]Welcome to Auto Agent[/bold green]\n"
                "Your AI-powered development assistant",
                title="🤖 Auto Agent"
            )
        )

        while True:
            choice = await self._get_menu_choice()
            if choice == "exit":
                self.console.print("[green]Goodbye! 👋[/green]")
                break
            
            await self._handle_choice(choice)
            self.console.print("\n" + "─" * 50 + "\n")

    async def _get_menu_choice(self):
        select = questionary.select(
            "Select an option:",
            choices=[
                questionary.Choice("🆕 Create New Project", "new"),
                questionary.Choice("🔄 Import Existing Project", "import"),
                questionary.Choice("🔨 Update Project", "update"),
                questionary.Choice("👋 Exit", "exit"),
            ]
        )
        
        result = await asyncio.get_event_loop().run_in_executor(None, select.ask)
        return result

    async def _handle_choice(self, choice):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            try:
                if choice == "new":
                    await self._handle_new_project(progress)
                elif choice == "import":
                    await self._handle_import_project(progress)
                elif choice == "update":
                    await self._handle_update_project(progress)
            except Exception as e:
                self.console.print(f"[red]Error: {str(e)}[/red]")

    async def _handle_new_project(self, progress):
        task = progress.add_task("[yellow]Setting up new project...", total=None)
        
        try:
            # Get basic project info
            config = await self._get_project_config()
            
            # Let the agent handle the rest
            progress.update(task, description=f"[yellow]Creating project: {config.name}...")
            await self.agent.initialize_project(config)
            
            progress.update(task, description="[green]Project created successfully!")
            self.console.print(f"\n[green]✓[/green] Project [bold]{config.name}[/bold] is ready!")
            
        except Exception as e:
            progress.update(task, description=f"[red]Error: {str(e)}")
            raise

    async def _handle_import_project(self, progress):
        task = progress.add_task("[yellow]Importing project...", total=None)
        
        try:
            # Get project path
            path = await self._get_project_path()
            
            # Let the agent handle the analysis and setup
            progress.update(task, description="[yellow]Analyzing project...")
            await self.agent.import_project(path)
            
            progress.update(task, description="[green]Project imported successfully!")
            
        except Exception as e:
            progress.update(task, description=f"[red]Error: {str(e)}")
            raise

    async def _handle_update_project(self, progress):
        task = progress.add_task("[yellow]Updating project...", total=None)
        
        try:
            # Let the agent handle the update
            progress.update(task, description="[yellow]Analyzing changes...")
            await self.agent.update_project()
            
            progress.update(task, description="[green]Project updated successfully!")
            
        except Exception as e:
            progress.update(task, description=f"[red]Error: {str(e)}")
            raise

    async def _get_project_config(self) -> ProjectConfig:
        """Get basic project configuration from user"""
        name = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: questionary.text("Project name:", validate=lambda x: len(x) >= 1).ask()
        )
        
        description = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: questionary.text("Project description:").ask()
        )
        
        framework = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: questionary.select(
                "Select framework:",
                choices=["Next.js", "React", "Vue", "Angular"]
            ).ask()
        )
        
        return ProjectConfig(
            name=name,
            description=description,
            framework=framework,
            features=[]  # Let the agent determine needed features
        )

    async def _get_project_path(self) -> str:
        """Get path to existing project"""
        return await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: questionary.path("Project path:").ask()
        ) 