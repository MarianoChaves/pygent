import rich
import sys

def test_print_rich_version():
    print(f"sys.path: {sys.path}")
    print(f"rich.__version__: {rich.__version__}")
    print(f"rich.__file__: {rich.__file__}")
    # Try the problematic import directly here
    try:
        from rich.table import Table
        print("Successfully imported Table from rich.table in test_rich_version")
    except Exception as e:
        print(f"Error importing Table from rich.table in test_rich_version: {e}")
    assert rich.__version__ is not None
