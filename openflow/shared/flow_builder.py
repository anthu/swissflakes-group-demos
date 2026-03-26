"""
Base class encapsulating the KuCoin AllTickers v2 pattern for Openflow REST API ingestion.

Each flow script subclasses OpenflowFlowBuilder and overrides:
  - flow_name, param_context_name
  - parameters() -> dict of parameter context values
  - api_url, http_method (defaults to GET)
  - jolt_spec (defaults to {"*":"RAW.&"})
  - schedule_period (defaults to "5 min")
  - build_fetch_chain() for multi-step patterns (STAC, ZIP, etc.)

Session configuration is read from the openflow infrastructure cache file
(~/.snowflake/cortex/memory/openflow_infrastructure_*.json) and the nipyapi
profile specified therein. No hardcoded account, user, or path values.

Uses the nipyapi Python SDK directly (not CLI subprocess calls) since the
builder is multi-step logic that benefits from native object handling.
"""
import glob
import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import nipyapi


def _find_cache_file() -> Path:
    """Find the openflow infrastructure cache file."""
    pattern = os.path.expanduser(
        "~/.snowflake/cortex/memory/openflow_infrastructure_*.json"
    )
    matches = glob.glob(pattern)
    if not matches:
        raise FileNotFoundError(
            "No openflow infrastructure cache found. "
            "Run the openflow skill's session start workflow first."
        )
    # Use most recently modified if multiple exist
    return Path(max(matches, key=os.path.getmtime))


def _load_session() -> dict:
    """Load session config from the openflow infrastructure cache."""
    cache_path = _find_cache_file()
    with open(cache_path) as f:
        cache = json.load(f)

    runtimes = [
        rt
        for dep in cache.get("deployments", [])
        for rt in dep.get("runtimes", [])
    ]
    if not runtimes:
        raise RuntimeError(
            "No runtimes found in openflow cache. "
            "Run the openflow skill's setup workflow first."
        )
    # Use first runtime (single-runtime deployments); callers can override
    runtime = runtimes[0]
    profile = runtime.get("nipyapi_profile")
    if not profile:
        raise RuntimeError(
            "No nipyapi_profile in cache runtime. "
            "Run the openflow skill's setup workflow to create a profile."
        )
    return {
        "connection": cache.get("connection", ""),
        "profile": profile,
        "runtime_name": runtime.get("runtime_name", ""),
    }


# Session state — initialized lazily on first use
_session: Optional[dict] = None


def _get_session() -> dict:
    global _session
    if _session is None:
        _session = _load_session()
    return _session


def get_profile() -> str:
    """Return the nipyapi profile name from the session cache."""
    return _get_session()["profile"]


def activate_session(profile: Optional[str] = None):
    """Activate the nipyapi profile for SDK calls."""
    if profile is None:
        profile = get_profile()
    nipyapi.profiles.switch(profile)


@dataclass
class ProcessorRef:
    id: str
    name: str
    type: str


@dataclass
class FlowComponents:
    pg_id: str
    param_context_id: str
    snowflake_conn_id: str
    web_client_id: str
    processors: dict = field(default_factory=dict)
    funnels: dict = field(default_factory=dict)


