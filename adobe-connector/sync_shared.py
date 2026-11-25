"""Copy the shared modules into each harness's utils/ package. Run after editing _shared/."""
import pathlib, shutil
ROOT = pathlib.Path(__file__).resolve().parent
for app in ("photoshop", "illustrator"):
    dest = ROOT / app / "agent-harness" / "cli_anything" / app / "utils"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "__init__.py").touch()
    for f in ("jsx_backend.py", "cli_common.py", "repl_skin.py"):
        shutil.copyfile(ROOT / "_shared" / f, dest / f)
    print("synced", dest)
