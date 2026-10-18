import sys
from pathlib import Path
from subprocess import run


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    proto_dir = root / "proto"
    output_dir = root / "mcstore" / "grpc_generated"
    output_dir.mkdir(parents=True, exist_ok=True)
    run(
        [
            sys.executable,
            "-m",
            "grpc_tools.protoc",
            f"-I{proto_dir}",
            f"--python_out={output_dir}",
            f"--grpc_python_out={output_dir}",
            str(proto_dir / "auth.proto"),
            str(proto_dir / "stats.proto"),
        ],
        check=True,
    )
    for generated_file in output_dir.glob("*_pb2*.py"):
        text = generated_file.read_text(encoding="utf-8")
        text = text.replace(
            "import auth_pb2 as auth__pb2",
            "from mcstore.grpc_generated import auth_pb2 as auth__pb2",
        )
        text = text.replace(
            "import stats_pb2 as stats__pb2",
            "from mcstore.grpc_generated import stats_pb2 as stats__pb2",
        )
        generated_file.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
