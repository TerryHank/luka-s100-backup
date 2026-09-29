"""Select S100 BPU person detection in the copied worker, leaving NX intact."""

from pathlib import Path

path = Path("/home/sunrise/luka_s100/person_follow/worker.py")
code = path.read_text(encoding="utf-8")
old = """            if requested not in ('peoplenet', 'yolo'):
                raise ValueError('NX_PERSON_DETECTOR 只能是 peoplenet 或 yolo')
            if requested == 'yolo':
"""
new = """            if requested not in ('peoplenet', 'yolo', 'bpu'):
                raise ValueError('NX_PERSON_DETECTOR 只能是 peoplenet、yolo 或 bpu')
            if requested == 'bpu':
                from s100_bpu_person import BpuPersonDetector
                detector = BpuPersonDetector(confidence=.35)
                self.person_detector.update(active='s100_bpu_yolo11n', confidence=.35)
            elif requested == 'yolo':
"""
if old in code:
    path.write_text(code.replace(old, new, 1), encoding="utf-8")
elif new in code:
    print("already patched")
else:
    raise RuntimeError("worker detector block changed; refusing to patch")
