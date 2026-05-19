import os
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import pandas as pd
from api_client import fetch_1min_data
from processor import apply_benchmark, mark_highlight

app = Flask(__name__)
CORS(app)  # 允许跨域（开发用）

# ---------- 前端 HTML 模板（嵌入 Flask）----------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>XAU Showtime · 外汇黄金K线分析</title>
    <!-- Plotly CDN -->
    <script src="https://cdn.plot.ly/plotly-3.0.1.min.js" charset="utf-8"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            background: #0f172a;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            padding: 24px;
            color: #e2e8f0;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: #1e293b;
            border-radius: 28px;
            padding: 24px 28px;
            box-shadow: 0 20px 35px -12px rgba(0,0,0,0.5);
        }
        h1 {
            font-size: 1.8rem;
            background: linear-gradient(135deg, #fbbf24, #f59e0b);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            display: inline-block;
            margin-bottom: 6px;
        }
        .sub {
            color: #94a3b8;
            border-left: 3px solid #f59e0b;
            padding-left: 12px;
            margin: 8px 0 24px 0;
            font-size: 0.9rem;
        }
        .control-panel {
            background: #0f172a;
            border-radius: 20px;
            padding: 20px 24px;
            margin-bottom: 28px;
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            align-items: flex-end;
        }
        .input-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
            min-width: 150px;
        }
        .input-group label {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #cbd5e1;
        }
        input, select {
            background: #1e293b;
            border: 1px solid #334155;
            padding: 10px 12px;
            border-radius: 14px;
            color: #f1f5f9;
            font-size: 0.9rem;
        }
        input:focus, select:focus {
            outline: none;
            border-color: #f59e0b;
        }
        .checkbox-group {
            display: flex;
            gap: 20px;
            background: #1e293b;
            border: 1px solid #334155;
            padding: 8px 20px;
            border-radius: 40px;
        }
        .checkbox-group label {
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            font-weight: normal;
            text-transform: none;
            font-size: 0.85rem;
        }
        button {
            background: #f59e0b;
            border: none;
            padding: 10px 28px;
            border-radius: 40px;
            font-weight: 700;
            color: #0f172a;
            cursor: pointer;
            transition: 0.2s;
            font-size: 0.9rem;
        }
        button:hover {
            background: #eab308;
            transform: translateY(-1px);
        }
        .chart-card {
            background: #0f172a;
            border-radius: 24px;
            padding: 16px;
            margin-top: 10px;
        }
        #chart {
            width: 100%;
            height: 550px;
        }
        .loading {
            text-align: center;
            padding: 40px;
            font-size: 1.2rem;
            color: #f59e0b;
        }
        .stats {
            margin-top: 16px;
            font-size: 0.8rem;
            color: #94a3b8;
            text-align: center;
        }
        .footnote {
            margin-top: 20px;
            font-size: 0.7rem;
            color: #5b6e8c;
            text-align: center;
            border-top: 1px solid #334155;
            padding-top: 16px;
        }
        @media (max-width: 780px) {
            .control-panel { flex-direction: column; align-items: stretch; }
            .checkbox-group { justify-content: center; }
            #chart { height: 400px; }
        }
    </style>
