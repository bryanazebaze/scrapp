#!/usr/bin/env python3
"""
Kali/Dev Environment Cleaner
----------------------------
A smart, interactive cleanup tool for Developers and Security Engineers.
Focuses on: Gradle, Android Studio, Docker, Snap, Apt, and System Logs.

Author: Gemini
"""

import os
import shutil
import subprocess
import sys
import glob
from pathlib import Path
from typing import List, Tuple

# Check for Rich library
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Confirm, Prompt
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
except ImportError:
    print("Error: This script requires the 'rich' library for its UI.")
    print("Please run: pip install rich")
    sys.exit(1)

console = Console()

# --- Utility Functions ---

def get_directory_size(path: Path) -> int:
    """Recursively calculates directory size in bytes."""
    total = 0
    if not path.exists():
        return 0
    try:
        for p in path.rglob('*'):
            if p.is_file():
                total += p.stat().st_size
    except (PermissionError, OSError):
        pass # Skip files we can't read
    return total

def format_bytes(size: int) -> str:
    """Formats bytes into readable strings (MB, GB)."""
    power = 2**10
    n = size
    power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    count = 0
    while n > power:
        n /= power
        count += 1
    return f"{n:.2f} {power_labels[count]}B"

def run_command(command: str, shell=True) -> bool:
    """Runs a shell command and returns Success/Fail."""
    try:
        subprocess.run(command, shell=shell, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

# --- Cleaner Modules ---

class CleanerModule:
    def __init__(self, name, icon):
        self.name = name
        self.icon = icon
        self.size = 0
        self.paths_to_clean: List[Path] = []
        self.available = False

    def scan(self):
        """Scans for files and calculates size."""
        pass

    def clean(self):
        """Performs the cleanup."""
        pass

class GradleCleaner(CleanerModule):
    def __init__(self):
        super().__init__("Gradle", "🐘")

    def scan(self):
        home = Path.home()
        # The massive Gradle cache
        cache_path = home / ".gradle" / "caches"
        
        if cache_path.exists():
            self.available = True
            self.paths_to_clean.append(cache_path)
            self.size = get_directory_size(cache_path)

    def clean(self):
        for path in self.paths_to_clean:
            if path.exists():
                shutil.rmtree(path, ignore_errors=True)

class AndroidCleaner(CleanerModule):
    def __init__(self):
        super().__init__("Android Studio", "🤖")

    def scan(self):
        home = Path.home()
        
        # 1. Build Cache
        build_cache = home / ".android" / "build-cache"
        if build_cache.exists():
            self.paths_to_clean.append(build_cache)

        # 2. IDE Caches (Google folder in .cache)
        # Looks for ~/.cache/Google/AndroidStudio*
        cache_root = home / ".cache" / "Google"
        if cache_root.exists():
            for p in cache_root.glob("AndroidStudio*"):
                self.paths_to_clean.append(p)
        
        # Calculate size
        if self.paths_to_clean:
            self.available = True
            for p in self.paths_to_clean:
                self.size += get_directory_size(p)

    def clean(self):
        for path in self.paths_to_clean:
            if path.exists():
                shutil.rmtree(path, ignore_errors=True)

class DockerCleaner(CleanerModule):
    def __init__(self):
        super().__init__("Docker", "🐳")

    def scan(self):
        # Check if docker is installed
        if shutil.which("docker"):
            self.available = True
            # Difficult to get exact "cleanable" size without running prune dry-run which is slow
            # We will assume it's available if docker exists.
            # We can try to get disk usage
            try:
                output = subprocess.check_output("docker system df --format '{{.Size}}'", shell=True).decode()
                # Very rough parsing, just to show it exists. Real cleanup happens via command.
                self.size = 1  # Signal that it's there
            except:
                self.size = 0

    def clean(self):
        # Prune stopped containers, unused networks, and dangling images
        # -f forces it without confirmation prompt (since we ask in UI)
        run_command("docker system prune -f")

class SystemCleaner(CleanerModule):
    def __init__(self):
        super().__init__("System (Apt & Logs)", "🐧")

    def scan(self):
        self.available = True
        
        # Apt Cache
        apt_cache = Path("/var/cache/apt/archives")
        if apt_cache.exists():
            self.size += get_directory_size(apt_cache)
        
        # Thumbnail Cache (User)
        thumb_cache = Path.home() / ".cache" / "thumbnails"
        if thumb_cache.exists():
            self.paths_to_clean.append(thumb_cache)
            self.size += get_directory_size(thumb_cache)

    def clean(self):
        # Clean Apt
        run_command("sudo apt-get clean")
        run_command("sudo apt-get autoremove -y")
        
        # Clean Journal Logs (Vacuum to 100M)
        run_command("sudo journalctl --vacuum-size=100M")

        # Clean User Files
        for path in self.paths_to_clean:
            if path.exists():
                shutil.rmtree(path, ignore_errors=True)

class SnapCleaner(CleanerModule):
    def __init__(self):
        super().__init__("Snap (Old Revisions)", "👻")

    def scan(self):
        if not shutil.which("snap"):
            return
        
        self.available = True
        # Estimate size of /var/lib/snapd/snaps - this is rough, 
        # as we only delete DISABLED ones, but it gives context.
        snap_path = Path("/var/lib/snapd/snaps")
        if snap_path.exists():
            self.size = get_directory_size(snap_path) // 2 # Rough heuristic: 50% might be old revisions

    def clean(self):
        # Bash script logic to remove disabled snaps
        script = """
        set -eu
        snap list --all | awk '/disabled/{print $1, $3}' |
            while read snapname revision; do
                sudo snap remove "$snapname" --revision="$revision"
            done
        """
        subprocess.run(script, shell=True, executable="/bin/bash")

class FlutterCleaner(CleanerModule):
    def __init__(self):
        super().__init__("Flutter/Dart", "🐦")

    def scan(self):
        # Check for pub cache
        pub_cache = Path.home() / ".pub-cache"
        if pub_cache.exists():
            self.available = True
            self.paths_to_clean.append(pub_cache)
            self.size = get_directory_size(pub_cache)

    def clean(self):
        for path in self.paths_to_clean:
            if path.exists():
                shutil.rmtree(path, ignore_errors=True)

# --- Main Interface ---

def main():
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]Kali/Dev Environment Cleaner[/bold cyan]\n"
        "[dim]Analyze and purge unused artifacts from Android Studio, Gradle, Docker, and Linux[/dim]",
        border_style="cyan"
    ))

    cleaners = [
        GradleCleaner(),
        AndroidCleaner(),
        DockerCleaner(),
        SnapCleaner(),
        SystemCleaner(),
        FlutterCleaner()
    ]

    # --- Scanning Phase ---
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        task = progress.add_task("Scanning system for junk...", total=len(cleaners))
        
        for cleaner in cleaners:
            progress.update(task, description=f"Scanning {cleaner.name}...")
            cleaner.scan()
            progress.advance(task)

    # --- Report Phase ---
    table = Table(title="Scan Results", show_header=True, header_style="bold magenta")
    table.add_column("Environment", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Est. Reclaimable Size", justify="right", style="yellow")

    total_size = 0
    active_cleaners = []

    for cleaner in cleaners:
        if cleaner.available:
            active_cleaners.append(cleaner)
            # For Docker/Snap where size is tricky, we might show a generic message or the calculated one
            size_str = format_bytes(cleaner.size)
            if cleaner.name == "Docker":
                size_str = "Unknown (System Prune)"
            elif cleaner.name == "Snap (Old Revisions)":
                size_str = "~" + size_str 
            else:
                total_size += cleaner.size

            table.add_row(f"{cleaner.icon} {cleaner.name}", "Found", size_str)
        else:
            table.add_row(f"{cleaner.icon} {cleaner.name}", "[dim]Not Found[/dim]", "-")

    console.print(table)
    
    if total_size > 0:
        console.print(f"\n[bold green]Total Confirmed Junk:[/bold green] {format_bytes(total_size)} (plus Docker/Snap savings)")
    else:
        console.print("\n[bold green]Your system is relatively clean![/bold green]")

    if not active_cleaners:
        console.print("[yellow]Nothing to clean. Exiting.[/yellow]")
        return

    # --- Action Phase ---
    console.print("\n[bold red]WARNING:[/bold red] Cleaning Gradle/Maven caches means they will redownload dependencies on next build.")
    if not Confirm.ask("Do you want to proceed with cleaning?"):
        console.print("[red]Aborted.[/red]")
        return

    # Select mode
    console.print("\n[1] Clean Everything (Recommended)")
    console.print("[2] Select specific items")
    choice = Prompt.ask("Choose an option", choices=["1", "2"], default="1")

    modules_to_run = active_cleaners
    if choice == "2":
        modules_to_run = []
        for mod in active_cleaners:
            if Confirm.ask(f"Clean {mod.name}?"):
                modules_to_run.append(mod)

    if not modules_to_run:
        console.print("No modules selected.")
        return

    # Execute
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=False
    ) as progress:
        for mod in modules_to_run:
            task_id = progress.add_task(f"Cleaning {mod.name}...", total=None)
            try:
                mod.clean()
                progress.update(task_id, description=f"[green]Cleaned {mod.name}![/green]")
            except Exception as e:
                progress.update(task_id, description=f"[red]Failed {mod.name}: {str(e)}[/red]")

    console.print("\n[bold green]✨ Cleanup Complete! Enjoy your free space. ✨[/bold green]")
    console.print("[dim]Tip: Run 'df -h' to see your new disk usage.[/dim]")

if __name__ == "__main__":
    main()

