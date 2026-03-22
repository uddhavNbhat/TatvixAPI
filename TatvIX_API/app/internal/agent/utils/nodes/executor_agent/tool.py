from typing import List
from app.internal.agent.utils.states.executor import (
    ExecutorAgentSchema,
    ToolOutputSchema,
    DocumentOutputSchema,
    ToolOutput,
)
from app.internal.agent.utils.custom.wrapper import make_async_node, make_node
from app.internal.agent.utils.custom.agent_class import ExecutorAgentStructure
import json


@make_async_node
async def tool_node(
    self: ExecutorAgentStructure, state: ExecutorAgentSchema
) -> ExecutorAgentSchema:
    """Tool node to make all the tool calls and store them in agent state"""
    tasks = state.get("tasks", [])
    if not tasks:
        return {"tool_outputs": [], "document_output": [], "index": 0}
    tool_outputs: List[ToolOutputSchema] = []
    document_data: List[DocumentOutputSchema] = []
    try:
        for instance in tasks:
            if instance.tool_call in self.tool_caller.current_tools:
                if instance.tool_call == "document_search":
                    print("Calling document search tool....")
                    raw_tool_output, _ = await self.tool_caller.call_tool(
                        tool_name=instance.tool_call, query=instance.enhanced_query
                    )

                    parsed_tool_output = json.loads(raw_tool_output)

                    file_ids = parsed_tool_output.get("file_id", [])
                    page_nos = parsed_tool_output.get("page_no", [])
                    text = parsed_tool_output.get("text", "")

                    for file_id, page_no in zip(file_ids, page_nos):
                        # Append meta data to document data object seperately
                        document_data.append(
                            DocumentOutputSchema(file_id=file_id, page_no=page_no)
                        )
                    # Append to tool output list accordingly
                    tool_outputs.append(
                        ToolOutputSchema(
                            enhanced_user_query=instance.enhanced_query,
                            tool_output=ToolOutput(
                                tool_name="document_search", data=text
                            ),
                        )
                    )

                if instance.tool_call == "search_engine":
                    print("Calling search engine tool....")
                    raw_tool_output, _ = await self.tool_caller.call_tool(
                        tool_name=instance.tool_call, query=instance.enhanced_query
                    )  # Take raw string here as there is no data that needs to be extracted explicitly
                    tool_outputs.append(
                        ToolOutputSchema(
                            enhanced_user_query=instance.enhanced_query,
                            tool_output=ToolOutput(
                                tool_name="search_engine", data=raw_tool_output
                            ),
                        )
                    )

        print(tool_outputs)

        return {
            "tool_outputs": tool_outputs,
            "document_output": document_data,
            "index": 0,
        }
    except Exception as e:
        raise e


@make_node
def structure_tool_context(
    self: ExecutorAgentStructure, state: ExecutorAgentSchema
) -> ExecutorAgentSchema:
    """Node to aggregate tool content in slices to pass to the executor node to get the final results"""
    tool_outputs = state.get("tool_outputs", [])
    index = state.get("index", 0)

    if index >= len(tool_outputs):
        return {"context": "", "index": index}

    try:
        tool_output = tool_outputs[index]
        tool_data = tool_output.tool_output.data
        if isinstance(tool_data, list):
            context = ";\n".join(tool_data)

        if isinstance(tool_data, str):
            context = tool_data

        return {"context": context, "index": index + 1}

    except Exception as e:
        raise e
