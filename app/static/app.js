const statusBadge = document.querySelector("#statusBadge");
const symbolCount = document.querySelector("#symbolCount");
const candleCount = document.querySelector("#candleCount");
const latestCandle = document.querySelector("#latestCandle");
const openaiState = document.querySelector("#openaiState");
const paperTradeCount = document.querySelector("#paperTradeCount");
const scanDate = document.querySelector("#scanDate");
const candidateRows = document.querySelector("#candidateRows");
const sectorFilter = document.querySelector("#sectorFilter");
const verdictFilter = document.querySelector("#verdictFilter");
const sectorState = document.querySelector("#sectorState");
const sectorGrid = document.querySelector("#sectorGrid");
const reportBox = document.querySelector("#reportBox");
const refreshBtn = document.querySelector("#refreshBtn");
const scanBtn = document.querySelector("#scanBtn");
const aiScanBtn = document.querySelector("#aiScanBtn");
const liveBtn = document.querySelector("#liveBtn");
const autoLiveBtn = document.querySelector("#autoLiveBtn");
const repairBtn = document.querySelector("#repairBtn");
const liveState = document.querySelector("#liveState");
const liveRows = document.querySelector("#liveRows");
const copyReportBtn = document.querySelector("#copyReportBtn");
const openPositions = document.querySelector("#openPositions");
const closedPositions = document.querySelector("#closedPositions");
const winRate = document.querySelector("#winRate");
const unrealizedPnl = document.querySelector("#unrealizedPnl");
const realizedPnl = document.querySelector("#realizedPnl");
const portfolioRows = document.querySelector("#portfolioRows");
const portfolioState = document.querySelector("#portfolioState");
const symbolSearch = document.querySelector("#symbolSearch");
const symbolListState = document.querySelector("#symbolListState");
const symbolGrid = document.querySelector("#symbolGrid");
const strategyState = document.querySelector("#strategyState");
const strategyTabs = document.querySelector("#strategyTabs");
const strategySummary = document.querySelector("#strategySummary");
const strategyRows = document.querySelector("#strategyRows");
const chartTitle = document.querySelector("#chartTitle");
const chartState = document.querySelector("#chartState");
const chartInterval = document.querySelector("#chartInterval");
const refreshChartBtn = document.querySelector("#refreshChartBtn");
const stockChart = document.querySelector("#stockChart");
const chartScreener = document.querySelector("#chartScreener");
const chartStrategyBadges = document.querySelector("#chartStrategyBadges");
const strategyVisualBox = document.querySelector("#strategyVisualBox");
const momentumStrategyBox = document.querySelector("#momentumStrategyBox");
const breakoutStrategyBox = document.querySelector("#breakoutStrategyBox");
const newsBox = document.querySelector("#newsBox");
const fundamentalsBox = document.querySelector("#fundamentalsBox");
const longTermResearchBox = document.querySelector("#longTermResearchBox");
const fundamentalDashboardTitle = document.querySelector("#fundamentalDashboardTitle");
const fundamentalDashboardState = document.querySelector("#fundamentalDashboardState");
const fundamentalDashboard = document.querySelector("#fundamentalDashboard");

let allSymbols = [];
let latestCandidates = [];
let strategyCatalog = [];
let selectedStrategyId = "all";
let autoLiveTimer = null;
let bootstrapTimer = null;
let currentStatus = null;
let selectedSymbol = null;
let activeChart = { candles: [], candidate: {}, start: 0, end: 0, dragging: false, dragX: 0 };

function formatNumber(value) {
  return new Intl.NumberFormat("en-IN").format(value || 0);
}

function formatPrice(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  return Number(value).toFixed(2);
}

function formatCompact(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "-";
  }
  return new Intl.NumberFormat("en-IN", { notation: "compact", maximumFractionDigits: 2 }).format(number);
}

function isNseTradingHours(now = new Date()) {
  const day = now.getDay();
  if (day === 0 || day === 6) {
    return false;
  }
  const ist = new Date(now.toLocaleString("en-US", { timeZone: "Asia/Kolkata" }));
  const minutes = ist.getHours() * 60 + ist.getMinutes();
  return minutes >= 9 * 60 + 15 && minutes <= 15 * 60 + 30;
}

function setStatus(text) {
  statusBadge.textContent = text;
}

async function getJson(url, options = {}) {
  const timeoutMs = options.timeoutMs || 90000;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    signal: controller.signal,
    ...options,
  });
  clearTimeout(timer);
  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `${response.status} ${response.statusText}`);
  }
  return response.json();
}

async function loadStatus() {
  const status = await getJson("/status");
  currentStatus = status;
  symbolCount.textContent = formatNumber(status.candle_stats.symbols);
  candleCount.textContent = formatNumber(status.candle_stats.candles);
  latestCandle.textContent = status.candle_stats.latest_candle_date || "-";
  openaiState.textContent = status.openai_configured ? "Ready" : "Fallback";
  paperTradeCount.textContent = formatNumber(status.paper_trades_count || 0);
  setStatus(status.data_provider === "yahoo" ? "Free data mode" : "Broker data mode");
  liveState.textContent =
    status.data_provider === "yahoo"
      ? "Using Yahoo/yfinance delayed data"
      : status.zerodha_configured
        ? "Ready for Zerodha LTP"
        : `Missing ${status.missing_zerodha_credentials.join(", ")}`;
  liveBtn.disabled = status.data_provider !== "yahoo" && !status.zerodha_configured;
  if (repairBtn) {
    const needsRepair = status.app_env === "production" && Number(status.candle_stats.symbols || 0) < 90;
    repairBtn.classList.toggle("attention", needsRepair);
    repairBtn.textContent = status.bootstrap?.running ? "Repairing" : needsRepair ? "Repair Data" : "Repair Data";
    repairBtn.disabled = Boolean(status.bootstrap?.running);
    if (needsRepair && !status.bootstrap?.running) {
      liveState.textContent = `${liveState.textContent} - hosted history is partial; click Repair Data`;
    }
  }
}

function renderSymbols() {
  const query = symbolSearch.value.trim().toUpperCase();
  const filtered = allSymbols.filter((item) => item.symbol.includes(query));

  symbolListState.textContent = `${filtered.length} of ${allSymbols.length} shown`;
  if (!filtered.length) {
    symbolGrid.innerHTML = '<span class="empty">No symbols match that search.</span>';
    return;
  }

  symbolGrid.innerHTML = filtered
    .map(
      (item) => `
        <span class="symbol-chip ${item.hasCandles ? "stored" : "missing"}" title="${item.hasCandles ? "Candles stored" : "No candle data stored"}">
          ${item.symbol}
        </span>
      `
    )
    .join("");
}

function setSectorOptions(candidates) {
  const sectors = Array.from(new Set(candidates.map((item) => item.sector || "Other"))).sort();
  const current = sectorFilter.value;
  sectorFilter.innerHTML = '<option value="all">All sectors</option>';
  sectors.forEach((sector) => {
    const option = document.createElement("option");
    option.value = sector;
    option.textContent = sector;
    sectorFilter.appendChild(option);
  });
  sectorFilter.value = sectors.includes(current) ? current : "all";
}

function renderSectorView(candidates) {
  const bySector = new Map();
  candidates.forEach((item) => {
    const sector = item.sector || "Other";
    const bucket = bySector.get(sector) || {
      sector,
      total: 0,
      setupCount: 0,
      avgScore: 0,
      leaders: [],
    };
    bucket.total += 1;
    bucket.avgScore += Number(item.score || 0);
    if (["strong_watchlist", "possible_breakout", "near_breakout"].includes(item.verdict)) {
      bucket.setupCount += 1;
    }
    bucket.leaders.push(item);
    bySector.set(sector, bucket);
  });

  const sectors = Array.from(bySector.values())
    .map((item) => ({
      ...item,
      avgScore: item.total ? Math.round(item.avgScore / item.total) : 0,
      leaders: item.leaders.sort((a, b) => Number(b.score || 0) - Number(a.score || 0)).slice(0, 3),
    }))
    .sort((a, b) => b.setupCount - a.setupCount || b.avgScore - a.avgScore);

  sectorState.textContent = `${sectors.length} sectors`;
  if (!sectors.length) {
    sectorGrid.innerHTML = '<span class="empty">No sector analytics available.</span>';
    return;
  }

  sectorGrid.innerHTML = sectors
    .map(
      (item) => `
        <button class="sector-tile" data-sector="${item.sector}">
          <span>${item.sector}</span>
          <strong>${item.setupCount}/${item.total}</strong>
          <small>Avg score ${item.avgScore} - ${item.leaders.map((leader) => leader.symbol).join(", ")}</small>
        </button>
      `
    )
    .join("");
}

function strategyById(strategyId) {
  return strategyCatalog.find((item) => item.id === strategyId);
}

function strategyLabels(ids) {
  return (ids || [])
    .slice(0, 4)
    .map((id) => strategyById(id)?.label || id.replaceAll("_", " "))
    .join(", ");
}

