"""Select the S100 BPU service while preserving the 8091 API and data."""

from pathlib import Path

root = Path("/home/sunrise/luka_s100/locateanything_trial_20260907")
app = root / "live_app.py"
code = app.read_text(encoding="utf-8")
code = code.replace("from model_runtime_nanoowl import ModelRuntime",
                    "from s100_model_runtime import ModelRuntime")
code = code.replace("model_backend='yoloe' if yoloe_active", "model_backend='s100_bpu_coco80' if yoloe_active")
code = code.replace(".input.jpg", ".input.png").replace("input.jpg", "input.png")
app.write_text(code, encoding="utf-8")

bridge = root / "yoloe_bridge.py"
code = bridge.read_text(encoding="utf-8")
code = code.replace("yoloe-home70-tensorrt", "s100-bpu-yolo11n-coco80")
code = code.replace("cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])",
                    "cv2.imencode('.png', frame, [int(cv2.IMWRITE_PNG_COMPRESSION), 3])")
code = code.replace('cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 92])',
                    'cv2.imencode(".png", frame, [int(cv2.IMWRITE_PNG_COMPRESSION), 3])')
bridge.write_text(code, encoding="utf-8")

memory = root / "semantic_memory.py"
code = memory.read_text(encoding="utf-8")
code = code.replace("yoloe-home70-tensorrt", "s100-bpu-yolo11n-coco80")
memory.write_text(code, encoding="utf-8")
