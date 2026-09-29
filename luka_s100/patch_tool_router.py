"""Reduce S100 CPU tool-selection prefill while preserving grounding rules."""

from pathlib import Path

path = Path("/home/sunrise/luka_s100/ddsm_car_ws/tools/nx_assistant_tools.py")
code = path.read_text(encoding="utf-8")
start = code.index("def prompt():\n")
end = code.index("\ndef polite_command(text):", start)
new = '''def prompt():
 return ("你是露卡的工具选择器，只返回JSON。可用工具：" + ",".join(TOOLS) +
         "。闲聊选chat，含糊请求选clarify；每次只选一个。问能力用settings_help，不执行动作。"
         "导航仅选原话中的已保存航点，房间不用object_bring；找物用find_object，已找到物品带路用object_bring。"
         "不要编造目标或执行否定、假设、引用中的动作。")
'''
if code[start:end] != new + "\n":
    path.write_text(code[:start] + new + code[end:], encoding="utf-8")
