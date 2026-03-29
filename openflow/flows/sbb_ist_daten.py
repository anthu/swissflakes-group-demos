#!/usr/bin/env python3
"""
Flow: SBB Ist-Daten v2 -> SFG_LOGISTICS.RAW_SHIPMENTS.SBB_IST_DATEN
Pattern: Catalog HTML -> Extract CSV URL -> Download CSV -> Split -> JSON Wrap -> SSV2

SBB publishes actual vs planned train times on data.opentransportdata.swiss.
The dataset page is an HTML catalog (CKAN), not a direct data endpoint.
This flow:
  1. Fetches the HTML catalog page for ist-daten-v2
  2. Regex-extracts the first CSV download URL from href attributes
  3. Downloads the CSV (~537 MB, ~2.1M rows, semicolon-delimited)
  4. Splits into batches of 1000 rows (SplitText) to avoid NiFi OOM
  5. Wraps each batch as NDJSON: one {"RAW":"<escaped_row>"} per line
  6. Streams to Snowflake via SSV2

This is a custom build() override — it does NOT use the base class's
single InvokeHTTP + transform pattern.
"""
import argparse

import nipyapi

from openflow.shared.flow_builder import (
    FlowComponents,
    OpenflowFlowBuilder,
    ProcessorRef,
)


