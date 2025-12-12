from pathlib import Path
import subprocess
import sys

def test_build_script_runs(tmp_path):
    # smoke: script runs and emits HTML file
    repo = Path(__file__).resolve().parents[1]
    out = subprocess.run([sys.executable, str(repo/"scripts"/"build_todo_board_html.py")],
                         cwd=str(repo), capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    html_path = repo/"docs"/"00_overview"/"PEAK_TRADE_TODO_BOARD.html"
    assert html_path.exists()
    txt = html_path.read_text(encoding="utf-8", errors="replace")
    assert "Peak_Trade – TODO Board" in txt
