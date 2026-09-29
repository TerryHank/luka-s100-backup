"""Adapt a copied NX workspace to the RDK S100 without touching the NX."""

from pathlib import Path

BASE = Path("/home/sunrise/luka_s100")
WS = BASE / "ddsm_car_ws"
REPLACEMENTS = {
    "/home/nvidia/ddsm_car_ws": str(WS),
    "/home/nvidia/person_follow": str(BASE / "person_follow"),
    "/home/nvidia/spatial_memory": str(BASE / "spatial_memory"),
    "/home/nvidia/locateanything_trial_20260907": str(BASE / "locateanything_trial_20260907"),
}
TEXT_SUFFIXES = {".py", ".sh", ".yaml", ".yml", ".json", ".xml", ".html", ".js", ".md", ".toml"}


def main():
    assert BASE.is_dir() and WS.is_dir()
    changed = 0
    for root in (WS / "tools", WS / "config", WS / "src", WS / "maps",
                 BASE / "person_follow", BASE / "spatial_memory",
                 BASE / "locateanything_trial_20260907", WS):
        if root == WS:
            files = [p for p in root.iterdir() if p.is_file()]
        else:
            files = root.rglob("*")
        for path in files:
            if not path.is_file() or path.is_symlink() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            if any(part in {".git", "__pycache__", "build", "install", "log"} for part in path.parts):
                continue
            if path.name.startswith("test_") or ".before" in path.name or path.name.endswith(".bak"):
                continue
            if path.stat().st_size > 2_000_000:
                continue
            try:
                old = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            new = old
            for source, target in REPLACEMENTS.items():
                new = new.replace(source, target)
            if old != new:
                path.write_text(new, encoding="utf-8")
                changed += 1

    # This hardware was replaced by a UVC stereo camera. Keep the original
    # upstream source as reference but do not require its ROS driver to build
    # the base-control package on the S100.
    manifest = WS / "src/ddsm_car_control/package.xml"
    old = manifest.read_text(encoding="utf-8")
    new = old.replace("  <exec_depend>orbbec_camera</exec_depend>\n", "")
    if old != new:
        manifest.write_text(new, encoding="utf-8")
        changed += 1
    for obsolete in (WS / "src/OrbbecSDK_ROS2", WS / "src/vision_opencv"):
        if obsolete.is_dir():
            (obsolete / "COLCON_IGNORE").touch()
    print(f"Prepared {WS}; updated {changed} text files")


if __name__ == "__main__":
    main()
