import os
import sys
import winreg
from pathlib import Path


def get_font_path(font_name: str) -> Path | None:
    """
    Finds the absolute path of a font file on Windows given its name.

    Args:
        font_name: The name of the font to search for (e.g., "Arial", "Meiryo UI").
                   The search is case-insensitive.

    Returns:
        The absolute path to the font file if found, otherwise None.
    """
    # Path to the registry key where font information is stored
    font_registry_key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"

    # The default directory for fonts in Windows
    # We use os.environ['SystemRoot'] to get the path to the Windows directory (e.g., C:\Windows)
    fonts_dir = os.path.join(os.environ["SystemRoot"], "Fonts")

    # The font name to search for, converted to lowercase for case-insensitive matching
    search_font_name = font_name.lower()

    try:
        # Open the registry key for reading.
        # The 'with' statement ensures the key is automatically closed.
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, font_registry_key_path, 0, winreg.KEY_READ
        ) as key:
            i = 0
            while True:
                try:
                    # Enumerate over the values in the registry key.
                    # Each font has a value name (e.g., "Arial (TrueType)") and value data (e.g., "arial.ttf").
                    value_name, file_name, value_type = winreg.EnumValue(key, i)

                    # Check if the desired font name is part of the registry entry's name.
                    # This handles variations like "(TrueType)", "(Bold)", etc.
                    if search_font_name in value_name.lower():
                        # If a match is found, construct the full path to the font file.
                        font_path = os.path.join(fonts_dir, file_name)

                        # Verify that the file actually exists before returning the path.
                        if os.path.exists(font_path):
                            return Path(font_path)

                    i += 1
                except OSError:
                    # This exception is raised when there are no more values to enumerate.
                    # It signals the end of the loop.
                    break

    except FileNotFoundError:
        # This occurs if the registry key itself does not exist (very unlikely on a Windows system).
        print(f"Error: Font registry key not found at '{font_registry_key_path}'")
        return None
    except Exception as e:
        # Catch any other unexpected errors during registry access.
        print(f"An unexpected error occurred: {e}")
        return None

    # If the loop completes without finding the font, return None.
    return None


if __name__ == "__main__":
    # --- Example Usage ---

    font_to_find = sys.argv[1]
    path = get_font_path(font_to_find)
    if path:
        print(f"Font '{font_to_find}' found at: {path}")
    else:
        print(f"Font '{font_to_find}' not found.")
