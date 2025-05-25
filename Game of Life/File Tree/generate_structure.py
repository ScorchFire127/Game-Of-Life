import os
import sys
import traceback
import subprocess
import time # Needed for delays when finding the new window
# --- Attempt to import pywin32 modules ---
try:
    import win32gui
    import win32com.client
    import pythoncom
except ImportError:
    print("ERROR: The 'pywin32' library is required for this script.")
    print("Please install it using: pip install pywin32")
    sys.exit(1)

# --- Helper function to get window path using COM objects ---
# This is the most reliable way to check what path an Explorer window is showing
def get_explorer_window_path(hwnd):
    try:
        shell = win32com.client.Dispatch("Shell.Application")
        for window in shell.Windows():
            if window.HWND == hwnd:
                 try:
                     url = window.LocationURL
                     if url.startswith('file:///'):
                         from urllib.parse import unquote
                         path = unquote(url[8:].replace('/', '\\'))
                     else:
                         path = url

                     return os.path.normpath(path)
                 except Exception:
                     return None
        return None
    except Exception as e:
        # print(f"DEBUG: Error in get_explorer_window_path for HWND {hwnd}: {e}", file=sys.stderr)
        return None

# --- Helper function to find a window by its path ---
def find_explorer_window_by_path(target_path):
    target_path_norm = os.path.normpath(target_path)
    try:
        shell = win32com.client.Dispatch("Shell.Application")
        for window in shell.Windows():
             window_path_norm = get_explorer_window_path(window.HWND)
             if window_path_norm and os.path.exists(window_path_norm):
                  try:
                     if os.path.samefile(window_path_norm, target_path_norm):
                         return window # Return the COM window object
                  except Exception:
                      pass
        return None
    except Exception as e:
        print(f"ERROR: Error enumerating shell windows: {e}", file=sys.stderr)
        return None

# --- Main Directory Structure Generation Logic (Same as before) ---
def generate_directory_structure(root_dir, output_file, prefix="", ignore_list=None):
    """
    Recursively generates a directory tree structure, ignoring specified items
    only at the immediate root_dir level of this call.
    """
    if ignore_list is None:
        ignore_list = []

    try:
        all_items_in_dir = os.listdir(root_dir)
        items = [item for item in all_items_in_dir if item not in ignore_list]
        items.sort()
    except PermissionError:
        error_msg = f"[Permission Denied for '{os.path.basename(root_dir)}']"
        print(f"ERROR: {error_msg} ({root_dir})", file=sys.stderr)
        try: output_file.write(f"{prefix}└── {error_msg}\n")
        except Exception as e_write_err: print(f"ERROR: Failed to write error message to file: {e_write_err}", file=sys.stderr)
        return
    except FileNotFoundError:
        error_msg = f"[Directory Not Found during scan of '{os.path.basename(root_dir)}']"
        print(f"ERROR: {error_msg} ({root_dir})", file=sys.stderr)
        try: output_file.write(f"{prefix}└── {error_msg}\n")
        except Exception as e_write_err: print(f"ERROR: Failed to write error message to file: {e_write_err}", file=sys.stderr)
        return
    except Exception as e_gds_listdir:
        error_msg = f"[Error listing directory '{os.path.basename(root_dir)}']"
        print(f"ERROR: Unexpected error listing dir '{root_dir}': {e_gds_listdir}", file=sys.stderr)
        try: output_file.write(f"{prefix}└── {error_msg}\n")
        except Exception as e_write_err: print(f"ERROR: Failed to write error message to file: {e_write_err}", file=sys.stderr)
        return

    for i, item_name in enumerate(items):
        path = os.path.join(root_dir, item_name)
        is_last = (i == len(items) - 1)
        connector = "└── " if is_last else "├── "
        line_to_write = f"{prefix}{connector}{item_name}\n"

        try:
            output_file.write(line_to_write)
        except Exception as e_write:
            print(f"ERROR: Error writing item '{item_name}' ('{path}') to output file: {e_write}", file=sys.stderr)

        if os.path.isdir(path):
            new_prefix = prefix + ("    " if is_last else "│   ")
            generate_directory_structure(path, output_file, new_prefix, [])


