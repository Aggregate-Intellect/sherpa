import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from cloudpathlib import CloudPath


def upload_file(src: Path, dest: Union[str, "CloudPath"]) -> None:
    """Upload a file.

    src (Path): The source path.
    url (str): The destination URL to upload to.
    """
    import smart_open

    # Create parent directories for local paths
    if isinstance(dest, Path):
        if not dest.parent.exists():
            dest.parent.mkdir(parents=True)

    dest = str(dest)
    with smart_open.open(dest, mode="wb") as output_file:
        with src.open(mode="rb") as input_file:
            output_file.write(input_file.read())


def download_file(
    src: Union[str, "CloudPath"], dest: Path, *, force: bool = False
) -> None:
    """Download a file using smart_open.

    url (str): The URL of the file.
    dest (Path): The destination path.
    force (bool): Whether to force download even if file exists.
        If False, the download will be skipped.
    """
    import smart_open

    if dest.exists() and not force:
        return None
    src = str(src)
    with smart_open.open(src, mode="rb", compression="disable") as input_file:
        with dest.open(mode="wb") as output_file:
            shutil.copyfileobj(input_file, output_file)
