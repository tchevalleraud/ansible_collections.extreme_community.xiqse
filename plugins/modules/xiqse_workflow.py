#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = r"""
---
module: xiqse_workflow
author:
  - Thibault Chevalleraud (@tchevalleraud)
short_description: Execute and monitor a workflow in XIQ-SE via GraphQL.
description:
  - This module starts a workflow in XIQ-SE using its path and optional input variables.
  - When wait is true, it polls the execution status until a terminal state is reached
    (SUCCESS, COMPLETED, FAILED, CANCELED, TIMEDOUT or SKIPPED) or poll_timeout is reached.
  - It is compatible with ExtremeCloudIQ - Site Engine.
extends_documentation_fragment:
  - extreme_community.xiqse.fragments.OPTIONS_PROVIDER
  - extreme_community.xiqse.fragments.OPTIONS_WORKFLOW_PATH
  - extreme_community.xiqse.fragments.OPTIONS_WORKFLOW_VARIABLES
  - extreme_community.xiqse.fragments.OPTIONS_WORKFLOW_WAIT
  - extreme_community.xiqse.fragments.OPTIONS_TIMEOUT
"""

EXAMPLES = r"""
- name: Start a workflow and wait for its completion
  extreme_community.xiqse.xiqse_workflow:
    path: "/Workflows/WF_TEST"
    variables:
      deviceIP: "10.201.100.41"
      devices:
        - "10.201.100.41"
    wait: true
    poll_interval: 5
    poll_timeout: 300
    provider:
      host: "{{ ansible_host }}"
      client_id: "{{ xiqse_client }}"
      client_secret: "{{ xiqse_secret }}"

- name: Start a workflow without waiting for its completion
  extreme_community.xiqse.xiqse_workflow:
    path: "/Workflows/WF_TEST"
    wait: false
    provider:
      host: "{{ ansible_host }}"
      client_id: "{{ xiqse_client }}"
      client_secret: "{{ xiqse_secret }}"
"""

RETURN = r"""
msg:
  description: Status message indicating the outcome of the operation.
  returned: always
  type: str
  sample: "Workflow /Workflows/WF_TEST finished with status SUCCESS."

changed:
  description: Indicates whether a change has been made.
  returned: always
  type: bool
  sample: true

execution_id:
  description: Identifier of the workflow execution.
  returned: when the workflow has been started
  type: int
  sample: 251

status:
  description: Last known status of the workflow execution.
  returned: always
  type: str
  sample: "SUCCESS"

operation_id:
  description: Operation identifier returned by XIQ-SE when starting the workflow.
  returned: when the workflow has been started
  type: str
  sample: "op-123"

start_message:
  description: Message returned by XIQ-SE when starting the workflow.
  returned: when the workflow has been started
  type: str
  sample: "Workflow started."
"""

import time

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.extreme_community.xiqse.plugins.module_utils.xiqse import XIQSE

TERMINAL_STATUSES   = {"CANCELED", "COMPLETED", "FAILED", "SKIPPED", "SUCCESS", "TIMEDOUT"}
SUCCESS_STATUSES    = {"SUCCESS", "COMPLETED"}


def run_module():
    module_args = dict(
        path            = XIQSE.params.get_workflow_path(),
        variables       = XIQSE.params.get_workflow_variables(),
        provider        = XIQSE.params.get_provider(),
        wait            = XIQSE.params.get_wait(),
        poll_interval   = XIQSE.params.get_poll_interval(),
        poll_timeout    = XIQSE.params.get_poll_timeout(),
        timeout         = XIQSE.params.get_timeout()
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    path            = module.params["path"]
    variables       = module.params["variables"] or {}
    provider        = module.params["provider"]
    wait            = module.params["wait"]
    poll_interval   = module.params["poll_interval"]
    poll_timeout    = module.params["poll_timeout"]
    timeout         = module.params["timeout"]

    if poll_interval < 1:
        module.fail_json(msg="poll_interval must be greater than or equal to 1 second.")

    try:
        xiqse = XIQSE(
            host=provider["host"],
            client_id=provider["client_id"],
            client_secret=provider["client_secret"],
            port=provider["port"],
            protocol=provider["protocol"],
            validate_certs=provider["verify"],
            timeout=timeout
        )

        start_query     = XIQSE.mutation.workflows_startWorkflow(path, variables)
        start_result    = xiqse.graphql(start_query)
        start_data      = start_result.get("data", {}).get("workflows", {}).get("startWorkflow", {}) or {}

        execution_id    = start_data.get("executionId")
        operation_id    = start_data.get("operationId")
        start_status    = start_data.get("status")
        start_message   = start_data.get("message")

        if execution_id is None:
            errors = start_result.get("errors") or start_message or "Unknown error."
            raise Exception(f"Unable to start workflow {path}: {errors}")

        if not wait:
            module.exit_json(
                changed=True,
                msg=f"Workflow {path} started with execution id {execution_id}.",
                execution_id=execution_id,
                operation_id=operation_id,
                status=start_status,
                start_message=start_message
            )

        query_execution = XIQSE.query.workflows.execution()
        deadline        = time.time() + poll_timeout
        current_status  = start_status

        while True:
            poll_result     = xiqse.graphql(query_execution, {"executionId": execution_id})
            execution_info  = poll_result.get("data", {}).get("workflows", {}).get("execution", {}) or {}
            current_status  = execution_info.get("status") or current_status

            if current_status in TERMINAL_STATUSES:
                break

            if time.time() >= deadline:
                module.fail_json(
                    msg=f"Timed out after {poll_timeout}s waiting for workflow {path} (execution {execution_id}); last status: {current_status}.",
                    execution_id=execution_id,
                    operation_id=operation_id,
                    status=current_status,
                    start_message=start_message
                )

            time.sleep(poll_interval)

        if current_status in SUCCESS_STATUSES:
            module.exit_json(
                changed=True,
                msg=f"Workflow {path} finished with status {current_status}.",
                execution_id=execution_id,
                operation_id=operation_id,
                status=current_status,
                start_message=start_message
            )

        if current_status == "SKIPPED":
            module.exit_json(
                changed=False,
                msg=f"Workflow {path} was skipped.",
                execution_id=execution_id,
                operation_id=operation_id,
                status=current_status,
                start_message=start_message
            )

        module.fail_json(
            msg=f"Workflow {path} finished with status {current_status}.",
            execution_id=execution_id,
            operation_id=operation_id,
            status=current_status,
            start_message=start_message
        )

    except Exception as e:
        module.fail_json(msg=str(e))


def main():
    run_module()


if __name__ == '__main__':
    main()
