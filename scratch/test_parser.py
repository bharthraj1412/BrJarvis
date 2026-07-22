from tools.registry import parse_tool_call

test_text = """<|start|>assistant<|channel|>commentary to=repo_browser.run_code <|constrain|>json<|message|>{
  "code": "import os, subprocess, sys, platform, shlex, subprocess\\nfilename='Cybersecurity_Learning_Roadmap.docx'\\nif platform.system()=='Windows':\\n    subprocess.run(['start', '', filename], shell=True)\\nelif platform.system()=='Darwin':\\n    subprocess.run(['open', filename])\\nelse:\\n    subprocess.run(['xdg-open', filename])\\nprint('Attempted to open file')\\n",
  "lang": "python",
  "timeout": 120
}<|call|>"""

tool_name, args = parse_tool_call(test_text)
print(f"Tool Name: {tool_name}")
print(f"Args Keys: {list(args.keys()) if args else None}")
print(f"Code snippet: {args.get('code')[:60].strip() if args else None}")