class SBBIstDaten(OpenflowFlowBuilder):

    @property
    def flow_name(self) -> str:
        return "SBB Ist-Daten"

    @property
    def param_context_name(self) -> str:
        return "SBB Ist-Daten Params"

    def parameters(self) -> dict:
        return {
            "Database": "SFG_LOGISTICS",
            "Schema": "RAW_SHIPMENTS",
            "Table": "SBB_IST_DATEN",
        }

    @property
    def api_url(self) -> str:
        return "https://data.opentransportdata.swiss/dataset/ist-daten-v2"

    @property
    def schedule_period(self) -> str:
        return "1 day"

    @property
    def offset_pointer(self) -> str:
        return "/BETRIEBSTAG"

    # ── Custom build: 7-processor pipeline ──────────────────────────

    _EXTRACT_CSV_URL_SCRIPT = (
        'import org.apache.commons.io.IOUtils\n'
        'import java.nio.charset.StandardCharsets\n'
        'import java.util.regex.Pattern\n'
        '\n'
        'def flowFile = session.get()\n'
        'if (!flowFile) return\n'
        '\n'
        'def html = ""\n'
        'session.read(flowFile, { inputStream ->\n'
        '    html = IOUtils.toString(inputStream, StandardCharsets.UTF_8)\n'
        '} as org.apache.nifi.processor.io.InputStreamCallback)\n'
        '\n'
        'def pattern = Pattern.compile(\n'
        '    \'href="(https://data[.]opentransportdata[.]swiss/dataset/\'\n'
        '    + \'[^"]+/download/[^"]+_istdaten[.]csv)"\')\n'
        'def matcher = pattern.matcher(html)\n'
        '\n'
        'if (matcher.find()) {\n'
        '    def csvUrl = matcher.group(1)\n'
        '    def parts = csvUrl.split("/")\n'
        '    def csvFilename = parts[parts.length - 1]\n'
        '    flowFile = session.putAttribute(flowFile, "csv.download.url", csvUrl)\n'
        '    flowFile = session.putAttribute(flowFile, "csv.filename", csvFilename)\n'
        '    log.info("Found CSV URL: " + csvUrl)\n'
        '    session.transfer(flowFile, REL_SUCCESS)\n'
        '} else {\n'
        '    log.error("No CSV download URL found in catalog page")\n'
        '    session.transfer(flowFile, REL_FAILURE)\n'
        '}\n'
    )

    _WRAP_NDJSON_SCRIPT = (
        'import org.apache.commons.io.IOUtils\n'
        'import groovy.json.JsonOutput\n'
        'import java.nio.charset.StandardCharsets\n'
        '\n'
        'def flowFile = session.get()\n'
        'if (!flowFile) return\n'
        '\n'
        'def content = ""\n'
        'session.read(flowFile, { inputStream ->\n'
        '    content = IOUtils.toString(inputStream, StandardCharsets.UTF_8)\n'
        '} as org.apache.nifi.processor.io.InputStreamCallback)\n'
        '\n'
        'def lines = content.split("\\n")\n'
        'def sb = new StringBuilder()\n'
        'for (line in lines) {\n'
        '    def trimmed = line.trim()\n'
        '    if (trimmed.length() > 0) {\n'
        '        sb.append(\'{"RAW":\')\n'
        '        sb.append(JsonOutput.toJson(trimmed))\n'
        '        sb.append(\'}\\n\')\n'
        '    }\n'
        '}\n'
        '\n'
        'flowFile = session.write(flowFile, { outputStream ->\n'
        '    outputStream.write(sb.toString().getBytes(StandardCharsets.UTF_8))\n'
        '} as org.apache.nifi.processor.io.OutputStreamCallback)\n'
        '\n'
        'session.transfer(flowFile, REL_SUCCESS)\n'
    )

    def build(self) -> FlowComponents:
        self._ensure_session()
        root_id = nipyapi.canvas.get_root_pg_id()

        print(f"[1/7] Creating process group: {self.flow_name}")
        pg = nipyapi.canvas.create_process_group(
            nipyapi.canvas.get_process_group(root_id, "id"),
            self.flow_name, location=(300, 300),
        )
        pg_id = pg.id

        print(f"[2/7] Creating parameter context: {self.param_context_name}")
        pc = nipyapi.parameters.create_parameter_context(self.param_context_name)
        for k, v in self.base_parameters().items():
            param = nipyapi.parameters.prepare_parameter(k, value=v)
            nipyapi.parameters.upsert_parameter_to_context(pc, param)
        nipyapi.parameters.assign_context_to_process_group(pg.id, pc.id)

        print("[3/7] Creating controller services")
        wc_type = nipyapi.canvas.get_controller_type("StandardWebClientServiceProvider")
        web_client = nipyapi.canvas.create_controller(pg, wc_type, name="Web Client")
        wc_config = nipyapi.canvas.prepare_controller_config(web_client, {
            "Connect Timeout": "10 secs",
            "Read Timeout": "10 secs",
            "Write Timeout": "10 secs",
            "HTTP Protocol Version": "HTTP_2",
        })
        nipyapi.canvas.update_controller(web_client, wc_config)

        print("[4/7] Creating processors (7-step pipeline)")
        components = FlowComponents(
            pg_id=pg_id,
            param_context_id=pc.id,
            snowflake_conn_id="",
            web_client_id=web_client.id,
        )

        # 1. Fetch catalog HTML
        fetch_cat = self._create_invoke_http(pg, (0, 0))
        components.processors["fetch_catalog"] = ProcessorRef(
            fetch_cat.id, fetch_cat.component.name, fetch_cat.component.type,
        )

        # 2. Extract CSV URL from HTML via Groovy regex
        groovy_type = nipyapi.canvas.get_processor_type("ExecuteGroovyScript")
        extract = nipyapi.canvas.create_processor(
            pg, groovy_type, (0, 200), name="Extract CSV URL",
        )
        cfg = nipyapi.canvas.prepare_processor_config(extract, {
            "Script Body": self._EXTRACT_CSV_URL_SCRIPT,
        })
        cfg.auto_terminated_relationships = ["failure"]
        nipyapi.canvas.update_processor(extract, cfg)
        extract = nipyapi.canvas.get_processor(extract.id, "id")
        components.processors["extract_url"] = ProcessorRef(
            extract.id, extract.component.name, extract.component.type,
        )

        # 3. Download the CSV using the extracted URL attribute
        http_type = nipyapi.canvas.get_processor_type("InvokeHTTP")
        fetch_csv = nipyapi.canvas.create_processor(
            pg, http_type, (0, 400), name="Fetch CSV Data",
        )
        cfg = nipyapi.canvas.prepare_processor_config(fetch_csv, {
            "HTTP Method": "GET",
            "HTTP URL": "${csv.download.url}",
            "Connection Timeout": "30 secs",
            "Socket Read Timeout": "300 secs",
            "Response Generation Required": "true",
            "Request User-Agent": "swissflakes-openflow",
        })
        cfg.scheduling_strategy = "TIMER_DRIVEN"
        cfg.scheduling_period = "0 sec"
        cfg.auto_terminated_relationships = [
            "Original", "No Retry", "Failure", "Retry",
        ]
        nipyapi.canvas.update_processor(fetch_csv, cfg)
        fetch_csv = nipyapi.canvas.get_processor(fetch_csv.id, "id")
        components.processors["fetch_csv"] = ProcessorRef(
            fetch_csv.id, fetch_csv.component.name, fetch_csv.component.type,
        )

        # 4. Split CSV into batches of 1000 rows (preserving header)
        split_type = nipyapi.canvas.get_processor_type("SplitText")
        split = nipyapi.canvas.create_processor(
            pg, split_type, (0, 600), name="Split CSV Rows",
        )
        cfg = nipyapi.canvas.prepare_processor_config(split, {
            "Line Split Count": "1000",
            "Header Line Count": "1",
            "Remove Trailing Newlines": "true",
        })
        cfg.auto_terminated_relationships = ["failure", "original"]
        nipyapi.canvas.update_processor(split, cfg)
        split = nipyapi.canvas.get_processor(split.id, "id")
        components.processors["split"] = ProcessorRef(
            split.id, split.component.name, split.component.type,
        )

        # 5. Wrap each batch as NDJSON: {"RAW":"<row>"} per line
        wrap = nipyapi.canvas.create_processor(
            pg, groovy_type, (0, 800), name="Wrap as JSON",
        )
        cfg = nipyapi.canvas.prepare_processor_config(wrap, {
            "Script Body": self._WRAP_NDJSON_SCRIPT,
        })
        cfg.auto_terminated_relationships = ["failure"]
        nipyapi.canvas.update_processor(wrap, cfg)
        wrap = nipyapi.canvas.get_processor(wrap.id, "id")
        components.processors["wrap"] = ProcessorRef(
            wrap.id, wrap.component.name, wrap.component.type,
        )

        # 6. Stream to Snowflake
        stream = self._create_put_snowpipe_streaming(pg, web_client.id, (0, 1000))
        components.processors["stream"] = ProcessorRef(
            stream.id, stream.component.name, stream.component.type,
        )

        # 7. Retry once on failure
        retry = self._create_retry_flowfile(pg, (-400, 1000))
        components.processors["retry"] = ProcessorRef(
            retry.id, retry.component.name, retry.component.type,
        )

        print("[5/7] Creating funnels")
        success_funnel = nipyapi.canvas.create_funnel(pg_id, position=(400, 1000))
        fail_funnel = nipyapi.canvas.create_funnel(pg_id, position=(-400, 1200))
        components.funnels["success"] = success_funnel.id
        components.funnels["fail"] = fail_funnel.id

        print("[6/7] Creating connections")
        nipyapi.canvas.create_connection(fetch_cat, extract, relationships=["Response"])
        nipyapi.canvas.create_connection(extract, fetch_csv, relationships=["success"])
        nipyapi.canvas.create_connection(fetch_csv, split, relationships=["Response"])
        nipyapi.canvas.create_connection(split, wrap, relationships=["splits"])
        nipyapi.canvas.create_connection(wrap, stream, relationships=["success"])
        nipyapi.canvas.create_connection(stream, success_funnel, relationships=["success"])
        nipyapi.canvas.create_connection(stream, retry, relationships=["failure"])
        nipyapi.canvas.create_connection(retry, stream, relationships=["retry"])
        nipyapi.canvas.create_connection(retry, fail_funnel, relationships=["retries_exceeded"])

        self._create_terminal_connections(pg, fetch_cat, success_funnel, fail_funnel)

        print("[7/7] Enabling controller services")
        nipyapi.canvas.schedule_controller(web_client, True, refresh=True)

        print(f"Flow '{self.flow_name}' built successfully. PG ID: {pg_id}")
        return components


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy SBB Ist-Daten flow")
    parser.add_argument("--account", required=True, help="Snowflake account identifier")
    parser.add_argument("--role", default="OPENFLOW_ADMIN", help="Snowflake role")
    parser.add_argument("--profile", default=None, help="nipyapi profile (default: from cache)")
    args = parser.parse_args()

    builder = SBBIstDaten(
        account=args.account, role=args.role, profile=args.profile,
    )
    components = builder.build()
    print(f"\nDone. Process Group ID: {components.pg_id}")
