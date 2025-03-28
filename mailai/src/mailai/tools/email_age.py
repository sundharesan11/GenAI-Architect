from datetime import datetime, date
from typing import Optional, Union, Tuple
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import time

class EmailAgeSchema(BaseModel):
    """Schema for the EmailAgeTool."""
    email_date: str = Field(
        ...,
        description="The date of the email in 'YYYY-MM-DD' format."
    )

class EmailAgeTool(BaseTool):
    """Tool to calculate the age of an email."""

    name: str = "email_age"
    description: str = "Calculate the age of an email from its date."
    schema: EmailAgeSchema = EmailAgeSchema

    def _run(self, email_date: str) -> Union[int, Tuple[int, int]]:
        """Calculate the age of the email."""
        try:
            # Parse the email date
            email_date_obj = datetime.strptime(email_date, "%Y-%m-%d").date()
            # Get today's date
            today = date.today()
            # Calculate the difference in days
            delta = today - email_date_obj
            return delta.days, delta.days // 30  # Return days and months
        except ValueError:
            raise ValueError("Invalid date format. Please use 'YYYY-MM-DD'.")