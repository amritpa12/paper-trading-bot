from rich.console import Console
from rich.table import Table
from stats import daily_summary, strategy_stats

console = Console()

summary = daily_summary()
if summary:
    console.print(f"[bold]Daily PnL Summary ({summary['date']})[/bold]")
    console.print(f"Trades: {summary['trades']} | Total PnL: {summary['total_pnl']:.2f} | Win Rate: {summary['win_rate']:.0%}")
else:
    console.print("No trades logged for today.")

stats = strategy_stats()
if stats is not None and not stats.empty:
    table = Table(title="Strategy Performance")
    table.add_column("Strategy")
    table.add_column("Trades", justify="right")
    table.add_column("Total PnL", justify="right")
    table.add_column("Avg PnL", justify="right")
    table.add_column("Win Rate", justify="right")

    for _, row in stats.iterrows():
        table.add_row(
            row["strategy"],
            str(int(row["trades"])),
            f"{row['total_pnl']:.2f}",
            f"{row['avg_pnl']:.2f}",
            f"{row['win_rate']:.0%}",
        )

    console.print(table)
else:
    console.print("No strategy stats yet.")