</head>
<body>
<div class="container">
    <h1>⚜️ XAU SHOWTIME</h1>
    <div class="sub">实时外汇/黄金1分钟K线 | 基准偏移分析 | 高亮特定时间周期</div>

    <div class="control-panel">
        <div class="input-group">
            <label>📟 交易品种</label>
            <select id="symbol">
                <option value="XAU/USD" selected>XAU/USD (黄金)</option>
                <option value="EUR/USD">EUR/USD</option>
                <option value="GBP/USD">GBP/USD</option>
                <option value="USD/JPY">USD/JPY</option>
            </select>
        </div>
        <div class="input-group">
            <label>📅 开始日期</label>
            <input type="date" id="startDate">
        </div>
        <div class="input-group">
            <label>📅 结束日期</label>
            <input type="date" id="endDate">
        </div>
        <div class="input-group">
            <label>💰 基准价格 (可选)</label>
            <input type="number" id="benchPrice" step="0.01" placeholder="自动取首根收盘价">
        </div>
        <div class="input-group">
            <label>⏱️ 高亮时间规则</label>
            <div class="checkbox-group">
                <label><input type="checkbox" value="1h" class="lightRule" checked> 1小时整点</label>
                <label><input type="checkbox" value="30min" class="lightRule" checked> 30分钟</label>
                <label><input type="checkbox" value="15min" class="lightRule"> 15分钟</label>
            </div>
        </div>
        <button id="refreshBtn">✨ 查询 & 渲染</button>
    </div>

    <div class="chart-card">
        <div id="chart" class="loading">等待加载数据…</div>
    </div>
    <div class="stats" id="statsInfo"></div>
    <div class="footnote">
        💡 数据来源: Twelve Data | 柱状图数值 = 每分钟收盘价 - 基准价格 | 蓝色柱表示满足高亮规则的时间点<br>
        🕒 默认查询最近一天 (从昨天 00:00 至今天 23:59)，可自定义范围，建议 ≤ 7 天以保证性能。
    </div>
</div>

<script>
    // 设置默认日期: 开始日期为昨天，结束日期为今天
    function setDefaultDates() {
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(today.getDate() - 1);

        const formatDate = (d) => d.toISOString().split('T')[0];
        const startInput = document.getElementById('startDate');
        const endInput = document.getElementById('endDate');
        if (!startInput.value) startInput.value = formatDate(yesterday);
        if (!endInput.value) endInput.value = formatDate(today);
    }

    // 获取高亮规则
    function getActiveRules() {
        const checks = document.querySelectorAll('.lightRule');
        let rules = [];
        checks.forEach(cb => {
            if (cb.checked) rules.push(cb.value);
        });
        return rules;
    }

    // 渲染图表
    function renderChart(data, benchPrice, symbol) {
        const timestamps = data.map(d => d.datetime);
        const offsets = data.map(d => d.offset);
        const highlight = data.map(d => d.highlight);
        const closes = data.map(d => d.close);

        // 定义柱状图颜色
        const colors = highlight.map(hl => hl ? '#3b82f6' : '#e2e8f0');

        const trace = {
            x: timestamps,
            y: offsets,
            type: 'bar',
            marker: {
                color: colors,
                line: { width: 0.6, color: '#475569' }
            },
            hovertemplate: '<b>%{x|%Y-%m-%d %H:%M}</b><br>' +
                           '原始价格: %{customdata[0]:.2f}<br>' +
                           '偏移值: %{y:.4f}<br>' +
                           '%{customdata[1]}<extra></extra>',
            customdata: closes.map((c, idx) => [c, highlight[idx] ? '🔵 高亮时段' : '⚪ 常规'])
        };

        const layout = {
            title: {
                text: `${symbol} 1分钟K线偏移分析 (基准价格: ${benchPrice.toFixed(4)})`,
                x: 0.5,
                font: { size: 18, color: '#f1f5f9' }
            },
            plot_bgcolor: '#0f172a',
            paper_bgcolor: '#1e293b',
            font: { color: '#cbd5e1' },
            xaxis: {
                title: '时间',
                rangeslider: { visible: true },
                type: 'date',
                tickformat: '%m-%d %H:%M'
            },
            yaxis: {
                title: `价格偏移 (close - ${benchPrice.toFixed(4)})`,
                zeroline: true,
                zerolinecolor: '#f59e0b',
                zerolinewidth: 2,
                gridcolor: '#334155'
            },
            hovermode: 'x unified',
            annotations: [{
                xref: 'paper', yref: 'paper',
                x: 0.02, y: 0.98,
                text: "<span style='color:#3b82f6'>🔵 高亮柱</span>   <span style='color:#e2e8f0'>⚪ 普通柱</span>",
                showarrow: false,
                font: { size: 12 },
                bgcolor: 'rgba(0,0,0,0.6)',
                borderpad: 4
            }]
        };

        Plotly.newPlot('chart', [trace], layout, { responsive: true });

        const highlightedCount = highlight.filter(v => v === true).length;
        document.getElementById('statsInfo').innerHTML = `📊 总K线: ${data.length} 根 &nbsp;|&nbsp; 高亮柱: ${highlightedCount} 根 (${(highlightedCount/data.length*100).toFixed(1)}%)`;
    }

    // 调用后端API
    async function fetchData() {
        const symbol = document.getElementById('symbol').value;
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        const benchPriceRaw = document.getElementById('benchPrice').value;
        const rules = getActiveRules();

        if (!startDate || !endDate) {
            alert('请完整填写开始和结束日期');
            return;
        }

        // 显示加载中
        const chartDiv = document.getElementById('chart');
        chartDiv.innerHTML = '<div class="loading">⏳ 正在获取数据，请稍候...</div>';

        const payload = {
            symbol: symbol,
            start_date: startDate,
            end_date: endDate,
            bench_price: benchPriceRaw ? parseFloat(benchPriceRaw) : null,
            light_rules: rules
        };

        try {
            const response = await fetch('/api/chart', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.error || '请求失败');
            }
            renderChart(result.data, result.bench_price, result.symbol);
        } catch (err) {
            chartDiv.innerHTML = `<div class="loading" style="color:#ef4444;">❌ 错误: ${err.message}</div>`;
            console.error(err);
        }
    }

    // 绑定事件
    window.addEventListener('DOMContentLoaded', () => {
        setDefaultDates();
        document.getElementById('refreshBtn').addEventListener('click', fetchData);
        // 初始自动查询
        fetchData();
    });
