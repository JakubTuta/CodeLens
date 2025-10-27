import typing
from typing import List

import ai.ai as ai
import pydantic
import utils.function_utils as function_utils
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate


class ImprovementsList(pydantic.BaseModel):
    improvements: List[str] = pydantic.Field(
        description="List of improvement suggestions for the code"
    )


class Improvements:
    @staticmethod
    async def generate_improvements_from_ai(
        function: typing.Callable,
        api_key: str,
        function_text: typing.Optional[str] = None,
    ) -> typing.List[str]:
        parser = PydanticOutputParser(pydantic_object=ImprovementsList)

        format_instructions = parser.get_format_instructions()

        prompt_template = """
        You are an expert in programming. Your task is to analyze the provided function and suggest improvements. Please provide the suggestions in a clear and concise manner.
        
        {format_instructions}
        
        Focus on:
        - Code efficiency and performance.
        - Readability and maintainability.
        - Best practices and design patterns.
        - Any potential bugs or issues.
        
        Limit your response to maximum 5 suggestions.
        
        IMPORTANT: Your entire response must be a valid JSON object that follows the format specified above.
        
        Function to analyze:
        {function_string}
        """

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["function_string"],
            partial_variables={"format_instructions": format_instructions},
        )

        if function_text:
            function_string = function_text
        else:
            function_string = function_utils.function_to_text(function)

        final_prompt = prompt.format(function_string=function_string)

        response = await ai.send_request_with_auto_detection_async(
            api_key=api_key,
            user_query=function_string,
            system_instructions=final_prompt,
        )

        if not response:
            return []

        response_text = ai.get_text_from_response(response)
        if not response_text:
            return []

        try:
            parsed_response = parser.parse(response_text)
            return parsed_response.improvements

        except Exception as e:
            try:
                improvements_list = ImprovementsList.model_validate_json(response_text)
                return improvements_list.improvements
            except Exception:
                return []
                return []
                return []
                return []
