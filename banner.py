from rich.console import Console

console = Console()

VERSION = "1.0.0"

def show_banner():
    console.print(r"""[bold red]
██████╗ ███████╗██████╗  █████╗ 
██╔══██╗██╔════╝██╔══██╗██╔══██╗
██████╔╝█████╗  ██║  ██║███████║
██╔══██╗██╔══╝  ██║  ██║██╔══██║
██████╔╝███████╗██████╔╝██║  ██║
╚═════╝ ╚══════╝╚═════╝ ╚═╝  ╚═╝
[/bold red]""")
    console.print(f"[bold red]Beda v{VERSION}[/bold red]")
    console.print("[yellow]Advanced HTTPS Brute Force Tool[/yellow]")
    console.print("[dim]Auto CSRF • Session • IP Rotation via Tor[/dim]")
    console.print("[dim]Developed by Youssef Mediouni[/dim]")
    console.print("[dim]For educational purposes and authorized testing only[/dim]\n")
