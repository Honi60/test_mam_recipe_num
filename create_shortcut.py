import os
import sys
import shutil
import tempfile
import subprocess

PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
MAIN_PY = os.path.join(PROJECT_DIR, 'main.py')
ICO_USER = os.path.join(PROJECT_DIR, 'receiptCreat.ico')
SHORTCUT_NAME = 'Receipt Tools.lnk'


def get_desktop_path():
    """Get the path to the Desktop folder."""
    # Try OneDrive Desktop first
    userprofile = os.environ.get('USERPROFILE')
    if userprofile:
        onedrive_desktop = os.path.join(userprofile, 'OneDrive', 'Desktop')
        if os.path.exists(onedrive_desktop):
            return onedrive_desktop
        
        # Try regular Desktop
        regular_desktop = os.path.join(userprofile, 'Desktop')
        if os.path.exists(regular_desktop):
            return regular_desktop
    
    # Try environment-based desktop path detection
    user_desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
    if os.path.exists(user_desktop):
        return user_desktop
    
    # Last resort: try to create ~/Desktop
    try:
        os.makedirs(user_desktop, exist_ok=True)
        return user_desktop
    except Exception:
        return None


def create_shortcut(lnk_path, target, args, workdir, icon=''):
    """Create a Windows shortcut using VBScript."""
    # Escape backslashes in paths for VBScript
    lnk_path = lnk_path.replace('\\', '\\\\')
    target = target.replace('\\', '\\\\')
    workdir = workdir.replace('\\', '\\\\')
    icon = icon.replace('\\', '\\\\') if icon else ''
    
    vbs_lines = [
        'Set s = CreateObject("WScript.Shell")',
        f'Set l = s.CreateShortcut("{lnk_path}")',
        f'l.TargetPath = "{target}"',
        f'l.Arguments = {args}',  # args already has quotes
        f'l.WorkingDirectory = "{workdir}"',
    ]
    if icon:
        vbs_lines.append(f'l.IconLocation = "{icon}"')
    vbs_lines.extend(['l.WindowStyle = 1', 'l.Save'])
    vbs = "\n".join(vbs_lines)

    # Create temporary VBS script
    fd, path = tempfile.mkstemp(suffix='.vbs', text=True)
    os.close(fd)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(vbs)
        subprocess.check_call(['cscript', '//nologo', path])
        return True
    except Exception as e:
        print('Failed to create shortcut:', e)
        return False
    finally:
        try:
            os.remove(path)
        except Exception:
            pass


def main():
    # Verify main.py exists
    if not os.path.exists(MAIN_PY):
        print('Error: main.py not found at', MAIN_PY)
        return

    # Get desktop path or fall back to project directory
    desktop = get_desktop_path()
    if desktop:
        print('Found Desktop at:', desktop)
        shortcut_path = os.path.join(desktop, SHORTCUT_NAME)
    else:
        print('Desktop not found, using project directory')
        shortcut_path = os.path.join(PROJECT_DIR, SHORTCUT_NAME)

    # Find Python interpreter (prefer pythonw for no console)
    python_exe = shutil.which('pythonw') or shutil.which('python') or sys.executable
    print('Using Python:', python_exe)

    # Check for icon
    icon = ICO_USER if os.path.exists(ICO_USER) else ''
    if icon:
        print('Using icon:', icon)
    else:
        print('Icon not found:', ICO_USER)

    # Create the shortcut
    if create_shortcut(shortcut_path, python_exe, f'"{MAIN_PY}"', PROJECT_DIR, icon):
        print('Successfully created shortcut at:', shortcut_path)
    else:
        print('Failed to create shortcut')


if __name__ == '__main__':
    main()