function strategyItems(ids) {
  return (ids || []).map((id) => strategyById(id) || { id, label: id.replaceAll("_", " "), basis: "" });
}

function candidatesForStrategy(strategyId) {
  const tradable = latestCandidates.filter((item) => item.verdict !== "data_missing");
  if (strategyId === "all") {
    return tradable;
  }
  return tradable.filter((item) => (item.strategy_matches || []).includes(strategyId));
}

function renderStrategyTabs() {
  if (!strategyTabs) {
    return;
  }
  const tabs = [{ id: "all", number: 0, label: "All", status: "active", basis: "All scanned Nifty 100 stocks." }, ...strategyCatalog];
  strategyTabs.innerHTML = tabs
    .map((strategy) => {
      const count = candidatesForStrategy(strategy.id).length;
      const muted = strategy.status !== "active" && strategy.status !== "active_daily_proxy" ? "muted-tab" : "";
      return `
        <button class="strategy-tab ${strategy.id === selectedStrategyId ? "active" : ""} ${muted}" data-strategy="${strategy.id}" title="${strategy.basis}">
          <span>${strategy.number ? `${strategy.number}. ` : ""}${strategy.label}</span>
          <strong>${count}</strong>
        </button>
      `;
    })
    .join("");
  renderStrategyRows();
}

function renderStrategyRows() {
  if (!strategyRows) {
    return;
  }
  const selected = selectedStrategyId === "all" ? null : strategyById(selectedStrategyId);
  const rows = candidatesForStrategy(selectedStrategyId);
  const hasScan = latestCandidates.length > 0;
  const statusText = selected?.status?.replaceAll("_", " ") || "active";
  strategyState.textContent =
    selectedStrategyId === "all"
      ? `${rows.length} scanned stocks across active strategy buckets`
      : `${selected?.label || "Strategy"} - ${statusText}`;
  strategySummary.textContent =
    selected?.basis ||
    "Each stock can appear in multiple strategy tabs because a breakout can also be a momentum, price-action, or moving-average setup.";

  if (selected && !["active", "active_daily_proxy"].includes(selected.status)) {
    strategyRows.innerHTML = `
      <tr>
        <td colspan="10" class="empty">
          This strategy needs extra data or a dedicated backtest before it should produce live stock signals.
        </td>
      </tr>
    `;
    return;
  }

  if (!rows.length) {
    strategyRows.innerHTML = hasScan
      ? '<tr><td colspan="10" class="empty">No Nifty 100 stocks currently match this strategy.</td></tr>'
      : '<tr><td colspan="10" class="empty">No scan data loaded yet. Click Run Scan to classify Nifty 100 stocks across strategy tabs.</td></tr>';
    return;
  }

  strategyRows.innerHTML = rows
    .slice()
    .sort((a, b) => Number(b.score || 0) - Number(a.score || 0))
    .map((item) => {
      const plan = item.trade_plan || {};
      const features = item.features || {};
      const reason = item.reasons?.[0] || item.risk_flags?.[0] || "Multi-factor scanner match";
      return `
        <tr data-symbol="${item.symbol}">
          <td class="symbol-cell"><strong>${item.symbol}</strong></td>
          <td>${item.sector || "Other"}</td>
          <td class="verdict ${item.verdict}">${item.verdict.replaceAll("_", " ")}</td>
          <td class="score">${item.score}</td>
          <td>${features.candle_pattern || "-"}</td>
          <td>${features.volume_vs_20d ? `${features.volume_vs_20d}x` : "-"}</td>
          <td>${formatPrice(plan.entry_price)}</td>
          <td>${formatPrice(plan.stop_loss)}</td>
          <td>${formatPrice(plan.target_1)}</td>
          <td title="${reason}">${reason}</td>
        </tr>
      `;
    })
    .join("");
}

async function loadStrategies() {
  const payload = await getJson("/strategies");
  strategyCatalog = payload.strategies || [];
  renderStrategyTabs();
}

async function loadSymbols() {
  const [universe, stored] = await Promise.all([getJson("/universe/default"), getJson("/symbols")]);
  const storedSet = new Set(stored.symbols || []);
  const universeSymbols = universe.nifty100 || [];
  const merged = Array.from(new Set([...universeSymbols, ...(stored.symbols || [])])).sort();
  allSymbols = merged.map((symbol) => ({
    symbol,
    hasCandles: storedSet.has(symbol),
  }));
  renderSymbols();
}

function renderCandidates(candidates) {
  const sector = sectorFilter.value;
  const verdict = verdictFilter.value;
  const filtered = candidates.filter((item) => {
    const sectorOk = sector === "all" || (item.sector || "Other") === sector;
    const verdictOk = verdict === "all" || item.verdict === verdict;
    return sectorOk && verdictOk;
  });

  if (!filtered.length) {
    candidateRows.innerHTML = '<tr><td colspan="17" class="empty">No candidates found.</td></tr>';
    return;
  }

  candidateRows.innerHTML = filtered
    .map((item) => {
      const volume = item.features?.volume_vs_20d ? `${item.features.volume_vs_20d}x` : "-";
      const support = item.features?.support_20d ? formatPrice(item.features.support_20d) : "-";
      const plan = item.trade_plan || {};
      const strategy = item.strategy_profile || {};
      const prediction = strategy.prediction || {};
      const matchedTabs = strategyLabels(item.strategy_matches);
      const tradable = item.verdict !== "data_missing" && Number(plan.entry_price || 0) > 0;
      const encodedPlan = encodeURIComponent(JSON.stringify(plan));
      const encodedStrategy = encodeURIComponent(JSON.stringify(strategy));
      const risk = item.risk_flags?.length ? item.risk_flags.join("; ") : plan.notes?.join("; ") || "Clear";
      return `
        <tr data-symbol="${item.symbol}" data-plan="${encodedPlan}" data-strategy="${encodedStrategy}">
          <td class="symbol-cell"><strong>${item.symbol}</strong></td>
          <td>${item.sector || "Other"}</td>
          <td>${strategy.strategy_label || "-"}</td>
          <td title="${matchedTabs || "-"}">${matchedTabs || "-"}</td>
          <td title="${prediction.summary || ""}">${prediction.bias || "-"} / ${prediction.confidence || "-"}</td>
          <td class="verdict ${item.verdict}">${item.verdict.replaceAll("_", " ")}</td>
          <td class="score">${item.score}</td>
          <td>${tradable ? formatPrice(item.close) : "-"}</td>
          <td>${formatPrice(plan.entry_price)}</td>
          <td>${formatPrice(plan.stop_loss)}</td>
          <td>${formatPrice(plan.target_1)}</td>
          <td>${tradable ? formatPrice(item.breakout_level) : "-"}</td>
          <td>${support}</td>
          <td>${volume}</td>
          <td title="${risk}">${plan.risk_grade ?? "Clear"}</td>
          <td><input class="qty-input" type="number" min="1" value="1" aria-label="Quantity for ${item.symbol}" ${tradable ? "" : "disabled"} /></td>
          <td>
            <div class="trade-actions">
              <button class="buy-btn" data-action="BUY" ${tradable ? "" : "disabled"}>Buy</button>
              <button class="sell-btn" data-action="SELL" ${tradable ? "" : "disabled"}>Sell</button>
            </div>
          </td>
        </tr>
      `;
    })
    .join("");
}

async function loadLatest() {
  try {
    const latest = await getJson("/results/latest");
    latestCandidates = latest.candidates || [];
    setSectorOptions(latestCandidates);
    renderSectorView(latestCandidates);
    renderStrategyTabs();
    scanDate.textContent = `Scan date ${latest.scan_date} - ${latest.candidates?.length || 0} stocks shown`;
    renderCandidates(latestCandidates);
  } catch (error) {
    latestCandidates = [];
    setSectorOptions(latestCandidates);
    renderSectorView(latestCandidates);
    scanDate.textContent = "No scan yet";
    candidateRows.innerHTML =
      '<tr><td colspan="17" class="empty">Run a scan after loading candle data.</td></tr>';
    renderStrategyTabs();
  }

  try {
    const response = await fetch("/reports/latest");
    reportBox.textContent = response.ok ? await response.text() : "No report generated yet.";
  } catch (error) {
    reportBox.textContent = "No report generated yet.";
  }
}

async function refresh() {
  setStatus("Refreshing");
  const failures = [];
  for (const [label, loader] of [
    ["status", loadStatus],
    ["strategies", loadStrategies],
    ["symbols", loadSymbols],
    ["latest scan", loadLatest],
    ["portfolio", loadPortfolio],
  ]) {
    try {
      await loader();
    } catch (error) {
      failures.push(`${label}: ${error.message}`);
    }
  }
  if (failures.length) {
    setStatus("Partial data");
    reportBox.textContent = `Some sections could not load:\n${failures.join("\n")}`;
    return;
  }
  setStatus("Ready");
}

