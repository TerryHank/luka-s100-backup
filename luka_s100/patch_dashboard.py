"""Keep the S100 staging UI read-only until hardware commissioning."""

from pathlib import Path

path = Path("/home/sunrise/luka_s100/ddsm_car_ws/tools/nx_dashboard.py")
code = path.read_text(encoding="utf-8")
old = """def post(self):
    if self.path.split('?',1)[0]=='/api/people/stop':"""
new = """def post(self):
    import os
    if os.getenv('LUKA_SOFTWARE_ONLY') == '1':
        return self.send_json({'error': 'S100 尚未接入外设，当前为只读软件验证模式'}, 503)
    if self.path.split('?',1)[0]=='/api/people/stop':"""
if old in code:
    path.write_text(code.replace(old, new, 1), encoding="utf-8")
elif new in code:
    print("already patched")
else:
    raise RuntimeError("dashboard POST handler changed; refusing to patch")

code = path.read_text(encoding="utf-8")
anchor = "if __name__ == '__main__':\n    app.main()"
notice = """if __import__('os').getenv('LUKA_SOFTWARE_ONLY') == '1':
    app.HTML = app.HTML.replace('NX 小车导航', 'S100 软件迁移验证')
    app.HTML = app.HTML.replace('<header>', '<div style="padding:12px;background:#714d19;color:#fff;font-size:16px">S100 软件迁移验证：外设尚未接入；所有操作按钮当前禁用。</div><header>', 1)
    app.HTML = app.HTML.replace('</body>', '<script>document.querySelectorAll("button").forEach(b=>{b.disabled=true;b.title="请待硬件接入和实车验收后启用"})</script></body>')

"""
if notice not in code:
    if anchor not in code:
        raise RuntimeError("dashboard main entry changed; refusing to patch")
    path.write_text(code.replace(anchor, notice + anchor), encoding="utf-8")
