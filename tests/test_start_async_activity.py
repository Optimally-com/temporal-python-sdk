import pytest
from datetime import timedelta

from temporal.workflow import workflow_method, WorkflowClient, Workflow
from temporal.activity_method import activity_method

TASK_QUEUE = "test_start_async_activity_tq"
NAMESPACE = "default"


class GreetingActivities:
    @activity_method(
        task_queue=TASK_QUEUE, schedule_to_close_timeout=timedelta(seconds=1000)
    )
    async def compose_greeting(self) -> str:
        raise NotImplementedError


class GreetingActivitiesImpl:
    activity_method_executed: bool = False

    async def compose_greeting(self):
        GreetingActivitiesImpl.activity_method_executed = True


class GreetingWorkflow:
    @workflow_method(task_queue=TASK_QUEUE)
    async def get_greeting(self) -> None:
        raise NotImplementedError


class GreetingWorkflowImpl(GreetingWorkflow):
    def __init__(self):
        self.greeting_activities: GreetingActivities = Workflow.new_activity_stub(
            GreetingActivities
        )

    async def get_greeting(self):
        await self.greeting_activities.compose_greeting()


@pytest.mark.asyncio
@pytest.mark.worker_config(
    NAMESPACE,
    TASK_QUEUE,
    activities=[(GreetingActivitiesImpl(), "GreetingActivities")],
    workflows=[GreetingWorkflowImpl],
)
async def test(worker):
    client = WorkflowClient.new_client(namespace=NAMESPACE)
    greeting_workflow: GreetingWorkflow = client.new_workflow_stub(GreetingWorkflow)
    await greeting_workflow.get_greeting()

    assert GreetingActivitiesImpl.activity_method_executed