class OpenflowFlowBuilder(ABC):

    def __init__(self, *, account: str,
                 role: str = "OPENFLOW_ADMIN", profile: Optional[str] = None):
        """
        Args:
            account: Snowflake account identifier (e.g. from config.yml).
            role: Snowflake role for the Openflow connection service.
                  Note: SNOWFLAKE_MANAGED auth uses the runtime's session role,
                  but the Role parameter is still sent as a hint/fallback.
            profile: nipyapi profile name. If None, read from session cache.
        """
        self._account = account
        self._role = role
        self._profile = profile
        self._session_activated = False

    def _ensure_session(self):
        """Activate the nipyapi profile if not already done."""
        if not self._session_activated:
            activate_session(self._profile)
            self._session_activated = True

    @property
    @abstractmethod
    def flow_name(self) -> str:
        ...

    @property
    @abstractmethod
    def param_context_name(self) -> str:
        ...

    @abstractmethod
    def parameters(self) -> dict:
        ...

    @property
    def api_url(self) -> str:
        raise NotImplementedError("Override api_url or build_fetch_chain()")

    @property
    def http_method(self) -> str:
        return "GET"

    @property
    def jolt_spec(self) -> str:
        return '{"*":"RAW.&"}'

    @property
    def schedule_period(self) -> str:
        return "5 min"

    @property
    def offset_pointer(self) -> str:
        return "/time"

    def base_parameters(self) -> dict:
        params = self.parameters()
        return {
            "Account": self._account,
            "Role": self._role,
            **params,
            "Pipe": f"{params['Table']}-STREAMING",
        }

    def build(self) -> FlowComponents:
        self._ensure_session()

        root_id = nipyapi.canvas.get_root_pg_id()

        print(f"[1/7] Creating process group: {self.flow_name}")
        pg = nipyapi.canvas.create_process_group(
            nipyapi.canvas.get_process_group(root_id, "id"),
            self.flow_name, location=(300, 300)
        )
        pg_id = pg.id

        print(f"[2/7] Creating parameter context: {self.param_context_name}")
        pc = nipyapi.parameters.create_parameter_context(self.param_context_name)
        pc_id = pc.id
        for k, v in self.base_parameters().items():
            param = nipyapi.parameters.prepare_parameter(k, value=v)
            nipyapi.parameters.upsert_parameter_to_context(pc, param)
        nipyapi.parameters.assign_context_to_process_group(pg.id, pc.id)

        print("[3/7] Creating controller services")
        wc_type = nipyapi.canvas.get_controller_type("StandardWebClientServiceProvider")
        web_client = nipyapi.canvas.create_controller(pg, wc_type, name="Web Client")
        wc_id = web_client.id
        wc_config = nipyapi.canvas.prepare_controller_config(web_client, {
            "Connect Timeout": "10 secs",
            "Read Timeout": "10 secs",
            "Write Timeout": "10 secs",
            "HTTP Protocol Version": "HTTP_2",
        })
        nipyapi.canvas.update_controller(web_client, wc_config)

        print("[4/7] Creating processors")
        components = FlowComponents(
            pg_id=pg_id,
            param_context_id=pc_id,
            snowflake_conn_id="",
            web_client_id=wc_id,
        )

        fetch = self._create_invoke_http(pg, (0, 0))
        components.processors["fetch"] = ProcessorRef(fetch.id, fetch.component.name, fetch.component.type)

        jolt = self._create_jolt_transform(pg, (0, 200))
        components.processors["jolt"] = ProcessorRef(jolt.id, jolt.component.name, jolt.component.type)

        stream = self._create_put_snowpipe_streaming(pg, wc_id, (0, 400))
        components.processors["stream"] = ProcessorRef(stream.id, stream.component.name, stream.component.type)

        retry = self._create_retry_flowfile(pg, (-400, 400))
        components.processors["retry"] = ProcessorRef(retry.id, retry.component.name, retry.component.type)

        print("[5/7] Creating funnels")
        success_funnel = nipyapi.canvas.create_funnel(pg_id, position=(400, 400))
        fail_funnel = nipyapi.canvas.create_funnel(pg_id, position=(-400, 600))
        components.funnels["success"] = success_funnel.id
        components.funnels["fail"] = fail_funnel.id

        print("[6/7] Creating connections")
        nipyapi.canvas.create_connection(fetch, jolt, relationships=["Response"])
        nipyapi.canvas.create_connection(jolt, stream, relationships=["success"])
        nipyapi.canvas.create_connection(stream, success_funnel, relationships=["success"])
        nipyapi.canvas.create_connection(stream, retry, relationships=["failure"])
        nipyapi.canvas.create_connection(retry, stream, relationships=["retry"])
        nipyapi.canvas.create_connection(retry, fail_funnel, relationships=["retries_exceeded"])

        self._create_terminal_connections(pg, fetch, success_funnel, fail_funnel)

        print("[7/7] Enabling controller services")
        nipyapi.canvas.schedule_controller(web_client, True, refresh=True)

        print(f"Flow '{self.flow_name}' built successfully. PG ID: {pg_id}")
        return components

    def _create_invoke_http(self, pg, location):
        proc_type = nipyapi.canvas.get_processor_type("InvokeHTTP")
        proc = nipyapi.canvas.create_processor(pg, proc_type, location, name=f"Fetch {self.flow_name}")
        config = nipyapi.canvas.prepare_processor_config(proc, {
            "HTTP Method": self.http_method,
            "HTTP URL": self.api_url,
            "HTTP/2 Disabled": "False",
            "Connection Timeout": "5 secs",
            "Socket Read Timeout": "15 secs",
            "Response Generation Required": "true",
        })
        config.scheduling_period = self.schedule_period
        config.auto_terminated_relationships = ["Original", "No Retry", "Failure", "Retry"]
        nipyapi.canvas.update_processor(proc, config)
        return nipyapi.canvas.get_processor(proc.id, "id")

    def _create_jolt_transform(self, pg, location):
        proc_type = nipyapi.canvas.get_processor_type("JoltTransformJSON")
        proc = nipyapi.canvas.create_processor(pg, proc_type, location, name="Wrap as VARIANT")
        config = nipyapi.canvas.prepare_processor_config(proc, {
            "Jolt Transform": "jolt-transform-shift",
            "Jolt Specification": self.jolt_spec,
            "Transform Cache Size": "1",
            "JSON Source": "FLOW_FILE",
            "Pretty Print": "false",
            "Max String Length": "20 MB",
        })
        config.auto_terminated_relationships = [
            "failure"
        ]
        nipyapi.canvas.update_processor(proc, config)
        return nipyapi.canvas.get_processor(proc.id, "id")

    def _create_put_snowpipe_streaming(self, pg, web_client_id, location):
        proc_type = nipyapi.canvas.get_processor_type("PutSnowpipeStreaming2")
        proc = nipyapi.canvas.create_processor(pg, proc_type, location, name="Stream to Snowflake")
        config = nipyapi.canvas.prepare_processor_config(proc, {
            "Authentication Strategy": "SNOWFLAKE_MANAGED",
            "Account": "#{Account}",
            "Role": "#{Role}",
            "Database": "#{Database}",
            "Schema": "#{Schema}",
            "Pipe": "#{Pipe}",
            "Web Client Service Provider": web_client_id,
            "Transfer Strategy": "ROWS",
            "Offset Tracking Resolution": "RECORD",
            "Offset Token Start Expression": "${now():toNumber()}",
            "Offset Token End Expression": "${now():toNumber()}",
            "Offset Token Record Pointer": self.offset_pointer,
            "Channel Group": "SHARED",
        })
        config.auto_terminated_relationships = ["invalid", "empty"]
        nipyapi.canvas.update_processor(proc, config)
        return nipyapi.canvas.get_processor(proc.id, "id")

    def _create_retry_flowfile(self, pg, location):
        proc_type = nipyapi.canvas.get_processor_type("RetryFlowFile")
        proc = nipyapi.canvas.create_processor(pg, proc_type, location, name="Retry Once")
        config = nipyapi.canvas.prepare_processor_config(proc, {
            "Maximum Retries": "1",
            "Penalize Retries": "true",
            "Reuse Mode": "fail",
        })
        config.auto_terminated_relationships = [
            "failure"
        ]
        nipyapi.canvas.update_processor(proc, config)
        return nipyapi.canvas.get_processor(proc.id, "id")

    def _create_terminal_connections(self, pg, fetch_proc, success_funnel, fail_funnel):
        pass
