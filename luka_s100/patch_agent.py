"""Use a compact S100 chat prompt to reduce CPU prefill latency."""

from pathlib import Path

path = Path("/home/sunrise/luka_s100/ddsm_car_ws/src/nav_llm_agent/nav_llm_agent/agent_node.py")
code = path.read_text(encoding="utf-8")
start = code.index("    def _build_chat_system_prompt(self) -> str:\n")
end = code.index("\n    def _publish_status(self, text: str) -> None:", start)
new = '''    def _build_chat_system_prompt(self) -> str:
        return (
            "你是小车语音助手露卡。用自然、亲切、具体的中文回答，别编造事实或使用表情符号。"
            "聊天时回应用户的话题；必要时问一个贴切的问题。"
            "导航、巡航、寻物、音乐等动作由工具执行；只有工具确认成功才说已完成。"
            "目前 S100 外设未接入，不能声称小车已移动或已看到现场。"
        )
'''
if code[start:end] != new.rstrip("\n"):
    path.write_text(code[:start] + new.rstrip("\n") + code[end:], encoding="utf-8")
