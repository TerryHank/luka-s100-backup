"""Optional bridge to the household YOLOE TensorRT service on port 8096.

The production 8091 API keeps its existing NanoOWL fallback. Exact household
queries use YOLOE, while descriptive/color queries continue to use NanoOWL.
The bridge also unloads the inactive backend so the two vision models are not
kept in GPU memory together.
"""

from __future__ import annotations

import base64
import json
import pathlib
import time
import urllib.error
import urllib.request

import cv2


BASE_URL = "http://127.0.0.1:8096"
NAMES = {
    "sofa", "chair", "table", "desk", "bed", "cabinet", "wardrobe", "bookshelf", "nightstand", "stool", "bench",
    "refrigerator", "microwave", "oven", "stove", "washing machine", "dryer", "air conditioner", "fan", "television", "computer", "monitor", "printer", "vacuum cleaner",
    "bottle", "cup", "mug", "glass", "bowl", "plate", "fork", "knife", "spoon", "kettle", "pot", "pan", "cutting board", "toaster", "rice cooker",
    "toilet", "sink", "bathtub", "shower", "mirror", "towel", "soap", "toothbrush", "toothpaste", "tissue",
    "scissors", "wire", "book", "bag", "backpack", "keys", "wallet", "phone", "remote control", "clock", "umbrella", "shoe", "clothes", "pillow", "blanket", "trash can",
    "door", "window", "curtain", "light", "fire extinguisher",
}
ALIASES = {
    "沙发": "sofa", "椅子": "chair", "办公椅": "chair", "桌子": "table", "餐桌": "table", "书桌": "desk", "办公桌": "desk",
    "床": "bed", "柜子": "cabinet", "橱柜": "cabinet", "储物柜": "cabinet", "衣柜": "wardrobe", "书架": "bookshelf", "床头柜": "nightstand", "凳子": "stool", "长凳": "bench",
    "冰箱": "refrigerator", "冰柜": "refrigerator", "微波炉": "microwave", "烤箱": "oven", "炉子": "stove", "灶台": "stove", "洗衣机": "washing machine", "烘干机": "dryer",
    "空调": "air conditioner", "风扇": "fan", "电风扇": "fan", "电视": "television", "电视机": "television", "电脑": "computer", "台式机": "computer", "显示器": "monitor", "打印机": "printer", "吸尘器": "vacuum cleaner",
    "瓶子": "bottle", "矿泉水瓶": "bottle", "杯子": "cup", "马克杯": "mug", "玻璃杯": "glass", "碗": "bowl", "盘子": "plate", "叉子": "fork", "刀": "knife", "菜刀": "knife", "勺子": "spoon", "水壶": "kettle", "烧水壶": "kettle", "锅": "pot", "平底锅": "pan", "砧板": "cutting board", "烤面包机": "toaster", "电饭锅": "rice cooker",
    "马桶": "toilet", "厕所": "toilet", "水槽": "sink", "洗手池": "sink", "浴缸": "bathtub", "淋浴": "shower", "花洒": "shower", "镜子": "mirror", "毛巾": "towel", "肥皂": "soap", "香皂": "soap", "牙刷": "toothbrush", "牙膏": "toothpaste", "纸巾": "tissue",
    "剪刀": "scissors", "电线": "wire", "线": "wire", "线缆": "wire", "网线": "wire", "书": "book", "包": "bag", "背包": "backpack", "钥匙": "keys", "钱包": "wallet", "手机": "phone", "电话": "phone", "遥控器": "remote control", "时钟": "clock", "钟": "clock", "雨伞": "umbrella", "伞": "umbrella", "鞋": "shoe", "鞋子": "shoe", "衣服": "clothes", "衣物": "clothes", "枕头": "pillow", "被子": "blanket", "毯子": "blanket", "垃圾桶": "trash can",
    "门": "door", "窗户": "window", "窗": "window", "窗帘": "curtain", "灯": "light", "灯具": "light", "灭火器": "fire extinguisher",
}


def canonical(query: str) -> str | None:
    query = query.strip()
    if query in ALIASES:
        return ALIASES[query]
    lowered = query.lower()
    return lowered if lowered in NAMES else None


def _post(path: str, payload: dict, timeout: float = 8.0) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        BASE_URL + path,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def unload() -> None:
    try:
        _post("/model/unload", {}, timeout=2.0)
    except Exception:
        pass


def loaded() -> bool:
    try:
        with urllib.request.urlopen(BASE_URL + "/health", timeout=0.25) as response:
            return bool(json.loads(response.read().decode("utf-8")).get("model_loaded"))
    except Exception:
        return False


def detect_all(frame):
    """One full-resolution frame, one fixed-vocabulary pass; never load NanoOWL."""
    ok, encoded = cv2.imencode('.png', frame, [int(cv2.IMWRITE_PNG_COMPRESSION), 3])
    if not ok:
        raise ValueError('图像编码失败')
    payload = _post('/infer_image', {'all_objects': True,
        'image_base64': base64.b64encode(encoded.tobytes()).decode('ascii')})
    return {'detections': [{'label': d['class'], 'score': d['confidence'], 'box': d['bbox']}
                           for d in payload.get('detections', [])],
            'inference_seconds': payload.get('inference_seconds')}


def locate(image: pathlib.Path, query: str, prefix: pathlib.Path):
    """Return a production-shaped result, or None for NanoOWL fallback."""
    target = canonical(query)
    if target is None:
        return None
    frame = cv2.imread(str(image))
    if frame is None:
        return None
    ok, encoded = cv2.imencode(".png", frame, [int(cv2.IMWRITE_PNG_COMPRESSION), 3])
    if not ok:
        return None
    payload = _post("/infer_image", {"query": query, "image_base64": base64.b64encode(encoded.tobytes()).decode("ascii")})
    detections = [
        {"label": item["class"], "score": item["confidence"], "box": item["bbox"]}
        for item in payload.get("detections", [])
    ]
    marked = frame.copy()
    for detection in detections:
        x1, y1, x2, y2 = map(int, detection["box"])
        cv2.rectangle(marked, (x1, y1), (x2, y2), (0, 220, 120), 2)
        cv2.putText(marked, f"{detection['label']} {detection['score']:.2f}",
                    (x1, max(20, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                    (0, 220, 120), 2, cv2.LINE_AA)
    prefix = pathlib.Path(prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(prefix.with_suffix(".png")), marked)
    result = {
        "image": str(prefix.with_suffix(".png")),
        "prompt": query,
        "backend": "s100-bpu-yolo11n-coco80",
        "inference_seconds": payload.get("inference_seconds"),
        "top_scores": [d["score"] for d in detections],
        "detections": detections,
    }
    prefix.with_suffix(".json").write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    return result
