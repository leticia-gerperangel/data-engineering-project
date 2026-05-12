from pathlib import Path

current_dir = Path.cwd()
current_file = Path(__file__).name

print(f"Files in: {current_dir}\n")

for filepath in sorted(current_dir.iterdir()):
    if filepath.name == current_file:
        continue
    
    print(f"- {filepath.name}")
    
    if filepath.is_file():
        try:
            # Try UTF-8 first, then UTF-16 if it fails
            try:
                content = filepath.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                content = filepath.read_text(encoding='utf-16')
            
            content = content.strip()
            
            if content:
                first_line = content.splitlines()[0]
                print(f"  {first_line[:120]}{'...' if len(first_line) > 120 else ''}")
            else:
                print("  (empty file)")
                
        except Exception:
            print("  (binary file - cannot display content)")
    
    print()  # spacing