async function runScan(useOpenAI = false) {
  const button = useOpenAI ? aiScanBtn : scanBtn;
  button.disabled = true;
  button.textContent = "Updating";
  try {
    const productionPartial =
      currentStatus?.app_env === "production" && Number(currentStatus?.candle_stats?.symbols || 0) < 90;
    if (productionPartial) {
      reportBox.textContent =
        "Hosted candle history is partial. Starting background repair first; scan will use currently stored candles until repair completes.";
      await startBootstrap();
    }
    reportBox.textContent = useOpenAI
      ? "Fetching latest candles, scanning, then generating AI scenario notes..."
      : "Fetching latest Yahoo candles, then scanning...";
    const fetchLatest = currentStatus?.app_env === "production" ? false : true;
    const result = await getJson("/scan", {
      method: "POST",
      body: JSON.stringify({ universe: "nifty100", use_openai: useOpenAI, fetch_latest: fetchLatest, min_score: 0 }),
      timeoutMs: 180000,
    });
    latestCandidates = result.candidates || [];
    setSectorOptions(latestCandidates);
    renderSectorView(latestCandidates);
    renderStrategyTabs();
    scanDate.textContent = `Scan date ${result.scan_date} - ${result.candidates?.length || 0} stocks shown`;
    renderCandidates(latestCandidates);
    reportBox.textContent = result.markdown_report || "Scan completed.";
    await loadStatus();
  } catch (error) {
    reportBox.textContent = `Scan failed: ${error.message}`;
  } finally {
    button.disabled = false;
    button.textContent = useOpenAI ? "AI Scan" : "Run Scan";
  }
}

async function loadBootstrapStatus() {
  const status = await getJson("/bootstrap/status", { timeoutMs: 30000 });
  const progress = `${status.stored_symbols || 0}/${status.total_symbols || 100} symbols`;
  liveState.textContent = `${status.message || "Repair status"} - ${progress}`;
  if (repairBtn) {
    repairBtn.disabled = Boolean(status.running);
    repairBtn.textContent = status.running ? "Repairing" : "Repair Data";
  }
  if (!status.running && bootstrapTimer) {
    clearInterval(bootstrapTimer);
    bootstrapTimer = null;
    await loadStatus();
    await loadLatest();
  }
  return status;
}

async function startBootstrap() {
  if (repairBtn) {
    repairBtn.disabled = true;
    repairBtn.textContent = "Repairing";
  }
  const status = await getJson("/bootstrap/start", { method: "POST", body: JSON.stringify({}), timeoutMs: 30000 });
  liveState.textContent = status.message || "History repair queued";
  if (bootstrapTimer) {
    clearInterval(bootstrapTimer);
  }
  bootstrapTimer = setInterval(() => {
    loadBootstrapStatus().catch((error) => {
      liveState.textContent = `Repair status failed - ${error.message}`;
    });
  }, 10000);
  return status;
}

function renderLiveQuotes(quotes) {
  if (!quotes.length) {
    liveRows.innerHTML = '<tr><td colspan="4" class="empty">No prices returned.</td></tr>';
    return;
  }

  liveRows.innerHTML = quotes
    .map(
      (quote) => `
        <tr>
          <td class="symbol-cell"><strong>${quote.symbol}</strong></td>
          <td>${quote.exchange_symbol}</td>
          <td>${quote.last_price ?? "-"}</td>
          <td title="${quote.source || "yahoo"}">${quote.last_time ?? "-"}</td>
        </tr>
      `
    )
    .join("");
}

async function loadLivePrices() {
  liveBtn.disabled = true;
  liveBtn.textContent = "Loading";
  const startedAt = new Date();
  liveState.textContent = "Requesting Nifty 100 delayed quotes";
  try {
    const result = await getJson("/quotes/live", {
      method: "POST",
      body: JSON.stringify({}),
      timeoutMs: 120000,
    });
    renderLiveQuotes(result.quotes || []);
    const priced = (result.quotes || []).filter((quote) => quote.last_price !== null && quote.last_price !== undefined).length;
    const marketText = result.market_open ? "NSE open" : "NSE closed / delayed";
    liveState.textContent = `${result.note || "Prices loaded"} - ${priced} shown - ${marketText} - ${startedAt.toLocaleTimeString()}`;
    renderStrategyTabs();
  } catch (error) {
    const message = error.name === "AbortError" ? "Quote request timed out. Try again in a moment." : error.message;
    liveRows.innerHTML = `<tr><td colspan="4" class="empty">${message}</td></tr>`;
    liveState.textContent = `Live request failed - ${startedAt.toLocaleTimeString()}`;
  } finally {
    liveBtn.disabled = false;
    liveBtn.textContent = "Free Prices";
  }
}

function emaSeries(values, period) {
  const multiplier = 2 / (period + 1);
  let previous = null;
  return values.map((value, index) => {
    if (!Number.isFinite(value)) {
      return null;
    }
    if (previous === null) {
      if (index + 1 < period) {
        return null;
      }
      const seed = values.slice(index + 1 - period, index + 1);
      previous = seed.reduce((sum, item) => sum + item, 0) / period;
      return previous;
    }
    previous = value * multiplier + previous * (1 - multiplier);
    return previous;
  });
}

function renderChartStrategyBadges(candidate) {
  const items = strategyItems(candidate?.strategy_matches || []);
  if (!items.length) {
    chartStrategyBadges.innerHTML = '<span class="empty">No strategy bucket matched this stock yet.</span>';
    return;
  }
  chartStrategyBadges.innerHTML = items
    .slice(0, 12)
    .map((item) => `<span class="strategy-badge" title="${item.basis || ""}">${item.label}</span>`)
    .join("");
}

function dateLabel(value, interval) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value).slice(0, 16);
  }
  if (interval === "1d") {
    return date.toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
  }
  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

function resetChartViewport(candles, candidate) {
  const visible = Math.min(candles.length, chartInterval.value === "1d" ? 90 : 80);
  activeChart = {
    candles,
    candidate,
    start: Math.max(0, candles.length - visible),
    end: candles.length,
    dragging: false,
    dragX: 0,
  };
}

function clampChartViewport() {
  const total = activeChart.candles.length;
  const minVisible = Math.min(12, total);
  let start = Math.max(0, Math.min(activeChart.start, Math.max(0, total - minVisible)));
  let end = Math.max(start + minVisible, Math.min(activeChart.end, total));
  if (end > total) {
    const width = end - start;
    end = total;
    start = Math.max(0, end - width);
  }
  activeChart.start = start;
  activeChart.end = end;
}

function redrawActiveChart() {
  drawCandleChart(activeChart.candles, activeChart.candidate);
}

