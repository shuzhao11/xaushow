import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots

def create_highlighted_barchart(df: pd.DataFrame, bench_price: float, symbol: str) -> go.Figure:
    """生成柱状图，高亮柱为蓝色，普通柱为空白色"""
    # 根据高亮标记分配颜色
    colors = ["#3b82f6" if hl else "#e2e8f0" for hl in df["highlight"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["datetime"],
        y=df["offset"],
        marker_color=colors,
        marker_line_width=0.5,
        marker_line_color="#475569",
        name="价格偏移",
        hovertemplate=(
            "<b>%{x|%Y-%m-%d %H:%M}</b><br>"
            "原始价格: %{customdata[0]:.2f}<br>"
            "偏移值: %{y:.4f}<br>"
            "%{customdata[1]}"
            "<extra></extra>"
        ),
        customdata=df[["close", "highlight"]].apply(
            lambda row: (row["close"], "🔵 高亮时段" if row["highlight"] else "⚪ 常规"), axis=1
        )
    ))

    fig.update_layout(
        title=dict(
            text=f"{symbol} 1分钟K线偏移分析 (基准价格: {bench_price:.2f})",
            x=0.5,
            font=dict(size=18)
        ),
        xaxis=dict(
            title="时间",
            rangeslider=dict(visible=True),
            type="date"
        ),
        yaxis=dict(
            title=f"价格偏移 (close - {bench_price:.2f})",
            zeroline=True,
            zerolinecolor="#f59e0b",
            zerolinewidth=2
        ),
        plot_bgcolor="#0f172a",
        paper_bgcolor="#1e293b",
        font=dict(color="#e2e8f0"),
        hovermode="x unified"
    )

    # 添加图例说明
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        text="<span style='color:#3b82f6'>🔵 高亮柱</span>   <span style='color:#e2e8f0'>⚪ 普通柱</span>",
        showarrow=False,
        font=dict(size=12),
        align="left",
        bgcolor="rgba(0,0,0,0.6)"
    )
    return fig

def save_chart(fig: go.Figure, output_path: str):
    """保存为 HTML 文件"""
    fig.write_html(output_path, include_plotlyjs="cdn")