"""Software-stage COCO detector API for S100's preinstalled YOLO11 BPU model.

This deliberately advertises only classes the model supports. It does not
pretend to provide the NX's open-vocabulary NanoOWL/YOLOE behavior.
"""

from base64 import b64decode
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from threading import Lock
from types import SimpleNamespace
import json
import sys
import time

import cv2
import numpy as np

SAMPLE = Path("/app/pydev_demo/02_detection_sample/02_ultralytics_yolo11/ultralytics_yolo11.py")
MODEL = Path("/opt/hobot/model/s100/basic/yolo11n_detect_nashe_640x640_nv12.hbm")
LABELS = Path("/app/res/labels/coco_classes.names")
sys.path.insert(0, "/app/pydev_demo")
spec = spec_from_file_location("s100_official_yolo11_object", SAMPLE)
module = module_from_spec(spec)
spec.loader.exec_module(module)
NAMES = [line.strip() for line in LABELS.read_text().splitlines()]

ALIASES = {
    "沙发": "sofa", "椅子": "chair", "餐桌": "diningtable", "桌子": "diningtable",
    "床": "bed", "冰箱": "refrigerator", "微波炉": "microwave", "烤箱": "oven",
    "瓶子": "bottle", "矿泉水瓶": "bottle", "杯子": "cup", "碗": "bowl",
    "书": "book", "手机": "cell phone", "遥控器": "remote", "剪刀": "scissors",
    "电视": "tvmonitor", "电视机": "tvmonitor", "背包": "backpack", "手提包": "handbag",
    "马桶": "toilet", "洗手池": "sink", "钟": "clock", "时钟": "clock",
}


class Detector:
    def __init__(self):
        opt = SimpleNamespace(model_path=str(MODEL), score_thres=0.30)
        self.model = module.YoloV11(opt)
        self.model.set_scheduling_params(priority=0, bpu_cores=[0])
        self.lock = Lock()

    def infer(self, image):
        height, width = image.shape[:2]
        with self.lock:
            inputs = self.model.pre_process(image)
            raw = self.model.forward(inputs)
            boxes, ids, scores = self.model.post_process(raw, width, height)
        return [{"class": NAMES[int(cls)], "confidence": round(float(score), 4),
                 "bbox": np.rint(box).astype(int).tolist()}
                for box, cls, score in zip(boxes, ids, scores)]


detector = None
detector_lock = Lock()


class Handler(BaseHTTPRequestHandler):
    def reply(self, body, status=200):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            return self.reply({"ok": True, "model_loaded": detector is not None,
                               "backend": "s100-bpu-yolo11n-coco80",
                               "classes": len(NAMES), "open_vocabulary": False})
        self.reply({"error": "not found"}, 404)

    def do_POST(self):
        global detector
        if self.path == "/model/unload":
            with detector_lock:
                detector = None
            return self.reply({"ok": True})
        if self.path != "/infer_image":
            return self.reply({"error": "not found"}, 404)
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 12_000_000:
                raise ValueError("invalid request size")
            request = json.loads(self.rfile.read(size))
            raw = b64decode(request["image_base64"], validate=True)
            if len(raw) > 8_000_000:
                raise ValueError("image too large")
            image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
            if image is None or image.shape[0] * image.shape[1] > 8_000_000:
                raise ValueError("invalid image")
            query = str(request.get("query") or "").strip()
            target = ALIASES.get(query, query.lower())
            if query and target not in NAMES:
                return self.reply({"error": "unsupported_class", "query": query,
                                   "backend": "s100-bpu-yolo11n-coco80"}, 422)
            with detector_lock:
                if detector is None:
                    detector = Detector()
                active = detector
            started = time.monotonic()
            results = active.infer(image)
            if query:
                results = [row for row in results if row["class"] == target]
            return self.reply({"detections": results,
                               "inference_seconds": round(time.monotonic() - started, 4),
                               "backend": "s100-bpu-yolo11n-coco80"})
        except (ValueError, KeyError, TypeError) as exc:
            self.reply({"error": str(exc)}, 400)
        except Exception as exc:
            self.reply({"error": type(exc).__name__}, 503)


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8096), Handler).serve_forever()
