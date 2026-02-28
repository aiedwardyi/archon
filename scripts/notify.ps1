# Bell + taskbar flash notification
[console]::beep(523,150)
[console]::beep(659,150)
[console]::beep(784,300)

if (-not ([System.Management.Automation.PSTypeName]'WindowFlasher').Type) {
    Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WindowFlasher {
    [StructLayout(LayoutKind.Sequential)]
    public struct FLASHWINFO {
        public uint cbSize;
        public IntPtr hwnd;
        public uint dwFlags;
        public uint uCount;
        public uint dwTimeout;
    }
    [DllImport("user32.dll")]
    public static extern bool FlashWindowEx(ref FLASHWINFO pwfi);

    public static void Flash(IntPtr hwnd) {
        FLASHWINFO fi = new FLASHWINFO();
        fi.cbSize = (uint)System.Runtime.InteropServices.Marshal.SizeOf(fi);
        fi.hwnd = hwnd;
        fi.dwFlags = 15;  // FLASHW_ALL | FLASHW_TIMERNOFG
        fi.uCount = 0;    // flash until focused
        fi.dwTimeout = 0;
        FlashWindowEx(ref fi);
    }
}
"@
}

# Find the terminal window — match any known terminal, title must contain 'Claude'
$term = Get-Process | Where-Object {
    $_.MainWindowHandle -ne 0 -and
    $_.ProcessName -in @('WindowsTerminal','ghostty','Ghostty','alacritty','wezterm-gui','ConEmu64','mintty','cmd','powershell','pwsh') -and
    $_.MainWindowTitle -match 'Claude'
} | Select-Object -First 1

if ($term) {
    [WindowFlasher]::Flash([IntPtr]$term.MainWindowHandle)
} else {
    # Fallback: flash ANY terminal window with a handle
    $fallback = Get-Process | Where-Object {
        $_.MainWindowHandle -ne 0 -and
        $_.ProcessName -in @('WindowsTerminal','ghostty','Ghostty','alacritty','wezterm-gui','ConEmu64','mintty')
    } | Select-Object -First 1
    if ($fallback) {
        [WindowFlasher]::Flash([IntPtr]$fallback.MainWindowHandle)
    }
}
