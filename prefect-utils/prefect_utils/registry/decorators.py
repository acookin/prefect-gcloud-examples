import functools

from datadog import api
from prefect.context import get_run_context


def datadog_event(fn):
    # decorator that will pust datadog events at the beginning and end of
    # each flow run
    @functools.wraps(fn)
    def decorated(*args, **kwargs):
        context = get_run_context()
        flow_name = context.flow.name
        api.Event.create(
            title="Flow Started",
            text=f"flow run for {flow_name} started",
            tags=[f"flow:{flow_name}"],
        )
        try:
            ret = fn(*args, **kwargs)
        except Exception as e:
            api.Event.create(
                title="Flow Errored",
                text=f"flow run for {flow_name} errored",
                tags=[f"flow:{flow_name}"],
            )
            raise

        api.Event.create(
            title="Flow Completed",
            text=f"flow run for {flow_name} completed",
            tags=[f"flow:{flow_name}"],
        )

        return ret

    return decorated
