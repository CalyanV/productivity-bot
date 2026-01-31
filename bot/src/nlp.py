from datetime import datetime
from typing import Dict, List, Optional
import logging
from .llm_client import LLMClient
from .models import ParsedTask, TimeEstimate

logger = logging.getLogger(__name__)


class TaskParser:
    """Parse natural language task input using LLM"""

    def __init__(self, api_key: str):
        self.llm = LLMClient(api_key=api_key)

    async def parse_task(
        self,
        user_input: str,
        context: Dict
    ) -> ParsedTask:
        """
        Parse natural language into structured task

        Args:
            user_input: Raw text from user
            context: Available projects, people, today's date

        Returns:
            ParsedTask with structured data
        """
        today = datetime.now().strftime('%Y-%m-%d')

        # Build context string
        context_str = f"Today's date: {today}\n"

        if context.get('projects'):
            projects = [p['title'] for p in context['projects']]
            context_str += f"Available projects: {', '.join(projects)}\n"

        if context.get('people'):
            people = [p['name'] for p in context['people']]
            context_str += f"Known people: {', '.join(people)}\n"

        # Create prompt
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a task parsing assistant. Extract structured data "
                    "from natural language task descriptions. Parse relative dates "
                    "like 'tomorrow', 'next Friday' into YYYY-MM-DD format. "
                    "Infer people, projects, and tags from context."
                )
            },
            {
                "role": "user",
                "content": f"{context_str}\nTask: {user_input}"
            }
        ]

        # Call LLM with structured output
        result = await self.llm.complete(
            response_model=ParsedTask,
            messages=messages
        )

        logger.info(f"Parsed task: {result.title}")
        return result

    async def estimate_time(
        self,
        task_title: str,
        task_context: Optional[str] = None,
        historical_data: Optional[List[Dict]] = None
    ) -> TimeEstimate:
        """
        Estimate task time using LLM

        Args:
            task_title: Task description
            task_context: Additional context
            historical_data: Similar past tasks with actual times

        Returns:
            TimeEstimate with estimate and reasoning
        """
        # Build prompt with historical data
        history_text = ""
        if historical_data:
            history_text = "Similar past tasks:\n"
            for task in historical_data[-10:]:
                history_text += (
                    f"- '{task['title']}': "
                    f"estimated {task['estimate']}min, "
                    f"actual {task['actual']}min\n"
                )
        else:
            history_text = "No historical data available"

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a time estimation assistant. Estimate how long "
                    "tasks will take based on their description and historical "
                    "data. Be realistic and account for complexity."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Task: {task_title}\n"
                    f"Context: {task_context or 'None'}\n\n"
                    f"{history_text}\n\n"
                    "Provide time estimate, confidence level, reasoning, "
                    "and a helpful suggestion for the user."
                )
            }
        ]

        # Use fallback model (Claude) for time estimation
        # as it requires better reasoning
        result = await self.llm.complete(
            response_model=TimeEstimate,
            messages=messages,
            use_fallback=True  # Use Claude for complex reasoning
        )

        logger.info(
            f"Estimated {result.estimate_minutes}min "
            f"with {result.confidence} confidence"
        )
        return result
