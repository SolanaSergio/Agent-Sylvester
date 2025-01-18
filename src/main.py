from src.agents.meta_agent import MetaAgent
from src.utils.types import AgentStatus
from src.managers.ui_manager import UIManager
from src.utils.project_structure import ProjectStructure
import click
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@click.command()
@click.option('--goal', default="Learn and evolve", help='Initial goal for the agent')
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--output-dir', default="./projects", help='Output directory for generated projects')
def main(goal: str, debug: bool, output_dir: str):
    """Autonomous Agent Development Studio"""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        
    ui = UIManager()
    agent = MetaAgent(goal)
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    async def run_agent():
        try:
            ui.display_welcome()
            
            while True:
                try:
                    # Get user input
                    user_input = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: ui.prompt_user("Enter your request (or 'exit' to quit)")
                    )
                    
                    if user_input.lower() in ['exit', 'quit']:
                        ui.display_status("Goodbye! 👋", "success")
                        break
                    
                    # Process the input
                    await agent.process_user_input(user_input)
                    
                except KeyboardInterrupt:
                    ui.display_status("\nInterrupted by user. Goodbye! 👋", "warning")
                    break
                except Exception as e:
                    ui.display_error(f"Error: {str(e)}")
                    logging.exception("Error processing user input")
                    ui.display_status("Please try again or type 'exit' to quit", "warning")
        finally:
            # Cleanup resources
            await agent.cleanup()

    # Run the agent
    asyncio.run(run_agent())

if __name__ == "__main__":
    main() 