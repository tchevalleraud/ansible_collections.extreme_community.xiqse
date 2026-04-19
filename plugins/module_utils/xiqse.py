import json

import requests
import urllib3


def _to_gql_literal(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return json.dumps(value)
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, list):
        return "[" + ", ".join(_to_gql_literal(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{" + ", ".join(f"{key}: {_to_gql_literal(val)}" for key, val in value.items()) + "}"
    raise TypeError(f"Unsupported type for GraphQL literal: {type(value).__name__}")

class XIQSE:
    def __init__(self, host, client_id, client_secret, port=8443, protocol="https", validate_certs=True, timeout=30):
        self.host           = host
        self.client_id      = client_id
        self.client_secret  = client_secret
        self.port           = port
        self.protocol       = protocol
        self.validate_certs = validate_certs
        self.timeout        = timeout
        self.token          = None

        if not self.validate_certs:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def base_url(self):
        return f"{self.protocol}://{self.host}:{self.port}"

    def authenticate(self):
        token_url   = f"{self.base_url()}/oauth/token/access-token?grant_type=client_credentials"
        headers     = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            response = requests.post(
                token_url,
                auth=(self.client_id, self.client_secret),
                headers=headers,
                verify=self.validate_certs,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()

            if "access_token" in result:
                self.token = result["access_token"]
                return self.token
            else:
                raise Exception("Authentication failed: No access_token in response")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Auth request failed: {e}")

    def graphql(self, query, variables=None):
        if self.token is None:
            self.authenticate()

        if variables is None:
            variables = {}

        url = f"{self.base_url()}/nbi/graphql"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                url,
                json={"query": query, "variables": variables},
                headers=headers,
                timeout=self.timeout,
                verify=self.validate_certs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"GraphQL request failed: {e}")

    class mutation:
        @staticmethod
        def network_addDevice():
          return """
          mutation Device($deviceIp: String!, $profileName: String!, $sitePath: String!) {
            network	{
              createDevices(input: {
                devices: {
                  ipAddress: $deviceIp
                  profileName: $profileName
                  siteLocation: $sitePath
                }
              }){
                results {
                  deviceId
                  ipAddress
                  message
                  serialNumber
                  status
                }
              }
            }
          }
          """

        @staticmethod
        def network_enforceAllDevices():
          return """
            mutation Device($ipAddress: String!) {
              network	{
                configureDevice(input: {
                  enforceAll: true
                  deviceConfig: {
                    ipAddress: $ipAddress
                  }
                }){
                  status
                }
              }
            }          
          """

        @staticmethod
        def network_createSite():
          return """
            mutation Site($sitePath: String!) {
              network {
                createSite(input: {
                  siteLocation: $sitePath
                }) {
                  errorCode
                  siteId
                  siteLocation
                  status
                }
              }
            }
          """

        @staticmethod
        def network_deleteSite():
          return """
            mutation Site($sitePath: String!) {
              network {
                deleteSite(input: {
                  siteLocation: $sitePath
                }) {
                  errorCode
                  siteId
                  siteLocation
                  status
                }
              }
            }
          """

        @staticmethod
        def workflows_startWorkflow(path, variables=None):
            path_literal        = json.dumps(path)
            variables_literal   = _to_gql_literal(variables or {})
            return f"""
            mutation {{
              workflows {{
                startWorkflow(input: {{
                  path: {path_literal}
                  variables: {variables_literal}
                }}){{
                  executionId
                  message
                  operationId
                  status
                }}
              }}
            }}
            """

        @staticmethod
        def network_readDevices():
            return """
            mutation DeviceRead($ipAddress: String!) {
              network {
                readDevices(input: {
                  devices: {
                    ipAddress: $ipAddress
                  }
                }){
                  errorCode
                  status
                }
              }
            }
          """

    class query:
        
        class administration:

            @staticmethod
            def serverInfo():
              return """
                query {
                  administration {
                    serverInfo {
                      uptime
                      version
                    }
                  }
                }
              """

            @staticmethod
            def serverInfo_version():
              return """
                query {
                  administration {
                    serverInfo {
                      version
                    }
                  }
                }
              """

        class network:
          
          @staticmethod
          def devices():
            return """
              query {
                network {
                  devices {
                    ip
                    sysName
                    sitePath
                  }
                }
              }
            """

          @staticmethod
          def sites():
            return """
              query {
                network {
                  sites {
                    location
                    siteName
                  }
                }
              }
            """

          class device:
            
            @staticmethod
            def byIp():
              return """
                query Device($ipAddress: String!) {
                  network {
                    device(ip: $ipAddress){
                      firmware
                      ip
                      sysName
                      sitePath
                    }
                  }
                }
              """

            @staticmethod
            def getFirmware():
              return """
                query Device($ipAddress: String!) {
                  network {
                    device(ip: $ipAddress){
                      firmware
                    }
                  }
                }
              """

          class site:
            @staticmethod
            def byLocation():
              return """
                query Site($sitePath: String!) {
                  network {
                    siteByLocation(location: $sitePath){
                      location
                      siteName
                    }
                  }
                }
              """

        class workflows:

          @staticmethod
          def execution():
            return """
              query Workflow($executionId: Long!) {
                workflows {
                  execution(executionId: $executionId) {
                    status
                  }
                }
              }
            """


    class params:
        @staticmethod
        def get_ipAddress():
            return dict(type="str", required=True)

        @staticmethod
        def get_mutation():
            return dict(type="str", required=True)
        
        @staticmethod
        def get_profile_name():
            return dict(type="str", required=True)

        @staticmethod
        def get_provider():
            return dict(
                type="dict", required=True, options=dict(
                    protocol=dict(type="str", required=False, default="https"),
                    host=dict(type="str", required=True),
                    port=dict(type="int", required=False, default=8443),
                    client_id=dict(type="str", required=True, no_log=True),
                    client_secret=dict(type="str", required=True, no_log=True),
                    verify=dict(type="bool", required=False, default=True),
                )
            )

        @staticmethod
        def get_query():
            return dict(type="str", required=True)

        @staticmethod
        def get_sitePath():
            return dict(type="str", required=True)

        @staticmethod
        def get_state():
            return dict(
                type="str",
                choices=["present", "absent", "replaced", "merged", "deleted", "gathered"],
                default="gathered"
            )

        @staticmethod
        def get_state_bool():
            return dict(
                type="str",
                choices=["present", "absent", "gathered"],
                default="gathered"
            )

        @staticmethod
        def get_state_status():
            return dict(
                type="str",
                choices=["enabled", "disabled", "gathered"],
                default="gathered"
            )

        @staticmethod
        def get_timeout():
            return dict(type="int", required=False, default=30)

        @staticmethod
        def get_workflow_path():
            return dict(type="str", required=True)

        @staticmethod
        def get_workflow_variables():
            return dict(type="dict", required=False, default={})

        @staticmethod
        def get_wait():
            return dict(type="bool", required=False, default=True)

        @staticmethod
        def get_poll_interval():
            return dict(type="int", required=False, default=5)

        @staticmethod
        def get_poll_timeout():
            return dict(type="int", required=False, default=600)
