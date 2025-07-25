import asyncio
import typing

from helpers import ai, function_utils


class Documentation:
    @staticmethod
    async def generate_documentation_from_ai_async(
        function: typing.Callable,
        api_key: str,
        function_text: typing.Optional[str] = None,
    ) -> typing.Optional[str]:
        template = """
        You are an expert in programming. Your task is to generate documentation for the provided function. Please provide the documentation in a clear and concise manner. ONLY return the function with documentation inside it, DO NOT change the code in any way and DO NOT write additional comments.
        The documentation should include:
        - A brief description of what the function does.
        - The parameters of the function, including their types and descriptions.
        - The return type of the function and its description.
        - Any exceptions that the function might raise.
        
        Example function with documentation:
        ```python
        def example_function(param1: int, param2: str) -> bool:
            \"\"\"This function does something useful.
            
            Args:
                param1 (int): The first parameter.
                param2 (str): The second parameter.
            
            Returns:
                bool: True if successful, False otherwise.
            \"\"\"
            return True
        ```
        """

        if function_text:
            function_string = function_text
        else:
            function_string = function_utils.function_to_text(function)

        response = await ai.send_request_with_auto_detection_async(
            api_key=api_key,
            user_query=function_string,
            system_instructions=template,
        )

        if response:
            response_text = ai.get_text_from_response(response)

            if not response_text:
                return None

            lines = response_text.strip().split("\n")
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            joined_text = "\n".join(lines).strip()
            return joined_text

    async def get_docs_async(
        self,
        function: typing.Callable,
        api_key: str,
        function_text: typing.Optional[str] = None,
    ) -> typing.Optional[str]:
        return await self.generate_documentation_from_ai_async(
            function, api_key, function_text
        )
