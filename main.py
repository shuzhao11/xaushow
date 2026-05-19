import click
import pandas as pd
from pathlib import Path
from api_client import fetch_1min_data
from processor import apply_benchmark, mark_highlight
from visualizer import create_highlighted_barchart, save_chart

@click.command()
@click.option("--symbol", default="XAU/USD", help="交易品种，例如 XAU/USD, EUR/USD")
@click.option("--start", required=True, help="开始日期 YYYY-MM-DD")
@click.option("--end", required=True, help="结束日期 YYYY-MM-DD")
@click.option("--bench", type=float, default=None, help="基准价格，不指定则使用第一根K线的收盘价")
@click.option("--light", multiple=True, type=click.Choice(["1h", "30min", "15min"]),
              default=["1h", "30min"], help="高亮规则，可多选")
@click.option("--output-dir", default="./output", help="输出目录")
def main(symbol, start, end, bench, light, output_dir):
    """
    获取外汇/黄金1分钟K线，计算偏移基准价格，高亮特定时间周期柱状图。
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)

    click.echo(f"🔄 正在获取 {symbol} 从 {start} 到 {end} 的1分钟数据...")
    df = fetch_1min_data(symbol, start, end)
    click.echo(f"✅ 获取到 {len(df)} 条K线")

    # 基准价格处理
    if bench is None:
        bench = df.iloc[0]["close"]
        click.echo(f"📌 未指定基准价格，使用首根收盘价: {bench:.4f}")
    else:
        click.echo(f"📌 使用指定基准价格: {bench:.4f}")

    df = apply_benchmark(df, bench)
    df["highlight"] = mark_highlight(df, list(light))
    click.echo(f"🎨 高亮规则: {', '.join(light)}")

    # 保存原始数据 CSV
    csv_file = output_path / "data.csv"
    df.to_csv(csv_file, index=False, encoding="utf-8-sig")
    click.echo(f"💾 原始数据已保存: {csv_file}")

    # 生成图表
    fig = create_highlighted_barchart(df, bench, symbol)
    html_file = output_path / "chart.html"
    save_chart(fig, html_file)
    click.echo(f"📈 交互式图表已生成: {html_file}")

    # 打印统计信息
    highlighted_count = df["highlight"].sum()
    click.echo(f"\n📊 统计: 总K线 {len(df)} 根, 其中高亮柱 {highlighted_count} 根 ({highlighted_count/len(df)*100:.1f}%)")

if __name__ == "__main__":
    main()