from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langgraph.graph.state import CompiledStateGraph
from langgraph.graph import START, END, StateGraph
from langgraph.types import RetryPolicy
from app.internal.agent.utils.states.executor import (
    ExecutorAgentOutputSchema,
    ExecutorAgentSchema,
    ExecutorOutputSchema,
    ShouldPlanSchema,
    PlannerOutputSchema,
    TaskListSchema,
)
from app.internal.agent.utils.nodes.executor_agent.planner import (
    should_plan,
    planner_node,
)
from app.internal.agent.utils.nodes.executor_agent.tool import (
    tool_node,
    structure_tool_context,
)
from app.internal.agent.utils.nodes.executor_agent.executor import (
    executor,
    task_tracker,
    should_continue,
)
from app.internal.agent.utils.nodes.executor_agent.aggregator import (
    aggregate,
    irrelvant_query,
)
from app.internal.agent.utils.custom.agent_tools import AgentTools


class ExecutionAgent:
    def __init__(
        self,
        llm: ChatGroq | ChatOllama | ChatGoogleGenerativeAI,
        tool_caller: AgentTools,
    ):
        self.retries = 3
        self.tool_caller = tool_caller
        self.should_plan_llm = llm.with_structured_output(
            ShouldPlanSchema, method="json_schema"
        )
        self.planner_llm = llm.with_structured_output(
            PlannerOutputSchema, method="json_schema"
        )
        self.execution_llm = llm.with_structured_output(
            ExecutorOutputSchema, method="json_schema"
        )
        self.task_list_llm = llm.with_structured_output(
            TaskListSchema, method="json_schema"
        )
        self.aggregator_llm = llm  # No structured output to support streaming
        self.agent_graph: CompiledStateGraph = self._build_agent()

    def _build_agent(self):
        """Method to build agent"""
        try:
            if not self.planner_llm:
                raise Exception("Agent initialization Incomplete!")

            builder = StateGraph(
                state_schema=ExecutorAgentSchema,
                output_schema=ExecutorAgentOutputSchema,
            )

            builder.add_node(
                "planner_node",
                planner_node(self),
                retry_policy=RetryPolicy(
                    max_attempts=self.retries, initial_interval=1.0, backoff_factor=2.0
                ),  # 5 second delay per node retry
            )

            builder.add_node(
                "irrelvant_query",
                irrelvant_query(self),
                retry_policy=RetryPolicy(
                    max_attempts=self.retries, initial_interval=1.0, backoff_factor=2.0
                ),  # 5 second delay per node retry
            )

            builder.add_node(
                "tool_node",
                tool_node(self),
                retry_policy=RetryPolicy(
                    max_attempts=self.retries, initial_interval=1.0, backoff_factor=2.0
                ),  # 5 second delay per node retry
            )

            builder.add_node(
                "structure_tool_context",
                structure_tool_context(self),
                retry_policy=RetryPolicy(
                    max_attempts=self.retries, initial_interval=1.0, backoff_factor=2.0
                ),  # 5 second delay per node retry
            )

            builder.add_node(
                "executor",
                executor(self),
                retry_policy=RetryPolicy(
                    max_attempts=self.retries, initial_interval=1.0, backoff_factor=2.0
                ),  # 5 second delay per node retry
            )

            builder.add_node(
                "task_tracker",
                task_tracker(self),
                retry_policy=RetryPolicy(
                    max_attempts=self.retries, initial_interval=1.0, backoff_factor=2.0
                ),  # 5 second delay per node retry
            )

            builder.add_node(
                "aggregate",
                aggregate(self),
                retry_policy=RetryPolicy(
                    max_attempts=self.retries, initial_interval=1.0, backoff_factor=2.0
                ),  # 5 second delay per node retry
            )

            builder.add_conditional_edges(
                START,
                should_plan(self),
                {"planner_node": "planner_node", "irrelvant_query": "irrelvant_query"},
            )
            builder.add_edge("planner_node", "tool_node")
            builder.add_edge("tool_node", "structure_tool_context")
            builder.add_edge("structure_tool_context", "executor")
            builder.add_edge("executor", "task_tracker")
            builder.add_conditional_edges(
                "task_tracker",
                should_continue(self),
                {
                    "structure_tool_context": "structure_tool_context",
                    "aggregate": "aggregate",
                },
            )
            builder.add_edge("irrelvant_query", END)
            builder.add_edge("aggregate", END)

            graph = builder.compile()

            return graph

        except Exception as e:
            raise e
