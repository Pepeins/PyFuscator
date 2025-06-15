# -*- coding: utf-8 -*-
import os
import sys
import time
from pathlib import Path
from core.obfuscator import PyObfuscator

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def colored_print(text, color=Colors.END):
    print(f"{color}{text}{Colors.END}")

def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
    ██████╗ ██╗   ██╗███████╗██╗   ██╗███████╗ ██████╗ █████╗ ████████╗ ██████╗ ██████╗ 
    ██╔══██╗╚██╗ ██╔╝██╔════╝██║   ██║██╔════╝██╔════╝██╔══██╗╚══██╔══╝██╔═══██╗██╔══██╗
    ██████╔╝ ╚████╔╝ █████╗  ██║   ██║███████╗██║     ███████║   ██║   ██║   ██║██████╔╝
    ██╔═══╝   ╚██╔╝  ██╔══╝  ██║   ██║╚════██║██║     ██╔══██║   ██║   ██║   ██║██╔══██╗
    ██║        ██║   ██║     ╚██████╔╝███████║╚██████╗██║  ██║   ██║   ╚██████╔╝██║  ██║
    ╚═╝        ╚═╝   ╚═╝      ╚═════╝ ╚══════╝ ╚═════╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝
                                    
                                   v0.4 - Python Obfuscator
{Colors.END}"""
    
    print(banner)
    colored_print("=" * 80, Colors.BLUE)
    colored_print(f"👤 User: {os.getenv('USERNAME', 'User')}", Colors.GREEN)
    colored_print(f"📁 Location: Desktop/pyfuscator", Colors.GREEN)
    colored_print(f"🛠️  Techniques: Control Flow Flattening, String Encryption, Dead Code, Opaque Predicates", Colors.YELLOW)
    colored_print("⚠️  Note: Complex f-strings may cause issues - use regular strings for better compatibility", Colors.YELLOW)
    colored_print("=" * 80, Colors.BLUE)

def get_desktop_path():
    home = Path.home()
    desktop_path = home / "Desktop" / "pyfuscator"
    return desktop_path

def setup_directories():
    base_path = get_desktop_path()
    input_path = base_path / "input"
    output_path = base_path / "output"
    
    for path in [input_path, output_path]:
        if not path.exists():
            colored_print(f"📁 Creating directory: {path}", Colors.YELLOW)
            path.mkdir(parents=True, exist_ok=True)
    
    return input_path, output_path

def scan_python_files():
    input_path, _ = setup_directories()
    
    if not input_path.exists():
        colored_print("❌ Error: Could not create input directory", Colors.RED)
        return []
    
    python_files = list(input_path.glob("*.py"))
    
    if not python_files:
        colored_print(f"📝 Info: Place your .py files in '{input_path}' to obfuscate them", Colors.YELLOW)
    
    return python_files

def check_file_for_fstrings(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # simple check for f-strings
            fstring_indicators = ['f"', "f'", 'f"""', "f'''", 'rf"', "rf'", 'fr"', "fr'"]
            has_fstrings = any(indicator in content for indicator in fstring_indicators)
            return has_fstrings
    except:
        return False

def display_file_menu(files):
    colored_print("\n📂 PYTHON FILES FOUND", Colors.HEADER)
    colored_print("=" * 50, Colors.BLUE)
    
    for i, file in enumerate(files, 1):
        file_size = file.stat().st_size
        if file_size < 1024:
            size_str = f"{file_size} bytes"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size/1024:.1f} KB"
        else:
            size_str = f"{file_size/(1024*1024):.1f} MB"
        
        fstring_warning = ""
        if check_file_for_fstrings(file):
            fstring_warning = " ⚠️ (contains f-strings)"
        
        colored_print(f"[{i}] {file.name} ({size_str}){fstring_warning}", Colors.CYAN)
    
    colored_print(f"[{len(files) + 1}] 🔄 Process ALL files", Colors.GREEN)
    colored_print("[0] ❌ Exit", Colors.RED)
    
    if any(check_file_for_fstrings(f) for f in files):
        colored_print("\n⚠️  Files with f-strings detected. If errors occur:", Colors.YELLOW)
        colored_print("   • Disable string obfuscation", Colors.YELLOW)
        colored_print("   • Or replace f-strings with .format() or % formatting", Colors.YELLOW)

