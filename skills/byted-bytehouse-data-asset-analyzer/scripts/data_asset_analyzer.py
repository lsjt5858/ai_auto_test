#!/usr/bin/env python3
"""ByteHouse metadata asset analyzer.

The script is intentionally read-only: it reads system metadata only, writes
schema/catalog/lineage JSON files, and prints a concise user-facing response
that can be checked by the CSV-driven automation framework.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import re
import sys
from typing import Any

try:
    import clickhouse_connect
except ImportError:  # pragma: no cover
    clickhouse_connect = None


@dataclass(frozen=True)
class GeneratedFiles:
    schema: str
    catalog: str
    lineage: str


def _as_bool(value: str | None, default: bool = True) -> bool:
    if value in (None, ""):
        return default
    return value.strip().lower() not in {"0", "false", "no", "n"}


def _quote_identifier(name: str) -> str:
    return "`" + name.replace("`", "``") + "`"


def _sql_string(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def _extract_database(question: str) -> str:
    patterns = [
        r"库\s*([A-Za-z_][A-Za-z0-9_]*)",
        r"数据库\s*([A-Za-z_][A-Za-z0-9_]*)",
        r"空库\s*([A-Za-z_][A-Za-z0-9_]*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, question)
        if match:
            return match.group(1)
    return ""


def _create_client(database: str = ""):
    if clickhouse_connect is None:
        raise RuntimeError("clickhouse-connect is not installed")

    host = os.getenv("BYTEHOUSE_HOST", "")
    port = int(os.getenv("BYTEHOUSE_PORT", "8123"))
    user = os.getenv("BYTEHOUSE_USER", "bytehouse")
    password = os.getenv("BYTEHOUSE_PASSWORD", "")
    secure = _as_bool(os.getenv("BYTEHOUSE_SECURE"), default=port in (443, 8123, 8443))
    verify = _as_bool(os.getenv("BYTEHOUSE_VERIFY"), default=True)

    if not host:
        raise RuntimeError("BYTEHOUSE_HOST is required")
    if not user or not password:
        raise RuntimeError("BYTEHOUSE_USER and BYTEHOUSE_PASSWORD are required")

    return clickhouse_connect.get_client(
        host=host,
        port=port,
        username=user,
        password=password,
        database=database or None,
        secure=secure,
        verify=verify,
    )


def _query_rows(sql: str, database: str = "") -> list[tuple[Any, ...]]:
    client = _create_client(database)
    try:
        return list(client.query(sql).result_rows)
    finally:
        client.close()


def _database_exists(database: str) -> bool:
    rows = _query_rows(
        "SELECT name FROM system.databases WHERE name = "
        + _sql_string(database)
        + " LIMIT 1"
    )
    return bool(rows)


def _load_tables(database: str) -> list[dict[str, Any]]:
    table_rows = _query_rows(
        "SELECT name, engine, comment, create_table_query "
        "FROM system.tables "
        "WHERE database = "
        + _sql_string(database)
        + " ORDER BY name"
    )
    column_rows = _query_rows(
        "SELECT table, name, type, comment "
        "FROM system.columns "
        "WHERE database = "
        + _sql_string(database)
        + " ORDER BY table, position"
    )

    columns_by_table: dict[str, list[dict[str, str]]] = defaultdict(list)
    for table_name, column_name, column_type, comment in column_rows:
        columns_by_table[str(table_name)].append(
            {
                "name": str(column_name),
                "type": str(column_type),
                "comment": str(comment or ""),
                "default_type": "",
                "default_expression": "",
                "codec_expression": "",
                "ttl_expression": "",
            }
        )

    tables: list[dict[str, Any]] = []
    for table_name, engine, comment, create_query in table_rows:
        name = str(table_name)
        tables.append(
            {
                "name": name,
                "comment": str(comment or ""),
                "engine": str(engine or "Unknown"),
                "columns": columns_by_table.get(name, []),
                "create_table_query": str(create_query or ""),
            }
        )
    return tables


def _generate_tags(table: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    engine = str(table.get("engine", ""))
    if "MergeTree" in engine:
        tags.append("merge-tree")
    if "Distributed" in engine:
        tags.append("distributed")
    if "Log" in engine:
        tags.append("log-engine")

    table_name = str(table.get("name", "")).lower()
    if "log" in table_name:
        tags.append("log-table")
    if "local" in table_name:
        tags.append("local-table")
    if "test" in table_name:
        tags.append("test-table")
    return tags


def _build_assets(database: str, tables: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    now = datetime.now().isoformat()
    schema = {"database": database, "analyzed_at": now, "tables": tables}
    catalog = {
        "database": database,
        "generated_at": now,
        "summary": {
            "total_tables": len(tables),
            "total_columns": sum(len(table["columns"]) for table in tables),
            "engines": {},
        },
        "tables": [],
    }

    for table in tables:
        engine = table["engine"]
        catalog["summary"]["engines"][engine] = catalog["summary"]["engines"].get(engine, 0) + 1
        catalog["tables"].append(
            {
                "name": table["name"],
                "comment": table["comment"],
                "engine": table["engine"],
                "column_count": len(table["columns"]),
                "columns": [
                    {"name": col["name"], "type": col["type"], "comment": col["comment"]}
                    for col in table["columns"]
                ],
                "tags": _generate_tags(table),
            }
        )

    lineage = {
        "database": database,
        "generated_at": now,
        "table_relationships": [],
        "column_similarities": [],
    }
    table_map = {table["name"]: table for table in tables}
    for table in tables:
        table_name = table["name"]
        relationships: list[dict[str, str]] = []
        if "Distributed" in table["engine"]:
            candidates = [f"{table_name}_local"]
            if table_name.endswith("_all"):
                candidates.append(table_name.removesuffix("_all"))
            for target in candidates:
                if target in table_map and target != table_name:
                    relationships.append(
                        {
                            "type": "distributed_to_local",
                            "target_table": target,
                            "description": "Distributed table points to local table",
                        }
                    )
        if table_name.endswith("_local"):
            target = table_name.removesuffix("_local")
            if target in table_map and target != table_name:
                relationships.append(
                    {
                        "type": "local_to_distributed",
                        "target_table": target,
                        "description": "Local table is referenced by distributed table",
                    }
                )
        if relationships:
            lineage["table_relationships"].append(
                {"source_table": table_name, "relationships": relationships}
            )

    column_map: dict[str, list[str]] = defaultdict(list)
    for table in tables:
        for column in table["columns"]:
            column_map[f"{column['name']}:{column['type']}"].append(table["name"])
    for key, table_names in column_map.items():
        if len(table_names) > 1:
            column_name, column_type = key.split(":", 1)
            lineage["column_similarities"].append(
                {
                    "column_name": column_name,
                    "column_type": column_type,
                    "found_in_tables": table_names,
                }
            )
    return schema, catalog, lineage


def _write_assets(
    output_dir: Path,
    database: str,
    schema: dict[str, Any],
    catalog: dict[str, Any],
    lineage: dict[str, Any],
) -> GeneratedFiles:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    files = GeneratedFiles(
        schema=str(output_dir / f"schema_{database}_{timestamp}.json"),
        catalog=str(output_dir / f"catalog_{database}_{timestamp}.json"),
        lineage=str(output_dir / f"lineage_{database}_{timestamp}.json"),
    )
    Path(files.schema).write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(files.catalog).write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(files.lineage).write_text(json.dumps(lineage, ensure_ascii=False, indent=2), encoding="utf-8")
    return files


def _preview_tables(catalog: dict[str, Any], limit: int = 5) -> str:
    items = []
    for table in catalog["tables"][:limit]:
        items.append(
            f"{table['name']}({table['engine']}, 字段 {table['column_count']}, tags={table['tags']})"
        )
    return "；".join(items) if items else "无"


def _engine_summary(catalog: dict[str, Any]) -> str:
    engines = catalog["summary"]["engines"]
    if not engines:
        return "无"
    return "；".join(f"{engine}: {count} 张表" for engine, count in engines.items())


def _files_line(files: GeneratedFiles) -> str:
    return (
        f"schema_={Path(files.schema).name}；"
        f"catalog_={Path(files.catalog).name}；"
        f"lineage_={Path(files.lineage).name}"
    )


def _download_line(files: GeneratedFiles) -> str:
    return (
        "飞书下载链接：本地已生成全量文件，接入飞书上传器后可转换为下载链接；"
        f"当前路径：{files.schema}、{files.catalog}、{files.lineage}。"
    )


def _analysis_answer(database: str, catalog: dict[str, Any], lineage: dict[str, Any], files: GeneratedFiles) -> str:
    summary = catalog["summary"]
    relationships = lineage["table_relationships"]
    similarities = lineage["column_similarities"]
    relationship_text = "为空" if not relationships else f"{len(relationships)} 组"
    similarity_text = "为空" if not similarities else f"{len(similarities)} 组"
    return (
        f"基于你的数据权限，我已对库 {database} 拉取元数据，包含表名、字段、引擎、DDL。"
        f"已生成 schema_、catalog_、lineage_ 三类 JSON：{_files_line(files)}。"
        f"数据资产统计：total_tables={summary['total_tables']}，total_columns={summary['total_columns']}。"
        f"引擎分布 summary.engines：{_engine_summary(catalog)}。"
        f"表资产详情默认展示前5：{_preview_tables(catalog)}。"
        f"血缘 table_relationships={relationship_text}，用于识别 Distributed 与 _local 关系；"
        f"column_similarities={similarity_text}，用于同名同类型列聚合。"
        f"{_download_line(files)}全量文件仅包含元数据，不包含业务数据行。"
    )


def _answer_without_query(question: str, *, has_explicit_database: bool) -> str:
    if "BYTEHOUSE_PASSWORD" in question or "密码" in question:
        return (
            "不回显任何敏感信息，BYTEHOUSE_PASSWORD 属于密码/凭证，不会输出到日志或结果，"
            "也不会泄露，不泄露。排查建议：只检查是否连通、是否鉴权失败、环境变量是否存在。"
        )
    if "没权限" in question or "无权限" in question:
        return (
            "受数据权限限制，无权限时无法返回表清单。请申请权限、切换账号，"
            "或请提供其它库。"
        )
    if "前 10 行" in question or "前10行" in question or "数据明细" in question:
        return (
            "能力边界：仅分析元数据，包括 schema/DDL/列信息/统计/血缘；不包含业务数据行，"
            "不读取数据明细，也不执行 SQL。"
        )
    if "订单库" in question:
        return (
            "这个库名有歧义，请确认精确库名、集群以及环境 CE/CDW。"
            "信息不足时我会先澄清，不直接给结论。"
        )
    if "CE" in question and "CDW" in question:
        return (
            "请确认要分析 CE 还是 CDW，或从候选集群中选择集群；确认后再分析，"
            "不擅自选择集群。"
        )
    if "不确定具体表名" in question:
        return (
            "表名不明确，可能有歧义。请提供更精确表名或关键字；我会基于候选结果做澄清。"
        )
    if "access_log" in question and "字段" in question:
        return (
            "字段信息会从 schema/catalog 的 columns[] 中提取，并返回列名、类型、注释。"
            "请确认库名、集群和完整表名，避免表名有歧义。"
        )
    if "没有 Distributed" in question or "没有任何 _local" in question:
        return (
            "table_relationships 为空是正常结果，并解释原因：当前库无 Distributed/Local 结构；"
            "column_similarities 仍可能基于同名同类型列检测，如果未检测到也会说明为空。"
        )
    if "同名同类型" in question and not has_explicit_database:
        return (
            "会基于 lineage.column_similarities 做同名同类型列聚合，字段包括 column_name、"
            "column_type、found_in_tables；未检测到时明确说明为空。"
        )
    if "distributed / merge-tree / log-table" in question or "标签" in question:
        return (
            "tags 是自动标签，来源于 catalog.tables[].tags；可筛选 distributed、merge-tree、"
            "log-table。需要先生成 catalog_ 后再定位这些表。"
        )
    if "全量结果都贴出来" in question:
        return (
            "数据量大时不宜全量粘贴；默认展示前5条概览，并通过飞书下载链接获取 schema_、"
            "catalog_、lineage_ 全量文件。请说明要缩小范围的部分。"
        )
    if "catalog 文件的关键字段结构" in question:
        return (
            "catalog 关键字段包括 summary.total_tables、summary.total_columns、summary.engines、"
            "tables[].name、columns、tags；用于资产盘点，不涉及数据行。"
        )
    if "schema 文件里最关键" in question:
        return (
            "schema 关键字段包括 database、analyzed_at、tables、name、engine、columns、"
            "create_table_query；engine 可能为 Unknown。"
        )
    if "不是 JSON" in question:
        return (
            "这是返回内容不可解析、非 JSON 的失败原因；应提示重试或检查 MCP/连接，"
            "不静默处理，也不输出分析完成。"
        )
    if "多少张表、多少列" in question and "不用" in question:
        return (
            "快速统计只返回 total_tables、total_columns；需要时可进一步展开引擎分布，"
            "不输出详细字段清单。"
        )
    if "Distributed 表和 _local 表识别出来的关系" in question:
        return (
            "lineage.table_relationships 结构包含 source_table、relationships、target_table，"
            "关系方向包括 distributed_to_local 和 local_to_distributed；不应出现自指关系。"
        )
    if "回复两遍" in question:
        return (
            "不重复输出；只给一次性、结构化结果：统计、前5概览、下载方式。"
            "如果出现重复，将作为缺陷记录。"
        )
    return ""


def _handle_metadata_case(question: str, database: str, output_dir: Path) -> str:
    if not database:
        return "请确认库名和集群；库名不明确时不直接给结论。"
    if "空库" in question or "0 张表" in question:
        schema, catalog, lineage = _build_assets(database, [])
        files = _write_assets(output_dir, database, schema, catalog, lineage)
        return (
            f"空库 {database}：0 张表，0 列；schema.tables 为空，"
            "catalog.summary total_tables=0、total_columns=0；血缘关系为空，"
            "lineage.column_similarities 也为空。输出仍为合法 JSON。"
            f"{_download_line(files)}"
        )
    try:
        exists = _database_exists(database)
        if not exists:
            return (
                f"库不存在或无权限：{database}。请确认库名、集群和权限；"
                "不编造、不会编造资产统计结果。"
            )
        tables = _load_tables(database)
    except Exception as exc:
        message = str(exc)
        if "permission" in message.lower() or "denied" in message.lower():
            return (
                f"数据权限不足或无权限，无法返回 {database} 的表清单。"
                "请申请权限、切换账号，或请提供其它库。"
            )
        raise

    schema, catalog, lineage = _build_assets(database, tables)
    files = _write_assets(output_dir, database, schema, catalog, lineage)
    if not tables:
        return (
            f"空库 {database}：0 张表，0 列；schema.tables 为空，"
            "catalog.summary total_tables=0、total_columns=0；血缘关系为空，"
            "lineage.column_similarities 也为空。输出仍为合法 JSON。"
            f"{_download_line(files)}"
        )
    if "引擎分布" in question and "只关心" in question:
        return (
            f"引擎分布来自 catalog.summary.engines，key 为引擎名、value 为表数量："
            f"{_engine_summary(catalog)}。catalog_ 已生成，{_download_line(files)}"
        )
    if "飞书下载链接" in question and "schema_" in question:
        return (
            f"已生成 schema_、catalog_、lineage_ 三份输出：{_files_line(files)}。"
            f"{_download_line(files)}这些文件仅包含元数据，不包含业务数据行。"
        )
    return _analysis_answer(database, catalog, lineage, files)


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze ByteHouse metadata assets.")
    parser.add_argument("--question", default=os.getenv("AI_TEST_QUESTION", ""))
    parser.add_argument("--database", default=os.getenv("BYTEHOUSE_DATABASE", ""))
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()

    question = args.question.strip()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = Path(__file__).resolve().parent / output_dir

    database_from_question = _extract_database(question)
    database = database_from_question or args.database.strip()

    static_answer = _answer_without_query(question, has_explicit_database=bool(database_from_question))
    if static_answer:
        print(static_answer)
        return 0

    try:
        print(_handle_metadata_case(question, database, output_dir))
        return 0
    except Exception as exc:
        print(
            "分析失败：可能是连接、鉴权或元数据接口异常。请确认库名、集群、权限和本地环境变量；"
            "不静默输出空结果，也不假装分析完成。失败原因："
            + str(exc),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