function drawCandleChart(candles, candidate) {
  const context = stockChart.getContext("2d");
  const rect = stockChart.getBoundingClientRect();
  const scale = window.devicePixelRatio || 1;
  stockChart.width = Math.max(320, Math.floor(rect.width * scale));
  stockChart.height = Math.floor(420 * scale);
  context.scale(scale, scale);

  const width = stockChart.width / scale;
  const height = stockChart.height / scale;
  context.clearRect(0, 0, width, height);

  if (!candles.length) {
    context.fillStyle = "#657386";
    context.fillText("No candles available", 24, 40);
    return;
  }

  const padding = { top: 18, right: 58, bottom: 34, left: 54 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  clampChartViewport();
  const visibleCandles = candles.slice(activeChart.start, activeChart.end);
  const highs = visibleCandles.map((item) => item.high);
  const lows = visibleCandles.map((item) => item.low);
  const closes = visibleCandles.map((item) => item.close);
  const plan = candidate?.trade_plan || {};
  const features = candidate?.features || {};
  const rawLevels = [
    candidate?.breakout_level,
    plan.entry_price,
    plan.stop_loss,
    plan.target_1,
    features.support_20d,
    features.support_50d,
    features.resistance_20d,
    features.resistance_50d,
  ]
    .map(Number)
    .filter((value) => Number.isFinite(value) && value > 0);
  const isIntraday = chartInterval.value !== "1d";
  const sortedLows = [...lows].sort((a, b) => a - b);
  const sortedHighs = [...highs].sort((a, b) => a - b);
  const lowIndex = Math.floor(sortedLows.length * 0.03);
  const highIndex = Math.max(0, Math.ceil(sortedHighs.length * 0.97) - 1);
  const candleMin = isIntraday ? sortedLows[lowIndex] : Math.min(...lows);
  const candleMax = isIntraday ? sortedHighs[highIndex] : Math.max(...highs);
  const candleRange = Math.max(candleMax - candleMin, 1);
  const nearbyLevels = rawLevels.filter((value) => {
    if (!isIntraday) {
      return true;
    }
    return value >= candleMin - candleRange * 1.2 && value <= candleMax + candleRange * 1.2;
  });
  const scaleLevels = isIntraday ? nearbyLevels : rawLevels;
  let minPrice = Math.min(...lows, ...scaleLevels);
  let maxPrice = Math.max(...highs, ...scaleLevels);
  const pad = Math.max((maxPrice - minPrice) * 0.08, candleRange * 0.12, 0.5);
  minPrice -= pad;
  maxPrice += pad;
  const range = Math.max(maxPrice - minPrice, 1);
  const yFor = (price) => padding.top + ((maxPrice - price) / range) * plotHeight;
  const xStep = plotWidth / visibleCandles.length;
  const bodyWidth = Math.max(2, Math.min(9, xStep * 0.62));
  const xFor = (index) => padding.left + index * xStep + xStep / 2;

  context.strokeStyle = "#dfe5ee";
  context.lineWidth = 1;
  for (let i = 0; i < 5; i += 1) {
    const y = padding.top + (plotHeight / 4) * i;
    context.beginPath();
    context.moveTo(padding.left, y);
    context.lineTo(width - padding.right, y);
    context.stroke();
    const price = maxPrice - (range / 4) * i;
    context.fillStyle = "#657386";
    context.font = "12px Segoe UI, sans-serif";
    context.fillText(price.toFixed(2), width - padding.right + 8, y + 4);
  }

  const shadeZone = (label, lowValue, highValue, color) => {
    const low = Number(lowValue);
    const high = Number(highValue);
    if (!Number.isFinite(low) || !Number.isFinite(high) || low <= 0 || high <= 0) {
      return;
    }
    if (isIntraday && (high < minPrice || low > maxPrice)) {
      return;
    }
    const topY = yFor(Math.max(low, high));
    const bottomY = yFor(Math.min(low, high));
    context.fillStyle = color;
    context.fillRect(padding.left, topY, plotWidth, Math.max(2, bottomY - topY));
    context.fillStyle = "#526172";
    context.fillText(label, padding.left + 8, topY + 14);
  };

  shadeZone("Resistance zone", features.resistance_20d, features.resistance_50d, "rgba(161, 92, 5, 0.08)");
  shadeZone("Support zone", features.support_20d, features.support_50d, "rgba(20, 116, 111, 0.08)");

  visibleCandles.forEach((item, index) => {
    const x = xFor(index);
    const openY = yFor(item.open);
    const closeY = yFor(item.close);
    const highY = yFor(item.high);
    const lowY = yFor(item.low);
    const up = item.close >= item.open;
    const color = up ? "#0b6b4a" : "#a33030";
    context.strokeStyle = color;
    context.fillStyle = color;
    context.beginPath();
    context.moveTo(x, highY);
    context.lineTo(x, lowY);
    context.stroke();
    const top = Math.min(openY, closeY);
    const bodyHeight = Math.max(Math.abs(closeY - openY), 1);
    if (up) {
      context.strokeRect(x - bodyWidth / 2, top, bodyWidth, bodyHeight);
    } else {
      context.fillRect(x - bodyWidth / 2, top, bodyWidth, bodyHeight);
    }
  });

  const drawSeries = (label, series, color) => {
    context.strokeStyle = color;
    context.lineWidth = 1.6;
    context.beginPath();
    let started = false;
    series.forEach((value, index) => {
      if (!Number.isFinite(value)) {
        return;
      }
      const x = xFor(index);
      const y = yFor(value);
      if (!started) {
        context.moveTo(x, y);
        started = true;
      } else {
        context.lineTo(x, y);
      }
    });
    if (started) {
      context.stroke();
      const last = [...series].reverse().find((value) => Number.isFinite(value));
      if (Number.isFinite(last)) {
        context.fillStyle = color;
        context.fillText(label, width - padding.right - 62, yFor(last) - 5);
      }
    }
  };

  drawSeries("EMA20", emaSeries(closes, 20), "#2563eb");
  drawSeries("EMA50", emaSeries(closes, 50), "#7c3aed");

  const drawnLevels = [];
  const drawLevel = (label, value, color, dash = [6, 5]) => {
    if (!Number.isFinite(value) || value <= 0) {
      return;
    }
    if (isIntraday && (value < minPrice || value > maxPrice)) {
      return;
    }
    const rawY = yFor(value);
    const nearby = drawnLevels.find((item) => Math.abs(item.value - value) / Math.max(value, 1) < 0.0015);
    if (nearby) {
      nearby.labels.push(label);
      return;
    }
    let labelY = rawY;
    while (drawnLevels.some((item) => Math.abs(item.labelY - labelY) < 18)) {
      labelY += 18;
    }
    drawnLevels.push({ value, labelY, labels: [label], color });
    context.strokeStyle = color;
    context.fillStyle = color;
    context.lineWidth = 1.6;
    context.setLineDash(dash);
    context.beginPath();
    context.moveTo(padding.left, rawY);
    context.lineTo(width - padding.right - 70, rawY);
    context.stroke();
    context.setLineDash([]);
    context.fillStyle = "#ffffff";
    context.fillRect(width - padding.right - 64, labelY - 11, 74, 18);
    context.strokeStyle = color;
    context.strokeRect(width - padding.right - 64, labelY - 11, 74, 18);
    context.fillStyle = color;
    context.font = "11px Segoe UI, sans-serif";
    context.fillText(value.toFixed(2), width - padding.right - 58, labelY + 2);
    context.fillText(label, padding.left + 8, rawY - 6);
  };

  drawLevel("Target", Number(plan.target_1), "#0b6b4a", [7, 5]);
  drawLevel("Entry", Number(plan.entry_price), "#14746f", [7, 5]);
  drawLevel("Breakout", Number(candidate?.breakout_level), "#a15c05", [7, 5]);
  drawLevel("Resistance", Number(features.resistance_50d), "#a15c05", [3, 5]);
  drawLevel("Support", Number(features.support_20d), "#14746f", [7, 5]);
  drawLevel("Stop", Number(plan.stop_loss), "#a33030", [7, 5]);

  const latest = candles[candles.length - 1];
  const latestX = xFor(visibleCandles.length - 1);
  const latestPattern = features.candle_pattern;
  if (!isIntraday && latestPattern && latestPattern !== "none" && activeChart.end === candles.length) {
    const markerY = yFor(latest.high) - 14;
    context.fillStyle = "#101820";
    context.beginPath();
    context.arc(latestX, markerY, 5, 0, Math.PI * 2);
    context.fill();
    context.fillText(latestPattern.replaceAll("_", " "), Math.max(padding.left, latestX - 92), markerY - 10);
  }

  const matches = strategyItems(candidate?.strategy_matches || []).slice(0, 4);
  if (matches.length) {
    context.fillStyle = "rgba(16, 24, 32, 0.88)";
    context.fillRect(padding.left, padding.top, Math.min(460, plotWidth), 28);
    context.fillStyle = "#ffffff";
    context.font = "12px Segoe UI, sans-serif";
    context.fillText(`Strategy: ${matches.map((item) => item.label).join(" + ")}`, padding.left + 10, padding.top + 18);
  }

  const labelCount = Math.min(6, Math.max(2, Math.floor(plotWidth / 150)));
  context.fillStyle = "#657386";
  context.font = "11px Segoe UI, sans-serif";
  for (let i = 0; i < labelCount; i += 1) {
    const index = Math.round((visibleCandles.length - 1) * (i / (labelCount - 1)));
    const x = xFor(index);
    const label = dateLabel(visibleCandles[index].date, chartInterval.value);
    const labelX = Math.min(Math.max(padding.left, x - 44), width - padding.right - 88);
    context.fillText(label, labelX, height - 12);
  }
  const windowText = `${activeChart.start + 1}-${activeChart.end} of ${candles.length} candles`;
  context.fillText(windowText, padding.left, padding.top + plotHeight + 18);
}

function renderScreener(symbol, candidate) {
  const plan = candidate?.trade_plan || {};
  const strategy = candidate?.strategy_profile || {};
  const features = candidate?.features || {};
  const rows = [
    ["Symbol", symbol],
    ["Sector", candidate?.sector || "Other"],
    ["Verdict", candidate?.verdict?.replaceAll("_", " ") || "-"],
    ["Score", candidate?.score ?? "-"],
    ["Strategy", strategy.strategy_label || "-"],
    ["Strategy Tabs", strategyLabels(candidate?.strategy_matches || []) || "-"],
    ["Breakout", formatPrice(candidate?.breakout_level)],
    ["Support 20d", formatPrice(features.support_20d)],
    ["Resistance 50d", formatPrice(features.resistance_50d)],
    ["Entry", formatPrice(plan.entry_price)],
    ["Stop", formatPrice(plan.stop_loss)],
    ["Target", formatPrice(plan.target_1)],
    ["Volume", features.volume_vs_20d ? `${features.volume_vs_20d}x avg` : "-"],
  ];
  chartScreener.innerHTML = rows.map(([label, value]) => `<div><dt>${label}</dt><dd>${value}</dd></div>`).join("");
}

function renderStrategyVisuals(candidate) {
  const features = candidate?.features || {};
  const plan = candidate?.trade_plan || {};
  const rows = [
    ["Trend", features.above_20ema && features.above_50ema ? "Above 20/50 EMA" : "Trend not fully aligned"],
    ["Breakout", features.valid_breakout ? "Triggered above resistance" : features.near_breakout ? "Near breakout level" : "No clean trigger"],
    ["Volume", features.volume_vs_20d ? `${features.volume_vs_20d}x 20-day average` : "-"],
    ["Support", `${formatPrice(features.support_20d)} / ${formatPrice(features.support_50d)}`],
    ["Resistance", `${formatPrice(features.resistance_20d)} / ${formatPrice(features.resistance_50d)}`],
    ["Pattern", features.candle_pattern || "-"],
    ["Risk/Reward", plan.risk_reward_to_t1 ? `${plan.risk_reward_to_t1}:1 to T1` : "-"],
  ];
  const matched = strategyItems(candidate?.strategy_matches || []);
  strategyVisualBox.innerHTML = `
    <div class="strategy-visual-grid">
      ${rows.map(([label, value]) => `<div><dt>${label}</dt><dd>${value}</dd></div>`).join("")}
    </div>
    <div class="strategy-rule-list">
      ${matched
        .slice(0, 8)
        .map((item) => `<p><strong>${item.label}</strong><span>${item.basis || "Matched by scanner rules."}</span></p>`)
        .join("") || '<p><strong>No strategy match</strong><span>Run a fresh scan to classify this stock.</span></p>'}
    </div>
  `;
}

function checkItem(label, formula, passed, badge = "Must") {
  return `
    <div class="momentum-check ${passed ? "pass" : "fail"}">
      <span class="check-box">${passed ? "✓" : ""}</span>
      <div><strong>${label}</strong><code>${formula}</code></div>
      <em>${badge}</em>
    </div>
  `;
}

function renderMomentumStrategy(candidate) {
  const f = candidate?.features || {};
  const p = candidate?.trade_plan || {};
  const entryChecks = [
    ["Price above 20 EMA and 50 EMA", "close > ema20 AND close > ema50", f.above_20ema && f.above_50ema, "Must"],
    ["20 EMA slope positive", "ema20[0] > ema20[-1]", f.ema_20_slope_positive, "Must"],
    ["50 EMA above 200 EMA", "ema50 > ema200", f.ema_50_gt_200, "Strong"],
    ["RSI(14) between 55 and 72", "rsi14 >= 55 AND rsi14 <= 72", f.rsi_14 >= 55 && f.rsi_14 <= 72, "Must"],
    ["MACD line above signal line", "macd_line > macd_signal", f.macd_line > f.macd_signal, "Must"],
    ["MACD histogram positive and expanding", "hist[0] > 0 AND hist[0] > hist[-1]", f.macd_hist > 0 && f.macd_hist > f.macd_hist_prev, "Strong"],
    ["ADX(14) above 25 and +DI > -DI", "adx14 > 25 AND plus_di > minus_di", f.adx_14 > 25 && f.plus_di_14 > f.minus_di_14, "Must"],
    ["Stochastic %K above %D from below 40", "stoch_k > stoch_d AND prev_k < 40", f.stoch_k > f.stoch_d && f.stoch_k_prev < 40, "Confirm"],
  ];
  const exitChecks = [
    ["Price closes below 20 EMA", "close < ema20 on close", Number(f.close) < Number(f.ema_20), "Exit now"],
    ["RSI drops below 50", "rsi14 < 50", f.rsi_14 < 50, "Exit now"],
    ["MACD bearish crossover", "macd_line < macd_signal", f.macd_line < f.macd_signal, "Exit now"],
    ["Trail stop: 2x ATR below highest close", "trail = high_close - 2*atr14", false, "Trail"],
    ["RSI reaches overbought 78+", "rsi14 >= 78 -> book 50%", f.rsi_14 >= 78, "Partial"],
    ["Bearish divergence warning", "price HH and RSI LH", false, "Warning"],
    ["ADX falling below 20", "adx14 < 20 AND adx_slope < 0", f.adx_14 < 20 && f.adx_14_slope < 0, "Caution"],
  ];
  const entryScore = entryChecks.filter((item) => item[2]).length;
  const exitScore = exitChecks.filter((item) => item[2]).length;
  const entry = Number(p.entry_price || f.close || 0);
  const atr = Number(f.atr || 0);
  const risk = Number(p.risk_per_share || 0);
  const slPct = entry ? (risk / entry) * 100 : 0;
  momentumStrategyBox.innerHTML = `
    <div class="momentum-header">
      <strong>Ride strong uptrends</strong>
      <span>Timeframe: 5-20 days</span>
      <span>Risk: ${p.risk_grade || "medium"}</span>
    </div>
    <div class="momentum-calculator">
      <div><span>Entry price</span><strong class="positive">₹${formatPrice(entry)}</strong></div>
      <div><span>ATR(14)</span><strong>₹${formatPrice(atr)}</strong></div>
      <div><span>Stop loss</span><strong class="negative">₹${formatPrice(p.stop_loss)}</strong></div>
      <div><span>Risk</span><strong>₹${formatPrice(risk)}</strong></div>
      <div><span>Target 1 (50%)</span><strong>₹${formatPrice(p.target_1)}</strong></div>
      <div><span>Target 2 / trail</span><strong>₹${formatPrice(p.target_2)}</strong></div>
      <div><span>SL % from entry</span><strong class="${slPct > 5 ? "negative" : "positive"}">${slPct.toFixed(2)}%</strong></div>
      <div><span>R:R target</span><strong>1:${formatPrice(p.target_rr || 2)}</strong></div>
    </div>
    <div class="stop-methods">
      <p><strong>Method A: ATR stop</strong><code>stop = entry - 1.5 × ATR = ₹${formatPrice(p.atr_stop)}</code></p>
      <p><strong>Method B: Below 20 EMA</strong><code>stop = ema20 - 0.3% = ₹${formatPrice(p.ema_stop)}</code></p>
      <p><strong>Method C: Below swing low</strong><code>stop = recent_swing_low - 0.2% = ₹${formatPrice(p.swing_stop)}</code></p>
      <p><strong>Trail</strong><code>${p.trail_stop_rule || "Trail at 2x ATR below highest close."}</code></p>
    </div>
    <div class="momentum-columns">
      <section><h4>Entry checklist <span>${entryScore}/8</span></h4>${entryChecks.map((item) => checkItem(...item)).join("")}</section>
      <section><h4>Exit checklist <span>${exitScore}/7</span></h4>${exitChecks.map((item) => checkItem(...item)).join("")}</section>
    </div>
  `;
}

function breakoutMethod(title, desc, formula, tag) {
  return `
    <p>
      <strong>${title}</strong>
      <span>${desc}</span>
      <code>${formula}</code>
      <em>${tag}</em>
    </p>
  `;
}

function renderBreakoutStrategy(candidate) {
  const f = candidate?.features || {};
  const p = candidate?.trade_plan || {};
  const breakoutLevel = Number(candidate?.breakout_level || f.resistance_20d || 0);
  const baseLow = Number(f.base_low || f.support_20d || 0);
  const baseHeight = Math.max(0, breakoutLevel - baseLow);
  const active = (candidate?.strategy_matches || []).includes("breakout_strategy");
  const failed = Number(f.close || 0) < breakoutLevel && f.valid_breakout;
  breakoutStrategyBox.innerHTML = `
    <div class="breakout-meta">
      <div><span>Candle timeframe</span><strong>Daily (EOD)</strong><small>Use 1D OHLCV data</small></div>
      <div><span>Signal scan time</span><strong>After 3:30 PM</strong><small>Post-market close scan</small></div>
      <div><span>Holding period</span><strong>3 - 15 days</strong><small>Swing trade</small></div>
      <div><span>Lookback needed</span><strong>252 candles</strong><small>52-week high check</small></div>
    </div>
    <div class="breakout-status ${active ? "active" : "watch"}">
      ${active ? "Breakout strategy conditions matched" : "Breakout strategy watch mode"}
    </div>
    <div class="breakout-columns">
      <section>
        <h4>Entry price - how to get it</h4>
        ${breakoutMethod(
          "Buy-stop 0.25% above breakout level",
          "Resistance level = rolling 20-day high. Place buy-stop just above it to catch confirmed breakout.",
          `entry = rolling_max(high, 20) * 1.0025 = ₹${formatPrice(p.breakout_buy_stop_entry)}`,
          "Recommended"
        )}
        ${breakoutMethod(
          "Next-day open after breakout close",
          "If breakout candle closes above resistance at EOD, enter at next-day open with confirmation.",
          p.breakout_next_open_entry_rule || "entry = next_open if prev_close > resistance",
          "EOD scan"
        )}
        ${breakoutMethod(
          "Retest of breakout level",
          "More conservative: wait for price to pull back and retest old resistance as new support.",
          `entry = resistance_level + 0.2% = ₹${formatPrice(p.breakout_retest_entry)}`,
          "Low risk"
        )}
      </section>
      <section>
        <h4>Exit price - how to get it</h4>
        ${breakoutMethod(
          "Target 1: measured move projection",
          "Height of the base pattern projected upward from breakout point.",
          `t1 = breakout + base_height (${formatPrice(baseHeight)}) = ₹${formatPrice(p.breakout_target_1)}`,
          "Primary T1"
        )}
        ${breakoutMethod(
          "Target 2: 2x base height projection",
          "Extended target for strong breakouts. Book remaining 50% here.",
          `t2 = breakout + 2 × base_height = ₹${formatPrice(p.breakout_target_2)}`,
          "Primary T2"
        )}
        ${breakoutMethod(
          "Exit if price falls below breakout level",
          "Failed breakout. Exit immediately; no second chances on false breakouts.",
          `if close < breakout_level (${formatPrice(breakoutLevel)}): exit_all()`,
          failed ? "Triggered" : "Forced exit"
        )}
      </section>
    </div>
    <div class="breakout-stops">
      <h4>Stop loss - 3 methods</h4>
      ${breakoutMethod(
        "Method A: below base low",
        "Most logical. If price returns to base, breakout has failed.",
        `stop_loss = base_low - 0.3% = ₹${formatPrice(p.breakout_base_stop)}`,
        "Primary"
      )}
      ${breakoutMethod(
        "Method B: 1.5x ATR below breakout level",
        "For larger bases where base_low is too far. ATR keeps stop proportional.",
        `stop_loss = breakout_level - 1.5 × ATR(14) = ₹${formatPrice(p.breakout_atr_stop)}`,
        "Secondary"
      )}
      ${breakoutMethod(
        "Method C: below breakout candle low",
        "Tight stop. If the breakout candle low is violated, momentum is suspect.",
        `stop_loss = breakout_candle_low - 0.2% = ₹${formatPrice(p.breakout_candle_stop)}`,
        "Tight"
      )}
      ${breakoutMethod(
        "Trail: move to breakout level after +5%",
        "Once up 5%, raise stop to original breakout level. Trail 20 EMA after T1.",
        p.breakout_trail_rule || "if pnl_pct >= 5: stop = breakout_level",
        "Trail"
      )}
    </div>
  `;
}

function renderNewsLoading() {
  newsBox.innerHTML = '<span class="empty">Loading latest headlines...</span>';
}

function renderNews(data) {
  const items = data.items || [];
  const riskLabel = (data.news_risk || "neutral").replaceAll("_", " ");
  if (!items.length) {
    newsBox.innerHTML = `
      <div class="news-risk neutral">No recent Yahoo Finance headlines found.</div>
      <p class="news-note">Technical setup is not being adjusted by news yet.</p>
    `;
    return;
  }

  newsBox.innerHTML = `
    <div class="news-risk ${data.news_risk || "neutral"}">
      ${riskLabel} - ${data.catalyst_count || 0} catalyst / ${data.risk_count || 0} risk headlines
    </div>
    <div class="news-list">
      ${items
        .slice(0, 5)
        .map(
          (item) => `
            <a class="news-item ${item.sentiment}" href="${item.url || "#"}" target="_blank" rel="noreferrer">
              <strong>${item.title}</strong>
              <span>${item.provider || "Yahoo Finance"}${item.age_hours !== null && item.age_hours !== undefined ? ` - ${item.age_hours}h ago` : ""}</span>
            </a>
          `
        )
        .join("")}
    </div>
  `;
}

async function loadNews(symbol) {
  renderNewsLoading();
  try {
    const data = await getJson(`/stocks/${encodeURIComponent(symbol)}/news?limit=8`, { timeoutMs: 30000 });
    renderNews(data);
  } catch (error) {
    newsBox.innerHTML = `<span class="empty">${error.message}</span>`;
  }
}

function renderFundamentals(data) {
  const q = data.quarterly || {};
  const rows = [
    ["Company", data.company_name || data.symbol],
    ["P/E", data.trailing_pe ?? "-"],
    ["Forward P/E", data.forward_pe ?? "-"],
    ["EPS TTM", data.eps_ttm ?? "-"],
    ["Market Cap", formatCompact(data.market_cap)],
    ["ROE", data.return_on_equity_pct !== null ? `${data.return_on_equity_pct}%` : "-"],
    ["Profit Margin", data.profit_margin_pct !== null ? `${data.profit_margin_pct}%` : "-"],
    ["Revenue Growth", data.revenue_growth_pct !== null ? `${data.revenue_growth_pct}%` : "-"],
    ["Earnings Growth", data.earnings_growth_pct !== null ? `${data.earnings_growth_pct}%` : "-"],
    ["Debt/Equity", data.debt_to_equity ?? "-"],
    ["Latest Revenue", formatCompact(q.latest_revenue)],
    ["Latest Profit", formatCompact(q.latest_net_income)],
    ["Profit QoQ", q.net_income_qoq_pct !== null ? `${q.net_income_qoq_pct}%` : "-"],
    ["Profit YoY", q.net_income_yoy_pct !== null ? `${q.net_income_yoy_pct}%` : "-"],
    ["Quality Score", data.quality_score ?? "-"],
    ["Valuation", data.valuation_note || "-"],
  ];
  fundamentalsBox.innerHTML = rows.map(([label, value]) => `<div><dt>${label}</dt><dd>${value}</dd></div>`).join("");
  renderLongTermResearch(data.long_term_research || {});
  renderFundamentalDashboard(data);
}

function renderFundamentalsLoading() {
  fundamentalsBox.innerHTML = '<div><dt>Fundamentals</dt><dd>Loading...</dd></div>';
  longTermResearchBox.innerHTML = '<span class="empty">Loading long-term scorecard...</span>';
  fundamentalDashboardState.textContent = "Loading derived fundamental parameters";
  fundamentalDashboard.innerHTML = '<span class="empty">Loading full fundamental dashboard...</span>';
}

async function loadFundamentals(symbol) {
  renderFundamentalsLoading();
  try {
    const data = await getJson(`/stocks/${encodeURIComponent(symbol)}/fundamentals`);
    renderFundamentals(data);
  } catch (error) {
    fundamentalsBox.innerHTML = `<div><dt>Fundamentals</dt><dd>${error.message}</dd></div>`;
  }
}

function cardClass(signal = "") {
  const lower = String(signal).toLowerCase();
  if (lower.includes("excellent") || lower.includes("strong") || lower.includes("good") || lower.includes("positive") || lower.includes("safe") || lower.includes("compounder")) {
    return "good";
  }
  if (lower.includes("weak") || lower.includes("risk") || lower.includes("negative") || lower.includes("danger") || lower.includes("expensive")) {
    return "bad";
  }
  return "neutral";
}

function dashValue(card) {
  if (card.value === null || card.value === undefined) {
    return "-";
  }
  const number = Number(card.value);
  if (!Number.isFinite(number)) {
    return "-";
  }
  return `${number.toLocaleString("en-IN", { maximumFractionDigits: Math.abs(number) >= 100 ? 0 : 2 })}${card.suffix || ""}`;
}

function sparkline(values = [], labels = [], unit = "") {
  const clean = values.map(Number).filter((value) => Number.isFinite(value));
  if (clean.length < 2) {
    return '<span class="empty">Not enough history</span>';
  }
  const width = 280;
  const height = 128;
  const padding = { top: 14, right: 14, bottom: 24, left: 44 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const min = Math.min(...clean);
  const max = Math.max(...clean);
  const range = Math.max(max - min, 1);
  const yFor = (value) => padding.top + ((max - value) / range) * plotHeight;
  const xFor = (index) => padding.left + (index / (clean.length - 1)) * plotWidth;
  const formatAxis = (value) => {
    const abs = Math.abs(value);
    if (abs >= 1000) {
      return new Intl.NumberFormat("en-IN", { notation: "compact", maximumFractionDigits: 1 }).format(value);
    }
    return value.toFixed(abs >= 100 ? 0 : 1);
  };
  const firstLabel = labels[0] || "Start";
  const lastLabel = labels[labels.length - 1] || "Now";
  const points = clean
    .map((value, index) => {
      const x = xFor(index);
      const y = yFor(value);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Trend chart">
    <line x1="${padding.left}" y1="${padding.top}" x2="${padding.left}" y2="${padding.top + plotHeight}" stroke="#d8e1ea" stroke-width="1"></line>
    <line x1="${padding.left}" y1="${padding.top + plotHeight}" x2="${padding.left + plotWidth}" y2="${padding.top + plotHeight}" stroke="#d8e1ea" stroke-width="1"></line>
    <line x1="${padding.left}" y1="${yFor(max).toFixed(1)}" x2="${padding.left + plotWidth}" y2="${yFor(max).toFixed(1)}" stroke="#eef2f6" stroke-width="1"></line>
    <line x1="${padding.left}" y1="${yFor(min).toFixed(1)}" x2="${padding.left + plotWidth}" y2="${yFor(min).toFixed(1)}" stroke="#eef2f6" stroke-width="1"></line>
    <text x="4" y="${yFor(max) + 4}" fill="#64748b" font-size="10">${formatAxis(max)}</text>
    <text x="4" y="${yFor(min) + 4}" fill="#64748b" font-size="10">${formatAxis(min)}</text>
    <text x="${padding.left}" y="${height - 5}" fill="#64748b" font-size="10">${firstLabel}</text>
    <text x="${padding.left + plotWidth - 34}" y="${height - 5}" fill="#64748b" font-size="10">${lastLabel}</text>
    <text x="${width - 40}" y="11" fill="#94a3b8" font-size="10">${unit || ""}</text>
    <polyline points="${points}" fill="none" stroke="#14746f" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"></polyline>
    ${clean.map((value, index) => {
      const x = xFor(index);
      const y = yFor(value);
      return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3" fill="#101820"></circle>`;
    }).join("")}
  </svg>`;
}

function renderSummaryTable(title, rows) {
  return `
    <section class="fundamental-dash-table">
      <h4>${title}</h4>
      ${(rows || [])
        .map((row) => `<div><span>${row.label || row.metric}</span><strong>${row.value !== undefined ? `${row.value ?? "-"} ${row.unit || ""}` : row.status}</strong></div>`)
        .join("")}
    </section>
  `;
}

function renderFundamentalDashboard(data) {
  const research = data.long_term_research || {};
  const dashboard = research.dashboard || {};
  const cards = dashboard.cards || [];
  const trends = dashboard.trends || [];
  const tables = dashboard.summary_tables || {};
  if (!cards.length) {
    fundamentalDashboard.innerHTML = '<span class="empty">Fundamental dashboard data is unavailable for this stock.</span>';
    return;
  }
  fundamentalDashboardTitle.textContent = `${data.symbol} Fundamental Dashboard`;
  fundamentalDashboardState.textContent = `${research.verdict || "Long-term research"} - score ${research.score ?? "-"}/100`;
  fundamentalDashboard.innerHTML = `
    <div class="fundamental-dash-cards">
      ${cards
        .map(
          (card) => `
            <article class="fundamental-dash-card ${cardClass(card.signal)}">
              <span>${card.label}</span>
              <strong>${dashValue(card)}</strong>
              <small>${card.signal || ""}</small>
            </article>
          `
        )
        .join("")}
    </div>
    <div class="fundamental-trends">
      ${trends
        .map(
          (trend) => `
            <article>
              <h4>${trend.name}</h4>
              ${sparkline(trend.values || [], trend.labels || [], trend.unit || "")}
            </article>
          `
        )
        .join("")}
    </div>
    <div class="fundamental-bottom-grid">
      ${renderSummaryTable("Financial Summary", tables.financial_summary || [])}
      ${renderSummaryTable("Quality Checks", tables.quality_checks || [])}
      ${renderSummaryTable(
        "Master Matrix",
        (research.master_matrix || []).slice(0, 8).map((row) => ({ label: row.parameter, value: row.threshold, unit: "" }))
      )}
    </div>
  `;
}

function formatMetricValue(metric) {
  if (metric.value === null || metric.value === undefined) {
    return "-";
  }
  const suffix = metric.unit && metric.unit !== "x" ? metric.unit : "";
  const prefix = metric.unit === "x" ? "" : "";
  const value = Number(metric.value);
  if (!Number.isFinite(value)) {
    return "-";
  }
  return `${prefix}${value.toFixed(Math.abs(value) >= 100 ? 0 : 2)}${suffix}${metric.unit === "x" ? "x" : ""}`;
}

function signalClass(signal = "") {
  const lower = signal.toLowerCase();
  if (
    lower.includes("excellent") ||
    lower.includes("strong") ||
    lower.includes("good") ||
    lower.includes("safe") ||
    lower.includes("healthy") ||
    lower.includes("expansion") ||
    lower.includes("leverage") ||
    lower.includes("clean") ||
    lower.includes("efficient") ||
    lower.includes("undervalued")
  ) {
    return "good";
  }
  if (lower.includes("unavailable") || lower.includes("needs") || lower.includes("watch") || lower.includes("fair") || lower.includes("moderate") || lower.includes("manageable")) {
    return "neutral";
  }
  return "bad";
}

function renderLongTermResearch(research) {
  const sections = research.sections || [];
  if (!sections.length) {
    longTermResearchBox.innerHTML = '<span class="empty">Long-term research data is unavailable for this stock.</span>';
    return;
  }
  longTermResearchBox.innerHTML = `
    <div class="fundamental-score">
      <strong>${research.score ?? "-"} / 100</strong>
      <span>${research.verdict || "Research verdict unavailable"}</span>
    </div>
    <div class="fundamental-sections">
      ${sections
        .map(
          (section) => `
            <section>
              <h4>${section.title}</h4>
              ${(section.metrics || [])
                .map(
                  (metric) => `
                    <div class="fundamental-metric">
                      <div>
                        <strong>${metric.name}</strong>
                        <code>${metric.formula}</code>
                      </div>
                      <span>${formatMetricValue(metric)}</span>
                      <em class="${signalClass(metric.signal)}">${metric.signal}</em>
                    </div>
                  `
                )
                .join("")}
            </section>
          `
        )
        .join("")}
    </div>
    <section class="master-matrix">
      <h4>Final Master Matrix</h4>
      <div class="matrix-head"><span>Category</span><span>Parameter</span><span>Signal</span></div>
      ${(research.master_matrix || [])
        .slice(0, 18)
        .map((row) => `<div><span>${row.category}</span><span>${row.parameter}</span><span>${row.threshold}</span></div>`)
        .join("")}
    </section>
  `;
}

async function openStockChart(symbol) {
  selectedSymbol = symbol;
  chartTitle.textContent = `${symbol} Chart`;
  chartState.textContent = "Loading candles";
  try {
    const interval = chartInterval.value;
    const period = interval === "1d" ? "6mo" : "1d";
    const result = await getJson(`/stocks/${encodeURIComponent(symbol)}/chart?period=${period}&interval=${interval}`);
    resetChartViewport(result.candles || [], result.candidate || {});
    renderChartStrategyBadges(result.candidate || {});
    redrawActiveChart();
    renderScreener(symbol, result.candidate || {});
    renderStrategyVisuals(result.candidate || {});
    renderMomentumStrategy(result.candidate || {});
    renderBreakoutStrategy(result.candidate || {});
    loadNews(symbol);
    loadFundamentals(symbol);
    chartState.textContent = `${result.mode.replaceAll("_", " ")} - ${result.candles.length} candles`;
    document.querySelector(".chart-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    chartState.textContent = "Chart load failed";
    reportBox.textContent = `Chart failed for ${symbol}: ${error.message}`;
  }
}

function zoomChart(delta, anchorRatio = 0.5) {
  const total = activeChart.candles.length;
  if (!total) {
    return;
  }
  const currentWidth = activeChart.end - activeChart.start;
  const minWidth = Math.min(12, total);
  const maxWidth = total;
  const factor = delta < 0 ? 0.8 : 1.25;
  const nextWidth = Math.max(minWidth, Math.min(maxWidth, Math.round(currentWidth * factor)));
  const anchorIndex = activeChart.start + currentWidth * anchorRatio;
  activeChart.start = Math.round(anchorIndex - nextWidth * anchorRatio);
  activeChart.end = activeChart.start + nextWidth;
  clampChartViewport();
  redrawActiveChart();
  chartState.textContent = `Zoom ${activeChart.end - activeChart.start} candles - drag to pan, double click to reset`;
}

function panChart(pixelDelta) {
  const total = activeChart.candles.length;
  if (!total) {
    return;
  }
  const rect = stockChart.getBoundingClientRect();
  const visible = activeChart.end - activeChart.start;
  const candlesPerPixel = visible / Math.max(rect.width, 1);
  const shift = Math.round(-pixelDelta * candlesPerPixel);
  if (!shift) {
    return;
  }
  activeChart.start += shift;
  activeChart.end += shift;
  clampChartViewport();
  redrawActiveChart();
  chartState.textContent = `Viewing candles ${activeChart.start + 1}-${activeChart.end}; wheel zoom, drag pan`;
}

function setAutoLive(enabled) {
  if (autoLiveTimer) {
    clearInterval(autoLiveTimer);
    autoLiveTimer = null;
  }
  autoLiveBtn.classList.toggle("active", enabled);
  autoLiveBtn.textContent = enabled ? "Auto On" : "Auto Live";
  if (!enabled) {
    return;
  }
  loadLivePrices();
  autoLiveTimer = setInterval(() => {
    loadLivePrices();
    if (selectedSymbol && isNseTradingHours()) {
      openStockChart(selectedSymbol);
    }
  }, 60000);
}

function pnlClass(value) {
  if (value > 0) {
    return "positive";
  }
  if (value < 0) {
    return "negative";
  }
  return "";
}

function renderPortfolio(payload) {
  const summary = payload.summary || {};
  const positions = payload.open_positions || [];
  openPositions.textContent = formatNumber(summary.open_positions || 0);
  closedPositions.textContent = formatNumber(summary.closed_positions || 0);
  winRate.textContent = `${summary.win_rate || 0}%`;
  unrealizedPnl.textContent = formatPrice(summary.unrealized_pnl || 0);
  realizedPnl.textContent = formatPrice(summary.realized_pnl || 0);
  unrealizedPnl.className = pnlClass(summary.unrealized_pnl || 0);
  realizedPnl.className = pnlClass(summary.realized_pnl || 0);

  if (!positions.length) {
    portfolioRows.innerHTML = '<tr><td colspan="11" class="empty">No open paper positions yet.</td></tr>';
    portfolioState.textContent = "Paper trade book";
    return;
  }

  portfolioRows.innerHTML = positions
    .map(
      (trade) => `
        <tr>
          <td>${trade.trade_id}</td>
          <td><strong>${trade.symbol}</strong></td>
          <td>${trade.side}</td>
          <td>${trade.quantity}</td>
          <td>${formatPrice(trade.entry_price)}</td>
          <td>${formatPrice(trade.current_price)}</td>
          <td>${formatPrice(trade.stop_loss)}</td>
          <td>${formatPrice(trade.target_1)}</td>
          <td class="${pnlClass(trade.unrealized_pnl || 0)}">${formatPrice(trade.unrealized_pnl || 0)}</td>
          <td class="${pnlClass(trade.return_pct || 0)}">${trade.return_pct || 0}%</td>
          <td><button class="close-btn" data-trade-id="${trade.trade_id}" data-price="${trade.current_price || trade.entry_price}">Close</button></td>
        </tr>
      `
    )
    .join("");
  portfolioState.textContent = `Gross exposure ${formatNumber(summary.gross_exposure || 0)}`;
}

async function loadPortfolio() {
  const payload = await getJson("/portfolio");
  renderPortfolio(payload);
}

function buildSellPlan(plan) {
  const entry = Number(plan.entry_price || plan.breakout_trigger || 0);
  const riskPerShare = Number(plan.risk_per_share || 0);
  const stop = entry + riskPerShare;
  return {
    entry_price: entry,
    stop_loss: stop,
    target_1: entry - 1.5 * riskPerShare,
    target_2: entry - 2.25 * riskPerShare,
  };
}

async function createPaperTradeFromRow(row, side) {
  const quantityInput = row.querySelector(".qty-input");
  const quantity = Number(quantityInput?.value || 1);
  const symbol = row.dataset.symbol;
  const plan = JSON.parse(decodeURIComponent(row.dataset.plan || "%7B%7D"));
  const strategy = JSON.parse(decodeURIComponent(row.dataset.strategy || "%7B%7D"));
  const prediction = strategy.prediction || {};
  const payload =
    side === "SELL"
      ? {
          symbol,
          side,
          quantity,
          strategy: `${strategy.strategy_label || "Manual"} short test`,
          prediction_bias: prediction.bias || "watch",
          prediction_confidence: prediction.confidence || "low",
          thesis: prediction.summary || "",
          ...buildSellPlan(plan),
        }
      : {
          symbol,
          side,
          quantity,
          entry_price: Number(plan.entry_price || 0),
          stop_loss: Number(plan.stop_loss || 0),
          target_1: Number(plan.target_1 || 0),
          target_2: Number(plan.target_2 || 0),
          strategy: strategy.strategy_label || "Manual",
          prediction_bias: prediction.bias || "watch",
          prediction_confidence: prediction.confidence || "low",
          thesis: prediction.summary || "",
        };

  await getJson("/paper-trades", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  await loadStatus();
  await loadPortfolio();
}

candidateRows.addEventListener("click", async (event) => {
  const symbolCell = event.target.closest(".symbol-cell");
  if (symbolCell) {
    const row = event.target.closest("tr");
    if (row?.dataset.symbol) {
      openStockChart(row.dataset.symbol);
    }
    return;
  }

  const button = event.target.closest("button[data-action]");
  if (!button) {
    return;
  }
  const row = event.target.closest("tr");
  if (!row) {
    return;
  }
  button.disabled = true;
  const original = button.textContent;
  button.textContent = "Saving";
  try {
    await createPaperTradeFromRow(row, button.dataset.action);
    button.textContent = "Saved";
  } catch (error) {
    reportBox.textContent = `Trade save failed: ${error.message}`;
    button.textContent = "Retry";
  } finally {
    setTimeout(() => {
      button.disabled = false;
      button.textContent = original;
    }, 700);
  }
});

liveRows.addEventListener("click", (event) => {
  const row = event.target.closest("tr");
  const symbol = row?.querySelector(".symbol-cell strong")?.textContent;
  if (symbol) {
    openStockChart(symbol);
  }
});

symbolGrid.addEventListener("click", (event) => {
  const chip = event.target.closest(".symbol-chip");
  if (chip) {
    openStockChart(chip.textContent.trim());
  }
});

sectorGrid.addEventListener("click", (event) => {
  const tile = event.target.closest(".sector-tile");
  if (!tile) {
    return;
  }
  sectorFilter.value = tile.dataset.sector;
  renderCandidates(latestCandidates);
});

strategyTabs.addEventListener("click", (event) => {
  const tab = event.target.closest(".strategy-tab");
  if (!tab) {
    return;
  }
  selectedStrategyId = tab.dataset.strategy || "all";
  renderStrategyTabs();
});

strategyRows.addEventListener("click", (event) => {
  const row = event.target.closest("tr");
  if (row?.dataset.symbol) {
    openStockChart(row.dataset.symbol);
  }
});

portfolioRows.addEventListener("click", async (event) => {
  const button = event.target.closest(".close-btn");
  if (!button) {
    return;
  }
  button.disabled = true;
  button.textContent = "Closing";
  try {
    await getJson(`/paper-trades/${button.dataset.tradeId}/close`, {
      method: "POST",
      body: JSON.stringify({
        exit_price: Number(button.dataset.price || 0),
        exit_reason: "Closed from dashboard",
      }),
    });
    await loadStatus();
    await loadPortfolio();
    button.textContent = "Closed";
  } catch (error) {
    reportBox.textContent = `Close trade failed: ${error.message}`;
    button.disabled = false;
    button.textContent = "Close";
  }
});

symbolSearch.addEventListener("input", renderSymbols);
sectorFilter.addEventListener("change", () => renderCandidates(latestCandidates));
verdictFilter.addEventListener("change", () => renderCandidates(latestCandidates));
refreshBtn.addEventListener("click", refresh);
scanBtn.addEventListener("click", () => runScan(false));
aiScanBtn.addEventListener("click", () => runScan(true));
liveBtn.addEventListener("click", loadLivePrices);
autoLiveBtn.addEventListener("click", () => setAutoLive(!autoLiveTimer));
repairBtn?.addEventListener("click", () => {
  startBootstrap().catch((error) => {
    liveState.textContent = `Repair failed to start - ${error.message}`;
    if (repairBtn) {
      repairBtn.disabled = false;
      repairBtn.textContent = "Repair Data";
    }
  });
});
refreshChartBtn.addEventListener("click", () => {
  if (selectedSymbol) {
    openStockChart(selectedSymbol);
  }
});
chartInterval.addEventListener("change", () => {
  if (selectedSymbol) {
    openStockChart(selectedSymbol);
  }
});
stockChart.addEventListener("wheel", (event) => {
  if (!activeChart.candles.length) {
    return;
  }
  event.preventDefault();
  const rect = stockChart.getBoundingClientRect();
  const anchorRatio = Math.max(0, Math.min(1, (event.clientX - rect.left) / Math.max(rect.width, 1)));
  zoomChart(event.deltaY, anchorRatio);
});
stockChart.addEventListener("pointerdown", (event) => {
  if (!activeChart.candles.length) {
    return;
  }
  activeChart.dragging = true;
  activeChart.dragX = event.clientX;
  stockChart.setPointerCapture(event.pointerId);
});
stockChart.addEventListener("pointermove", (event) => {
  if (!activeChart.dragging) {
    return;
  }
  const delta = event.clientX - activeChart.dragX;
  activeChart.dragX = event.clientX;
  panChart(delta);
});
stockChart.addEventListener("pointerup", (event) => {
  activeChart.dragging = false;
  if (stockChart.hasPointerCapture(event.pointerId)) {
    stockChart.releasePointerCapture(event.pointerId);
  }
});
stockChart.addEventListener("pointerleave", () => {
  activeChart.dragging = false;
});
stockChart.addEventListener("dblclick", () => {
  if (!activeChart.candles.length) {
    return;
  }
  resetChartViewport(activeChart.candles, activeChart.candidate);
  redrawActiveChart();
  chartState.textContent = "Chart reset - wheel zoom, drag pan";
});
copyReportBtn.addEventListener("click", async () => {
  await navigator.clipboard.writeText(reportBox.textContent);
  copyReportBtn.textContent = "Copied";
  setTimeout(() => {
    copyReportBtn.textContent = "Copy";
  }, 1200);
});

refresh()
  .then(loadLivePrices)
  .catch((error) => {
  setStatus("Offline");
  reportBox.textContent = error.message;
});