def select_files(files):
    if not files:
        return []
    
    display_file_menu(files)
    
    while True:
        try:
            choice = input(f"\n{Colors.BOLD}Select an option (0-{len(files) + 1}): {Colors.END}").strip()
            choice = int(choice)
            
            if choice == 0:
                return []
            elif choice == len(files) + 1:
                return files
            elif 1 <= choice <= len(files):
                return [files[choice - 1]]
            else:
                colored_print(f"❌ Error: Select a number between 0 and {len(files) + 1}", Colors.RED)
        except ValueError:
            colored_print("❌ Error: Enter a valid number", Colors.RED)
        except KeyboardInterrupt:
            colored_print("\n\n👋 Exiting...", Colors.YELLOW)
            return []

def get_obfuscation_options():
    colored_print("\n⚙️  OBFUSCATION CONFIGURATION", Colors.HEADER)
    colored_print("=" * 40, Colors.BLUE)
    
    options = {}
    
    # basic options
    questions = [
        ("obfuscate_strings", "🔤 Obfuscate strings", True),
        ("obfuscate_numbers", "🔢 Obfuscate numbers", True),
        ("obfuscate_names", "🏷️  Obfuscate names (variables/functions)", True),
        ("add_dummy_code", "🗂️  Add dummy code", False),
    ]
    
    for key, prompt, default in questions:
        default_text = "Y/n" if default else "y/N"
        
        # special warnimgs
        if key == "obfuscate_strings":
            colored_print("⚠️  Note: String obfuscation may cause issues with complex f-strings", Colors.YELLOW)
        
        response = input(f"{prompt}? ({default_text}): ").strip().lower()
        
        if default:
            options[key] = response not in ['n', 'no']
        else:
            options[key] = response in ['y', 'yes']
    
    # obfuscation level
    colored_print(f"\n{Colors.HEADER}🎚️  OBFUSCATION LEVEL{Colors.END}", Colors.HEADER)
    colored_print("[1] 🟢 Basic (fast, compatible)", Colors.GREEN)
    colored_print("[2] 🟡 Intermediate (recommended)", Colors.YELLOW)
    colored_print("[3] 🔴 Advanced (slow, maximum security)", Colors.RED)
    
    while True:
        try:
            level = int(input(f"\n{Colors.BOLD}Select level (1-3): {Colors.END}").strip())
            if 1 <= level <= 3:
                options['obfuscation_level'] = level
                break
            else:
                colored_print("❌ Error: Select a number between 1 and 3", Colors.RED)
        except ValueError:
            colored_print("❌ Error: Enter a valid number", Colors.RED)
        except KeyboardInterrupt:
            colored_print("\n\n👋 Exiting...", Colors.YELLOW)
            return None
    
    # advanced options for higher levels
    if options['obfuscation_level'] >= 2:
        colored_print(f"\n{Colors.HEADER}🚀 ADVANCED TECHNIQUES{Colors.END}", Colors.HEADER)
        colored_print("=" * 30, Colors.BLUE)
        
        advanced_questions = [
            ("control_flow_flattening", "🔀 Control Flow Flattening", True),
            ("opaque_predicates", "🧩 Opaque Predicates", True),
            ("string_encryption", "🔐 String Encryption (multi-layer)", True),
            ("dead_code_insertion", "💀 Dead Code Insertion", True),
        ]
        
        for key, prompt, default in advanced_questions:
            default_text = "Y/n" if default else "y/N"
            response = input(f"{prompt}? ({default_text}): ").strip().lower()
            options[key] = response not in ['n', 'no'] if default else response in ['y', 'yes']
    else:
        for key in ['control_flow_flattening', 'opaque_predicates', 'string_encryption', 'dead_code_insertion']:
            options[key] = False
    
    return options