def main():
    output_filename = "structure.txt"
    script_parent_dir = "" # Initialize

    try:
        # --- Determine paths based on the script's own location ---
        script_path = os.path.abspath(__file__)
        script_parent_dir = os.path.dirname(script_path) # Directory where script is run from and output is saved
        scan_directory_root = os.path.dirname(os.path.normpath(script_parent_dir)) # Directory one level up to scan

        folder_to_ignore_name = os.path.basename(os.path.normpath(script_parent_dir))
        items_to_ignore = [folder_to_ignore_name]

        # --- Handle root directory edge case ---
        if os.path.normpath(scan_directory_root) == os.path.normpath(script_parent_dir):
            print(f"INFO: Script appears to be in a root directory ('{script_parent_dir}'). Scanning this root directly.")
            items_to_ignore = []
            scan_directory_root = os.path.normpath(script_parent_dir)
        else:
             print(f"INFO: Script is in '{folder_to_ignore_name}'. Scanning parent directory '{scan_directory_root}' and ignoring '{folder_to_ignore_name}'.")

        # --- Validate scan_directory_root ---
        if not os.path.isdir(scan_directory_root):
            print(f"FATAL ERROR: The calculated scan directory '{scan_directory_root}' is not a valid directory. Exiting.")
            sys.exit(1)

        # --- Ensure the output directory exists and is writable ---
        if not os.path.isdir(script_parent_dir):
             print(f"FATAL ERROR: Script's parent directory '{script_parent_dir}' does not exist unexpectedly. Exiting.")
             sys.exit(1)

        if not os.access(script_parent_dir, os.W_OK):
            print(f"FATAL ERROR: No write permissions for the script's directory '{script_parent_dir}' to save '{output_filename}'. Exiting.")
            sys.exit(1)

        # --- Construct full output file path ---
        full_output_path = os.path.join(script_parent_dir, output_filename)

        # --- Determine the name to display for the root of the tree ---
        actual_root_name_for_display = os.path.basename(os.path.normpath(scan_directory_root))
        if not actual_root_name_for_display:
            actual_root_name_for_display = os.path.normpath(scan_directory_root)

        # --- File Creation and Writing ---
        print(f"INFO: Generating structure of '{scan_directory_root}' (excluding '{folder_to_ignore_name}' if applicable) into '{full_output_path}'...")
        try:
            with open(full_output_path, 'w', encoding='utf-8') as f_struct:
                f_struct.write(actual_root_name_for_display + "\n")
                generate_directory_structure(scan_directory_root, f_struct, prefix="", ignore_list=items_to_ignore)
            print(f"SUCCESS: Directory structure successfully written to '{full_output_path}'.")

        except IOError as e_io:
             print(f"FATAL ERROR (IOError) during file operation: {e_io}", file=sys.stderr)
             print(f"Please check permissions and disk space for '{full_output_path}'.", file=sys.stderr)
             sys.exit(1)
        except Exception as e_write_block:
            print(f"FATAL UNEXPECTED ERROR within file writing block: {e_write_block}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)

        # --- Window Manipulation Logic using pywin32 ---
        print("\nINFO: Starting File Explorer window manipulation...")
        target_dir_norm = os.path.normpath(script_parent_dir)
        found_window = None
        window_rect = None # To store position and size (left, top, right, bottom)

        try:
            # 1. Find an existing window displaying the target path
            print(f"INFO: Searching for existing Explorer window displaying '{target_dir_norm}'...")
            found_window = find_explorer_window_by_path(target_dir_norm)

            if found_window:
                print(f"INFO: Found existing window (HWND: {found_window.HWND}) for '{target_dir_norm}'.")
                # 2. Get its location
                try:
                    window_rect = win32gui.GetWindowRect(found_window.HWND)
                    print(f"INFO: Captured window position/size: {window_rect}")
                except Exception as e_get_rect:
                     print(f"WARNING: Could not get window rectangle for HWND {found_window.HWND}: {e_get_rect}", file=sys.stderr)
                     window_rect = None

                # 3. Close that specific window
                print(f"INFO: Closing window HWND {found_window.HWND}...")
                try:
                    found_window.Quit()
                    print(f"INFO: Close command issued for HWND {found_window.HWND}.")
                    # Reduce sleep time - might need adjustment based on OS speed
                    time.sleep(0.3) # Give the window a moment to start closing
                except Exception as e_close:
                    print(f"ERROR: Failed to close window HWND {found_window.HWND}: {e_close}", file=sys.stderr)
                    found_window = None

            else:
                print(f"INFO: No existing Explorer window found displaying '{target_dir_norm}'.")


        except Exception as e_find_close:
             print(f"ERROR: An error occurred during the window finding/closing phase: {e_find_close}", file=sys.stderr)
             traceback.print_exc(file=sys.stderr)


        # 4. Open a new window for the same path
        print(f"\nINFO: Opening a new Explorer window for '{target_dir_norm}'...")
        try:
            subprocess.Popen(['explorer', target_dir_norm])
            print(f"INFO: 'explorer {target_dir_norm}' command issued via subprocess.Popen.")
        except Exception as e_popen:
            print(f"FATAL ERROR: Failed to open new explorer window: {e_popen}", file=sys.stderr)
            print("Please manually open the directory:", target_dir_norm, file=sys.stderr)
            sys.exit(1)

        # 5. Set the new window to the old location (if location was captured)
        if window_rect:
            print("INFO: Attempting to find the newly opened window and set its position...")
            new_window_hwnd = None
            # Poll for the new window - adjusted parameters for speed
            search_attempts = 20 # More attempts
            search_delay = 0.1 # Shorter delay (Total timeout = 20 * 0.1 = 2 seconds)

            for i in range(search_attempts):
                 # print(f"DEBUG: Searching for new window, attempt {i+1}/{search_attempts}...") # Too verbose
                 # Need to re-dispatch Shell.Application or refresh its view? Let's rely on find_explorer_window_by_path
                 newly_found_com_window = find_explorer_window_by_path(target_dir_norm)

                 if newly_found_com_window:
                     new_window_hwnd = newly_found_com_window.HWND
                     print(f"INFO: Found new window (HWND: {new_window_hwnd}) after {i+1} attempts.")
                     break # Found the new window, exit search loop

                 time.sleep(search_delay) # Wait before next attempt

            if new_window_hwnd:
                print(f"INFO: Setting position/size of new window (HWND: {new_window_hwnd}) to {window_rect}...")
                try:
                    left, top, right, bottom = window_rect
                    width = right - left
                    height = bottom - top
                    # Use SWP_SHOWWINDOW flag (0x0040) potentially helps visibility right after positioning
                    # Also ensure it's not minimized or maximized before setting pos
                    win32gui.ShowWindow(new_window_hwnd, win32gui.SW_RESTORE) # Restore if minimized/maximized
                    win32gui.SetWindowPos(new_window_hwnd, None, left, top, width, height, win32gui.SWP_SHOWWINDOW) # Added SWP_SHOWWINDOW
                    print("SUCCESS: Window position/size updated.")
                except Exception as e_set_pos:
                    print(f"ERROR: Failed to set position/size for new window HWND {new_window_hwnd}: {e_set_pos}", file=sys.stderr)
                    print("Please manually adjust the window.", file=sys.stderr)
            else:
                 print(f"WARNING: Could not find the newly opened window for '{target_dir_norm}' within timeout. Cannot set position.")
                 print("The directory should still be open in a default location.", file=sys.stderr)
        else:
            print("INFO: Old window location not captured. Cannot set position for the new window.")


        # --- Final Information ---
        print(f"\nINFO: Script finished.")

    except Exception as e_main:
        print(f"FATAL UNEXPECTED ERROR in main execution flow: {e_main}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # Initialize COM library
    try:
        pythoncom.CoInitialize()
    except pythoncom.com_error:
        pass # COM is already initialized

    main()

    # Uninitialize COM library
    try:
        pythoncom.CoUninitialize()
    except pythoncom.com_error:
        pass # Ignore