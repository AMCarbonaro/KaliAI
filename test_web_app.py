#!/usr/bin/env python3
"""Quick validation script to check web_app.py structure."""

import ast
import sys

def check_gradio_compatibility(file_path):
    """Check if web_app.py is compatible with Gradio 6.0."""
    print("🔍 Checking Gradio 6.0 compatibility...")
    
    with open(file_path, 'r') as f:
        content = f.read()
        tree = ast.parse(content)
    
    issues = []
    
    # Check for old Chatbot parameters
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == 'Chatbot':
                    for keyword in node.keywords:
                        if keyword.arg in ['show_copy_button', 'show_label']:
                            issues.append(f"❌ Found deprecated parameter: {keyword.arg} in Chatbot()")
    
    # Check if theme is in Blocks (should be in launch)
    blocks_has_theme = False
    launch_has_theme = False
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == 'Blocks':
                    for keyword in node.keywords:
                        if keyword.arg == 'theme':
                            blocks_has_theme = True
                            issues.append("❌ theme parameter found in Blocks() - should be in launch()")
                elif node.func.attr == 'launch':
                    for keyword in node.keywords:
                        if keyword.arg == 'theme':
                            launch_has_theme = True
    
    if not blocks_has_theme and launch_has_theme:
        print("✅ Theme correctly placed in launch() method")
    elif blocks_has_theme:
        print("⚠️  Theme found in Blocks() - needs to be moved to launch()")
    
    if not issues:
        print("✅ No deprecated Gradio parameters found")
        print("✅ Code structure looks compatible with Gradio 6.0")
        return True
    else:
        print("\n⚠️  Issues found:")
        for issue in issues:
            print(f"   {issue}")
        return False

if __name__ == "__main__":
    file_path = "kali_orchestrator/web_app.py"
    try:
        result = check_gradio_compatibility(file_path)
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"❌ Error checking file: {e}")
        sys.exit(1)