def process_files(files, options):
    _, output_dir = setup_directories()
    obfuscator = PyObfuscator(**options)
    
    colored_print(f"\n🔄 PROCESSING {len(files)} FILE(S)", Colors.HEADER)
    colored_print("=" * 50, Colors.BLUE)
    
    results = {
        'successful': 0,
        'failed': 0,
        'warnings': [],
        'errors': []
    }
    
    for i, file_path in enumerate(files, 1):
        colored_print(f"\n[{i}/{len(files)}] 🔄 Processing: {file_path.name}", Colors.CYAN)
        
        # check for f-strings before processing
        if check_file_for_fstrings(file_path) and options.get('obfuscate_strings', False):
            colored_print("    ⚠️  File contains f-strings - processing carefully...", Colors.YELLOW)
        
        try:
            output_file = output_dir / f"obfuscated_{file_path.name}"
            
            # show progress
            print("    ⏳ Analyzing AST...", end="", flush=True)
            time.sleep(0.1)
            print(" ✅")
            
            print("    ⏳ Applying obfuscation...", end="", flush=True)
            errors = obfuscator.obfuscate_file(file_path, output_file)
            time.sleep(0.1)
            print(" ✅")
            
            print("    ⏳ Generating code...", end="", flush=True)
            time.sleep(0.1)
            print(" ✅")
            
            colored_print(f"    ✅ Completed: {output_file.name}", Colors.GREEN)
            results['successful'] += 1
            
            if errors:
                results['warnings'].extend(errors)
                colored_print(f"    ⚠️  {len(errors)} warning(s) during processing", Colors.YELLOW)
                
        except Exception as e:
            error_message = str(e)
            colored_print(f"    ❌ Error: {error_message}", Colors.RED)
            results['failed'] += 1
            results['errors'].append(f"{file_path.name}: {error_message}")
            
            # specific advice for f-string errors
            if "f-string" in error_message.lower() or "joinedstr" in error_message.lower():
                colored_print(f"    💡 Tip: Disable string obfuscation or convert f-strings to .format()", Colors.BLUE)
    
    return results

def show_results(results, output_dir):
    colored_print(f"\n📊 PROCESSING SUMMARY", Colors.HEADER)
    colored_print("=" * 50, Colors.BLUE)
    
    if results['successful'] > 0:
        colored_print(f"✅ Files processed successfully: {results['successful']}", Colors.GREEN)
    
    if results['failed'] > 0:
        colored_print(f"❌ Files with errors: {results['failed']}", Colors.RED)
    
    if results['warnings']:
        colored_print(f"⚠️  Total warnings: {len(results['warnings'])}", Colors.YELLOW)
    
    colored_print(f"📁 Files saved to: {output_dir}", Colors.CYAN)
    
    # show detailed errors if any
    if results['errors']:
        colored_print(f"\n🔍 DETAILED ERRORS:", Colors.RED)
        for error in results['errors']:
            colored_print(f"  • {error}", Colors.RED)
            
        # show f-string advice if relevant
        fstring_errors = [e for e in results['errors'] if 'f-string' in e.lower() or 'joinedstr' in e.lower()]
        if fstring_errors:
            colored_print(f"\n💡 F-STRING SOLUTIONS:", Colors.BLUE)
            colored_print("  1. Disable string obfuscation", Colors.BLUE)
            colored_print("  2. Replace f-strings with .format():", Colors.BLUE)
            colored_print("     Change: f'Hello {name}'", Colors.BLUE)
            colored_print("     To:     'Hello {}'.format(name)", Colors.BLUE)
            colored_print("  3. Or use % formatting:", Colors.BLUE)
            colored_print("     To:     'Hello %s' % name", Colors.BLUE)
    
    if results['warnings']:
        colored_print(f"\n⚠️  SOME WARNINGS:", Colors.YELLOW)
        for warning in results['warnings'][:5]:  # show first 5 warnings
            colored_print(f"  • {warning}", Colors.YELLOW)
        if len(results['warnings']) > 5:
            colored_print(f"  ... and {len(results['warnings']) - 5} more", Colors.YELLOW)

def main():
    try:
        print_banner()

        python_files = scan_python_files()
        if not python_files:
            colored_print("\n❌ No .py files found in the 'input' folder", Colors.RED)
            input(f"\n{Colors.BOLD}Press Enter to exit...{Colors.END}")
            return
        
        selected_files = select_files(python_files)
        if not selected_files:
            colored_print("\n👋 Goodbye!", Colors.YELLOW)
            return
        
        options = get_obfuscation_options()
        if options is None:
            return
        
        results = process_files(selected_files, options)
        
        _, output_dir = setup_directories()
        show_results(results, output_dir)
        
        if results['successful'] > 0:
            colored_print(f"\n🎉 Process completed! Check the files in the 'output' folder", Colors.GREEN)
        
        input(f"\n{Colors.BOLD}Press Enter to exit...{Colors.END}")
        
    except KeyboardInterrupt:
        colored_print(f"\n\n👋 Program closed by user", Colors.YELLOW)
    except Exception as e:
        colored_print(f"\n💥 Unexpected error: {str(e)}", Colors.RED)
        input(f"\n{Colors.BOLD}Press Enter to exit...{Colors.END}")

if __name__ == "__main__":
    main()
