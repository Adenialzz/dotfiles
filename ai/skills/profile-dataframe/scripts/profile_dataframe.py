# /// script
# dependencies = [
#   "pandas",
#   "openpyxl",
#   "xlrd",
#   "pyarrow",
# ]
# ///

import argparse
import json
import sys
import warnings
from pathlib import Path

import pandas as pd
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
    is_string_dtype,
)


TEXT_SCAN_LIMIT = 5000


def parse_args():
    parser = argparse.ArgumentParser(
        description="Profile a dataframe-like file and emit a machine-readable JSON summary.",
        epilog=(
            "Use this tool to inspect an unfamiliar table-like file before writing a script.\n"
            "Supported formats: csv, txt, tsv, xlsx, xls, xlsm, parquet, json, jsonl, "
            "ndjson, feather, pkl, pickle.\n"
            "\n"
            "Success output:\n"
            "  A single JSON object with ok=true and summary fields such as path, "
            "file_format, shape, sample_rows, and columns.\n"
            "  Each item in columns typically includes name, dtype, null stats, "
            "unique_count, sample_values, inferred_roles, and optional numeric_summary, "
            "datetime_summary, or text_summary.\n"
            "\n"
            "Role inference:\n"
            "  inferred_roles are heuristic guesses for faster schema understanding.\n"
            "  Common values: identifier, timestamp, boolean, measure, categorical, text.\n"
            "  Treat them as hints, not authoritative schema.\n"
            "\n"
            "Failure output:\n"
            "  A single JSON object with ok=false and error.type / error.message."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("path", help="Path to csv/xlsx/parquet/json/... file")
    parser.add_argument("--sheet", help="Excel sheet name to read", default=None)
    parser.add_argument("--sample-rows", type=int, default=5)
    parser.add_argument(
        "--profile-rows",
        type=int,
        default=50000,
        help="Use only the first N rows for expensive per-column profiling.",
    )
    return parser.parse_args()


def normalize_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            value = value.item()
        except Exception:
            pass
    if isinstance(value, Path):
        return str(value)
    return value


def sample_values(series, limit):
    values = []
    seen = set()
    for value in series.dropna():
        normalized = normalize_value(value)
        marker = repr(normalized)
        if marker in seen:
            continue
        seen.add(marker)
        values.append(normalized)
        if len(values) >= limit:
            break
    return values


def infer_roles(name, series, profiled_series):
    roles = []
    lower_name = name.lower()
    non_null = series.dropna()
    unique_ratio = None
    avg_text_length = None
    if len(non_null) > 0:
        unique_ratio = non_null.nunique(dropna=True) / len(non_null)

    if any(token in lower_name for token in ("id", "uuid", "code", "key")):
        if unique_ratio is None or unique_ratio >= 0.8:
            roles.append("identifier")

    parsed_datetime_ratio = 0.0
    if (is_string_dtype(series) or is_object_dtype(series)) and len(profiled_series) > 0:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            parsed = pd.to_datetime(profiled_series, errors="coerce")
        parsed_datetime_ratio = float(parsed.notna().mean())
        avg_text_length = float(profiled_series.astype(str).str.len().mean())

    if is_datetime64_any_dtype(series) or parsed_datetime_ratio >= 0.8 or any(
        token in lower_name
        for token in ("time", "date", "dt", "day", "created", "updated")
    ):
        roles.append("timestamp")

    if is_bool_dtype(series):
        roles.append("boolean")

    if is_numeric_dtype(series) and "identifier" not in roles and "timestamp" not in roles:
        roles.append("measure")

    if len(profiled_series) > 0:
        profiled_unique = profiled_series.nunique(dropna=True)
        profiled_unique_ratio = profiled_unique / max(len(profiled_series), 1)
        if (
            "identifier" not in roles
            and "timestamp" not in roles
            and (
                is_bool_dtype(series)
                or profiled_unique_ratio <= 0.2
                or (
                    (is_string_dtype(series) or is_object_dtype(series))
                    and profiled_unique <= 20
                    and profiled_unique_ratio <= 0.5
                    and (avg_text_length or 0) < 30
                )
            )
        ):
            roles.append("categorical")

    if is_string_dtype(series) or is_object_dtype(series):
        text_lengths = profiled_series.astype(str).str.len()
        if len(text_lengths) > 0 and text_lengths.mean() >= 30:
            roles.append("text")

    ordered_roles = []
    for role in roles:
        if role not in ordered_roles:
            ordered_roles.append(role)
    return ordered_roles


def summarize_column(name, series, profiled_series, sample_row_limit):
    non_null_count = int(series.notna().sum())
    null_count = int(series.isna().sum())
    total_count = int(len(series))
    summary = {
        "name": name,
        "dtype": str(series.dtype),
        "non_null_count": non_null_count,
        "null_count": null_count,
        "null_ratio": round(null_count / total_count, 6) if total_count else 0.0,
        "unique_count": int(series.nunique(dropna=True)),
        "sample_values": sample_values(series, sample_row_limit),
        "inferred_roles": infer_roles(name, series, profiled_series),
    }

    if is_numeric_dtype(series) and non_null_count:
        summary["numeric_summary"] = {
            "min": normalize_value(series.min()),
            "max": normalize_value(series.max()),
            "mean": normalize_value(series.mean()),
        }
    elif is_datetime64_any_dtype(series) and non_null_count:
        summary["datetime_summary"] = {
            "min": normalize_value(series.min()),
            "max": normalize_value(series.max()),
        }
    elif is_string_dtype(series) or is_object_dtype(series):
        text_lengths = profiled_series.dropna().astype(str).str.len()
        if len(text_lengths) > 0:
            summary["text_summary"] = {
                "avg_length": round(float(text_lengths.mean()), 3),
                "max_length": int(text_lengths.max()),
            }

    return summary


def load_dataframe(path, sheet):
    suffix = path.suffix.lower()
    meta = {"file_format": suffix.lstrip(".")}

    if suffix in {".csv", ".txt", ".tsv"}:
        sep = "\t" if suffix == ".tsv" else None
        df = pd.read_csv(path, sep=sep, engine="python")
    elif suffix in {".xlsx", ".xls", ".xlsm"}:
        excel_file = pd.ExcelFile(path)
        meta["available_sheets"] = excel_file.sheet_names
        selected_sheet = sheet or excel_file.sheet_names[0]
        meta["selected_sheet"] = selected_sheet
        df = pd.read_excel(path, sheet_name=selected_sheet)
    elif suffix == ".parquet":
        df = pd.read_parquet(path)
    elif suffix in {".json", ".jsonl", ".ndjson"}:
        lines = suffix in {".jsonl", ".ndjson"}
        df = pd.read_json(path, lines=lines)
    elif suffix == ".feather":
        df = pd.read_feather(path)
    elif suffix in {".pkl", ".pickle"}:
        df = pd.read_pickle(path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    if isinstance(df, pd.Series):
        df = df.to_frame()
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Loaded object is not a DataFrame: {type(df).__name__}")

    return df, meta


def build_summary(df, meta, path, sample_rows, profile_rows):
    profiled_df = df.head(profile_rows).copy()
    summary = {
        "ok": True,
        "path": str(path.resolve()),
        "file_format": meta.get("file_format"),
        "shape": {"rows": int(len(df)), "columns": int(len(df.columns))},
        "columns": [],
        "duplicate_row_count": int(df.duplicated().sum()),
        "profiled_row_count": int(len(profiled_df)),
        "role_inference_is_heuristic": True,
        "role_inference_note": "inferred_roles are heuristic guesses, not authoritative schema.",
        "sample_rows": json.loads(
            df.head(sample_rows).to_json(orient="records", date_format="iso")
        ),
    }
    for key in ("available_sheets", "selected_sheet"):
        if key in meta:
            summary[key] = meta[key]

    for column in df.columns:
        summary["columns"].append(
            summarize_column(
                str(column),
                df[column],
                profiled_df[column].dropna().head(TEXT_SCAN_LIMIT),
                sample_rows,
            )
        )
    return summary


def main():
    args = parse_args()
    try:
        path = Path(args.path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        df, meta = load_dataframe(path, args.sheet)
        summary = build_summary(df, meta, path, args.sample_rows, args.profile_rows)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        error_summary = {
            "ok": False,
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
            },
        }
        print(json.dumps(error_summary, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