</script>
</body>
</html>
"""


# ---------- Flask API 路由 ----------
@app.route('/')
def index():
    """返回前端页面"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/chart', methods=['POST'])
def chart_api():
    """
    接收 JSON 参数:
    {
        "symbol": "XAU/USD",
        "start_date": "2025-05-13",
        "end_date": "2025-05-14",
        "bench_price": 2345.00 (可选),
        "light_rules": ["1h", "30min"]
    }
    返回: { "data": [{datetime, offset, highlight, close}], "bench_price": xxx, "symbol": xxx }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "无效请求"}), 400

    symbol = data.get("symbol")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    bench_price = data.get("bench_price")
    light_rules = data.get("light_rules", ["1h", "30min"])

    if not all([symbol, start_date, end_date]):
        return jsonify({"error": "缺少必要参数 symbol, start_date, end_date"}), 400

    try:
        # 1. 获取原始1分钟数据
        df = fetch_1min_data(symbol, start_date, end_date)
        if df.empty:
            return jsonify({"error": "未获取到任何数据，请检查日期范围或品种代码"}), 404

        # 2. 基准价格处理
        if bench_price is None:
            bench_price = df.iloc[0]["close"]
        else:
            bench_price = float(bench_price)

        # 3. 计算偏移 & 高亮标记
        df = apply_benchmark(df, bench_price)
        df["highlight"] = mark_highlight(df, light_rules)

        # 4. 构造返回 JSON (datetime 转为 ISO 字符串)
        response_data = []
        for _, row in df.iterrows():
            response_data.append({
                "datetime": row["datetime"].isoformat(),
                "offset": round(row["offset"], 6),
                "highlight": bool(row["highlight"]),
                "close": round(row["close"], 4)
            })

        return jsonify({
            "symbol": symbol,
            "bench_price": round(bench_price, 4),
            "data": response_data
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"服务器错误: {str(e)}"}), 500


if __name__ == "__main__":
    # 确保 .env 中 API_KEY 已设置
    from config import API_KEY

    app.run(host="0.0.0.0", port=25235, debug=True)