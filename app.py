import datetime as dt
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import pandas as pd
from api_client import fetch_1min_data

app = Flask(__name__)
CORS(app)


# ---------- 休市时段判断（北京时间）----------
def is_settlement_hour(beijing_time: datetime) -> bool:
    if beijing_time.weekday() >= 5:
        return False
    hour = beijing_time.hour
    minute = beijing_time.minute
    if (hour == 5) or (hour == 6 and minute == 0):
        return True
    if (hour == 6) or (hour == 7 and minute == 0):
        return True
    return False


# ---------- 前端模板 ----------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XAU Showtime · 动态填充色</title>
    <script src="https://cdn.plot.ly/plotly-3.0.1.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0f172a; font-family: system-ui; padding: 24px; color: #e2e8f0; }
        .container { max-width: 1400px; margin: auto; background: #1e293b; border-radius: 28px; padding: 24px; }
        h1 { font-size: 1.8rem; background: linear-gradient(135deg, #fbbf24, #f59e0b); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .sub { color: #94a3b8; border-left: 3px solid #f59e0b; padding-left: 12px; margin: 8px 0 24px; }
        .control-panel { background: #0f172a; border-radius: 20px; padding: 20px; margin-bottom: 28px; display: flex; flex-wrap: wrap; gap: 20px; align-items: flex-end; }
        .input-group { display: flex; flex-direction: column; gap: 8px; min-width: 130px; }
        .input-group label { font-size: 0.75rem; font-weight: 600; color: #cbd5e1; }
        input, select { background: #1e293b; border: 1px solid #334155; padding: 10px 12px; border-radius: 14px; color: #f1f5f9; }
        .radio-group { display: flex; gap: 20px; background: #1e293b; border: 1px solid #334155; padding: 8px 20px; border-radius: 40px; }
        .radio-group label { display: flex; align-items: center; gap: 8px; }
        button { background: #f59e0b; border: none; padding: 10px 28px; border-radius: 40px; font-weight: 700; color: #0f172a; cursor: pointer; }
        button:hover { background: #eab308; }
        .chart-card { background: #0f172a; border-radius: 24px; padding: 16px; }
        #chart { width: 100%; height: 600px; }
        .stats { margin-top: 16px; font-size: 0.8rem; text-align: center; }
        .footnote { margin-top: 20px; font-size: 0.7rem; color: #5b6e8c; text-align: center; }
    </style>
</head>
<body>
<div class="container">
    <h1>⚜️ XAU SHOWTIME · 动态填充色</h1>
    <div class="sub">下跌→前一根标黄 | 上涨→后一根标亮白</div>

    <div class="control-panel">
        <div class="input-group"><label>品种</label><select id="symbol">
            <option value="XAU/USD" selected>XAU/USD (现货黄金)</option>
            <option value="EUR/USD">EUR/USD</option>
            <option value="GBP/USD">GBP/USD</option>
            <option value="USD/JPY">USD/JPY</option>
        </select></div>
        <div class="input-group"><label>开始</label><input type="date" id="startDate"></div>
        <div class="input-group"><label>结束</label><input type="date" id="endDate"></div>
        <div class="input-group"><label>基准价</label><input type="number" id="benchPrice" step="0.01" placeholder="自动"></div>
        <div class="input-group"><label>Δ阈值</label><input type="number" id="delta" step="1" value="15"></div>
        <div class="input-group"><label>高亮规则</label><div class="radio-group">
            <label><input type="radio" name="lightRule" value="1h"> 1h</label>
            <label><input type="radio" name="lightRule" value="30min"> 30min</label>
            <label><input type="radio" name="lightRule" value="15min" checked> 15min</label>
        </div></div>
        <button id="refreshBtn">渲染</button>
    </div>

    <div class="chart-card"><div id="chart">加载中…</div></div>
    <div class="stats" id="statsInfo"></div>
    <div class="footnote">💡 相邻高亮价差>Δ：虚线连接，下跌（前高后低）→前一根黄色填充；上涨（前低后高）→后一根亮白填充。</div>
</div>

<script>
    let rawData = null;
    function setDefaultDates() {
        const today = new Date();
        const yesterday = new Date(today); yesterday.setDate(today.getDate()-1);
        const fmt = d => d.toISOString().split('T')[0];
        if(!document.getElementById('startDate').value) document.getElementById('startDate').value = fmt(yesterday);
        if(!document.getElementById('endDate').value) document.getElementById('endDate').value = fmt(today);
    }
    function getSelectedLightRule() { return document.querySelector('input[name="lightRule"]:checked').value; }

    function renderChart() {
        if (!rawData || !rawData.data.length) return;
        const { data, bench_price, symbol, delta, light_rule } = rawData;
        const timestamps = data.map(d => d.timestamp);
        const offsets = data.map(d => d.offset);
        const highlight = data.map(d => d.highlight);
        const closes = data.map(d => d.close);
        const datetimeStrs = data.map(d => d.datetime_str);

        const diffMap = {};
        data.forEach((d, idx) => { if(d.diff_info) diffMap[idx] = d.diff_info; });

        const barColors = highlight.map((h,i) => (h && offsets[i] !== null) ? '#3b82f6' : '#e2e8f0');
        const trace = {
            x: timestamps, y: offsets, type: 'bar', name: '偏移',
            marker: { color: barColors, line: { width: 0.6, color: '#475569' } },
            hovertemplate: '<b>%{customdata[2]}</b><br>原始价: %{customdata[0]:.2f}<br>偏移: %{y:.4f}<br>%{customdata[1]}<extra></extra>',
            customdata: closes.map((c,i) => [c, highlight[i] ? '🔵高亮' : '⚪常规', datetimeStrs[i]])
        };

        let shapes = [], annotations = [];
        for (let i = 0; i < data.length; i++) {
            const info = diffMap[i];
            if (!info || !info.diff_gt_delta) continue;
            const prevIdx = info.prev_hl_idx;
            const currIdx = info.curr_hl_idx;
            const prevOff = offsets[prevIdx];
            const currOff = offsets[currIdx];
            const prevTime = timestamps[prevIdx];
            const currTime = timestamps[currIdx];
            const diffVal = info.abs_diff;
            if (prevOff === null || currOff === null) continue;

            // 虚线连接（从低价柱顶到高价柱顶）
            const lowY = Math.min(prevOff, currOff);
            const highY = Math.max(prevOff, currOff);
            const lowTime = prevOff < currOff ? prevTime : currTime;
            const highTime = prevOff < currOff ? currTime : prevTime;
            shapes.push({
                type: 'line', x0: lowTime, y0: lowY, x1: highTime, y1: highY,
                line: { color: '#fbbf24', width: 2, dash: 'dot' }, xref: 'x', yref: 'y'
            });

            // 判断涨跌并确定需要填充的K线索引和颜色
            const isDown = prevOff > currOff;  // 下跌：前一根价格高
            let fillIdx, fillColor;
            if (isDown) {
                fillIdx = prevIdx;   // 前一根标黄
                fillColor = 'rgba(250,204,21,0.4)';   // 黄色
            } else {
                fillIdx = currIdx;   // 后一根标亮白
                fillColor = 'rgba(255,255,255,0.6)';  // 亮白
            }
            const fillTime = timestamps[fillIdx];
            const barHalf = 30 * 1000;
            shapes.push({
                type: 'rect', x0: fillTime - barHalf, x1: fillTime + barHalf,
                y0: lowY, y1: highY,
                fillcolor: fillColor, line: { width: 0 }, xref: 'x', yref: 'y'
            });

            // 差值标注
            annotations.push({
                x: (prevTime + currTime) / 2, y: (prevOff + currOff) / 2,
                xref: 'x', yref: 'y', text: `Δ=${diffVal.toFixed(2)}`, showarrow: true,
                arrowhead: 2, arrowsize: 0.8, arrowcolor: '#fbbf24', bgcolor: '#0f172a',
                font: { color: '#fbbf24', size: 11 }, bordercolor: '#fbbf24', borderwidth: 0.5
            });
        }

        const layout = {
            title: `${symbol} 1分钟偏移 (基准:${bench_price.toFixed(4)}) | Δ阈值:${delta} | 高亮:${light_rule}`,
            plot_bgcolor: '#0f172a', paper_bgcolor: '#1e293b', font: { color: '#cbd5e1' },
            xaxis: { title: '时间 (北京时间)', type: 'date', rangeslider: { visible: true }, tickformat: '%m-%d %H:%M', tickangle: 45 },
            yaxis: { title: `偏移值`, zeroline: true, zerolinecolor: '#f59e0b', gridcolor: '#334155' },
            hovermode: 'x unified', shapes, annotations
        };
        Plotly.newPlot('chart', [trace], layout, { responsive: true });
        const valid = data.filter(d => d.offset !== null).length;
        const hl = data.filter((d,i)=> d.highlight && offsets[i] !== null).length;
        const links = Object.values(diffMap).filter(v=>v && v.diff_gt_delta).length;
        document.getElementById('statsInfo').innerHTML = `📊 总:${data.length} 有效:${valid} 高亮:${hl} 连线:${links}`;
    }

    async function fetchAndRender() {
        const symbol = document.getElementById('symbol').value;
        const start = document.getElementById('startDate').value;
        const end = document.getElementById('endDate').value;
        const benchRaw = document.getElementById('benchPrice').value;
        const delta = parseFloat(document.getElementById('delta').value);
        const lightRule = getSelectedLightRule();
        if (!start || !end) return alert("请填写日期");
        document.getElementById('chart').innerHTML = '<div style="padding:40px;">⏳ 加载中...</div>';
        try {
            const resp = await fetch('/api/chart', {
                method: 'POST', headers: {'Content-Type':'application/json'},
                body: JSON.stringify({ symbol, start_date: start, end_date: end,
                    bench_price: benchRaw ? parseFloat(benchRaw) : null,
                    light_rule: lightRule, delta: delta })
            });
            const result = await resp.json();
            if (!resp.ok) throw new Error(result.error);
            rawData = result;
            renderChart();
        } catch(err) {
            document.getElementById('chart').innerHTML = `<div style="color:#ef4444;">❌ ${err.message}</div>`;
        }
    }

    window.addEventListener('DOMContentLoaded', () => {
        setDefaultDates();
        document.getElementById('refreshBtn').addEventListener('click', fetchAndRender);
        fetchAndRender();
    });
</script>
</body>
</html>
"""


# ---------- Flask API ----------
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/chart', methods=['POST'])
def chart_api():
    req = request.get_json()
    if not req:
        return jsonify({"error": "无效请求"}), 400
    symbol = req.get("symbol")
    start_date = req.get("start_date")
    end_date = req.get("end_date")
    bench_price = req.get("bench_price")
    light_rule = req.get("light_rule", "30min")
    delta = float(req.get("delta", 15.0))
    if not all([symbol, start_date, end_date]):
        return jsonify({"error": "缺少参数"}), 400
    try:
        start_str = f"{start_date} 00:00:00"
        today_str = datetime.now().strftime("%Y-%m-%d")
        if end_date >= today_str:
            end_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            end_str = f"{end_date} 23:59:59"
        df = fetch_1min_data(symbol, start_str, end_str)
        if df.empty:
            return jsonify({"error": "无数据"}), 404
        if bench_price is None:
            bench_price = df.iloc[0]["close"]
        else:
            bench_price = float(bench_price)
        df["offset"] = df["close"] - bench_price
        df["offset"] = pd.to_numeric(df["offset"], errors='coerce').fillna(0.0)

        # 高亮规则
        def get_minute(t):
            try:
                return int(t.split(' ')[1].split(':')[1])
            except:
                return 0

        df["minute"] = df["datetime_str"].apply(get_minute)
        if light_rule == "1h":
            df["highlight"] = df["minute"] == 0
        elif light_rule == "30min":
            df["highlight"] = df["minute"].isin([0, 30])
        else:
            df["highlight"] = df["minute"] % 15 == 0
        # 休市过滤
        df["beijing_dt"] = pd.to_datetime(df["datetime_str"])
        df["is_settlement"] = df["beijing_dt"].apply(is_settlement_hour)
        df.loc[df["is_settlement"], "offset"] = None
        df.loc[df["is_settlement"], "highlight"] = False
        # 相邻高亮价差分析
        hl_idx = df[(df["highlight"]) & (df["offset"].notnull())].index.tolist()
        diff_info = [None] * len(df)
        for i in range(1, len(hl_idx)):
            cur = hl_idx[i]
            prev = hl_idx[i - 1]
            cur_off = df.loc[cur, "offset"]
            prev_off = df.loc[prev, "offset"]
            if cur_off is None or prev_off is None:
                continue
            abs_diff = abs(cur_off - prev_off)
            if abs_diff > delta:
                diff_info[cur] = {
                    "diff_gt_delta": True,
                    "abs_diff": float(abs_diff),
                    "prev_hl_idx": int(prev),
                    "curr_hl_idx": int(cur)
                }
            else:
                diff_info[cur] = {"diff_gt_delta": False}
        # 构造返回
        response = []
        for idx, row in df.iterrows():
            ts = int(row["beijing_dt"].timestamp() * 1000)
            response.append({
                "timestamp": ts,
                "datetime_str": row["datetime_str"],
                "offset": None if pd.isna(row["offset"]) else float(row["offset"]),
                "highlight": bool(row["highlight"]),
                "close": float(row["close"]),
                "diff_info": diff_info[idx] if idx < len(diff_info) else None
            })
        return jsonify({
            "symbol": symbol,
            "bench_price": round(bench_price, 4),
            "delta": delta,
            "light_rule": light_rule,
            "data": response
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=25258, debug=True)