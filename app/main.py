def main():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from streamlit.web import cli as stcli
    import sys

    app_path = str(Path(__file__).parent / "ui" / "streamlit_app.py")
    sys.argv = ["streamlit", "run", app_path]
    stcli.main()
