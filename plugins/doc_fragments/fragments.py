# plugins/doc_fragments/fragments.py
# -*- coding: utf-8 -*-

class ModuleDocFragment:
    OPTIONS_IPADDRESS       = r"""
      options:
        ip_address:
          description:
            - Device IP Address
          type: str
          required: true
    """
    OPTIONS_MUTATION        = r"""
      options:
        mutation:
          description:
            - GraphQL mutation for XIQ-SE
          type: str
          required: true
    """
    OPTIONS_PROVIDER        = r"""
      options:
        provider:
          description:
            - Connection information for accessing the ExtremeCloud IQ - Site Engine (XIQ-SE) API.
          required: true
          type: dict
          suboptions:
            protocol:
              description:
                - Protocol to use for API communication.
              type: str
              default: https
              choices: [http, https]
            host:
              description:
                - IP address or FQDN of the XIQ-SE server.
              type: str
              required: true
            port:
              description:
                - Port to use for API communication.
              type: int
              default: 8443
            client_id:
              description:
                - OAuth2 client ID used for authentication.
              type: str
              required: true
              no_log: true
            client_secret:
              description:
                - OAuth2 secret associated with the client ID.
              type: str
              required: true
              no_log: true
            verify:
              description:
                - Whether to validate the SSL certificate.
              type: bool
              default: true
    """
    OPTIONS_QUERY           = r"""
      options:
        query:
          description:
            - GraphQL query for XIQ-SE
          type: str
          required: true
    """
    OPTIONS_SITE_PATH       = r"""
      options:
        site_path:
          description:
            - Full site path/location in XIQ-SE (e.g. "Global/Region/Site").
          type: str
          required: true
    """
    OPTIONS_STATE           = r"""
      options:
        state:
          description:
            - Desired state of the item.
          type: str
          default: gathered
          choices:
            - present
            - absent
            - replaced
            - merged
            - deleted
            - gathered
    """
    OPTIONS_STATE_BOOL      = r"""
      options:
        state:
          description:
            - Desired state of the item.
          type: str
          default: gathered
          choices:
            - present
            - absent
            - gathered
    """
    OPTIONS_STATE_STATUS    = r"""
      options:
        state:
          description:
            - Desired state of the item.
          type: str
          default: gathered
          choices:
            - enabled
            - disabled
            - gathered
    """
    OPTIONS_TIMEOUT         = r"""
      options:
        timeout:
          description:
            - Connection timeout in seconds.
          type: int
          default: 30
    """
    OPTIONS_WORKFLOW_PATH   = r"""
      options:
        path:
          description:
            - Full path of the workflow in XIQ-SE (e.g. "/Workflows/WF_TEST").
          type: str
          required: true
    """
    OPTIONS_WORKFLOW_VARIABLES = r"""
      options:
        variables:
          description:
            - Variables to pass to the workflow execution.
            - Keys map to the workflow input variable names and values may be scalars or lists.
          type: dict
          required: false
          default: {}
    """
    OPTIONS_WORKFLOW_WAIT   = r"""
      options:
        wait:
          description:
            - Whether to poll the workflow execution until it reaches a terminal status.
          type: bool
          default: true
        poll_interval:
          description:
            - Interval in seconds between two execution status polls.
          type: int
          default: 5
        poll_timeout:
          description:
            - Maximum time in seconds to wait for the workflow execution to reach a terminal status.
          type: int
          default: 600
    """
