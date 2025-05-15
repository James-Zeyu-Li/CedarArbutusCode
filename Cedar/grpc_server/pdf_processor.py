import asyncio
import shutil
import os
from pathlib import Path
import logging

logger = logging.getLogger("PDFProcessor")


async def run_pdf_ingestion(script_path: Path, input_file: Path, output_dir: Path) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        str(script_path),
        str(input_file),
        str(output_dir),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode, stderr.decode(errors="ignore")


def archive_results(output_dir: Path, zip_target: Path):
    shutil.make_archive(
        base_name=str(zip_target.with_suffix("")),
        format="zip",
        root_dir=str(output_dir)
    )


async def process_pdf_job(script_path: Path, input_file: Path, output_dir: Path) -> tuple[bool, Path | None, str]:
    if not input_file.exists():
        return False, None, f"File not found: {input_file}"

    os.chmod(script_path, 0o755)
    output_dir.mkdir(parents=True, exist_ok=True)

    code, stderr = await run_pdf_ingestion(script_path, input_file, output_dir)
    if code != 0:
        return False, None, stderr[:200]

    output_files = list(output_dir.glob("chunk-*.json*"))
    if not output_files:
        return False, None, "No output files generated"

    zip_path = output_dir.parent / f"{output_dir.name}.zip"
    archive_results(output_dir, zip_path)
    return True, zip_path, "Success"
