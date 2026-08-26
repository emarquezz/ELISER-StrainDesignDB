(() => {
  "use strict";

  const DATA_URL = "./data/eliser.json";
  const PAGE_SIZE = 20;
  const SEARCH_ALIASES = new Map([
    ["e. coli", "escherichia coli"],
    ["e coli", "escherichia coli"],
    ["s. cerevisiae", "saccharomyces cerevisiae"],
    ["s cerevisiae", "saccharomyces cerevisiae"],
    ["c. glutamicum", "corynebacterium glutamicum"],
    ["c glutamicum", "corynebacterium glutamicum"],
  ]);

  const state = {
    records: [],
    filtered: [],
    meta: null,
    page: 1,
    highlightTerms: [],
    debounce: null,
  };

  const elements = {
    searchForm: document.querySelector("#search-form"),
    search: document.querySelector("#search-input"),
    organism: document.querySelector("#organism-filter"),
    product: document.querySelector("#product-filter"),
    gene: document.querySelector("#gene-filter"),
    direction: document.querySelector("#direction-filter"),
    yearFrom: document.querySelector("#year-from-filter"),
    yearTo: document.querySelector("#year-to-filter"),
    sort: document.querySelector("#sort-select"),
    clear: document.querySelector("#clear-filters"),
    activeFilters: document.querySelector("#active-filters"),
    resultCount: document.querySelector("#result-count"),
    resultContext: document.querySelector("#result-context"),
    results: document.querySelector("#results"),
    loading: document.querySelector("#loading-state"),
    error: document.querySelector("#error-state"),
    pagination: document.querySelector("#pagination"),
    previous: document.querySelector("#previous-page"),
    next: document.querySelector("#next-page"),
    pageStatus: document.querySelector("#page-status"),
    export: document.querySelector("#export-button"),
    modificationCount: document.querySelector("#modification-count"),
    positiveCount: document.querySelector("#positive-count"),
    negativeCount: document.querySelector("#negative-count"),
    otherCount: document.querySelector("#other-count"),
    positiveBar: document.querySelector("#positive-bar"),
    negativeBar: document.querySelector("#negative-bar"),
    otherBar: document.querySelector("#other-bar"),
    topOrganisms: document.querySelector("#top-organisms"),
    topProducts: document.querySelector("#top-products"),
  };

  const numberFormatter = new Intl.NumberFormat("en-US");

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function escapeRegExp(value) {
    return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function normalize(value) {
    return String(value ?? "")
      .normalize("NFKD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .trim();
  }

  function normalizeWithAliases(value) {
    let normalized = normalize(value);
    SEARCH_ALIASES.forEach((expanded, alias) => {
      normalized = normalized.replaceAll(alias, expanded);
    });
    return normalized;
  }

  function stripPubMedMarkup(value) {
    return String(value ?? "").replace(/<\/?(?:b|i|sup|sub)>/gi, "");
  }

  function splitProducts(value) {
    const fullLabel = String(value ?? "").trim();
    if (!fullLabel) return [];
    return [...new Set([fullLabel, ...fullLabel.split(",").map((item) => item.trim())].filter(Boolean))];
  }

  function highlight(value) {
    const text = String(value ?? "");
    const expression = state.highlightTerms
      .filter((term) => term.length > 1)
      .sort((a, b) => b.length - a.length)
      .map(escapeRegExp)
      .join("|");
    if (!expression) return escapeHtml(text);
    return text
      .split(new RegExp(`(${expression})`, "gi"))
      .map((part, index) => index % 2 ? `<mark>${escapeHtml(part)}</mark>` : escapeHtml(part))
      .join("");
  }

  function formatNumber(value) {
    return numberFormatter.format(value || 0);
  }

  function safeYear(value) {
    const year = Number(value);
    return Number.isFinite(year) ? year : null;
  }

  function pubmedUrl(pmid) {
    return `https://pubmed.ncbi.nlm.nih.gov/${encodeURIComponent(pmid)}/`;
  }

  function buildSearchIndex(record) {
    const geneText = record.genes
      .map((gene) => `${gene.name} ${gene.directions.join(" ")}`)
      .join(" ");
    return normalize(
      `${record.pmid} ${stripPubMedMarkup(record.title)} ${record.organism} ${record.product} ${geneText}`,
    );
  }

  function populateSelectYears(meta) {
    const years = [];
    for (let year = meta.minYear; year <= meta.maxYear; year += 1) years.push(year);
    const anyFrom = '<option value="">Any year</option>';
    const anyTo = '<option value="">Any year</option>';
    const options = years.map((year) => `<option value="${year}">${year}</option>`).join("");
    elements.yearFrom.innerHTML = anyFrom + options;
    elements.yearTo.innerHTML = anyTo + options;
  }

  function populateDatalist(id, values) {
    const datalist = document.querySelector(id);
    datalist.innerHTML = values
      .slice(0, 300)
      .map((value) => `<option value="${escapeHtml(value)}"></option>`)
      .join("");
  }

  function setHeroStats(meta) {
    const mapping = {
      "#hero-record-count": meta.recordCount,
      "#hero-organism-count": meta.organismCount,
      "#hero-product-count": meta.productCount,
      "#hero-gene-count": meta.geneCount,
    };
    Object.entries(mapping).forEach(([selector, value]) => {
      document.querySelector(selector).textContent = formatNumber(value);
    });
  }

  function readUrlState() {
    const params = new URLSearchParams(window.location.search);
    const fields = [
      ["q", elements.search],
      ["organism", elements.organism],
      ["product", elements.product],
      ["gene", elements.gene],
      ["direction", elements.direction],
      ["from", elements.yearFrom],
      ["to", elements.yearTo],
      ["sort", elements.sort],
    ];
    fields.forEach(([key, element]) => {
      const value = params.get(key);
      if (value !== null) element.value = value;
    });
  }

  function writeUrlState() {
    if (!window.history?.replaceState) return;
    const params = new URLSearchParams();
    const fields = [
      ["q", elements.search.value.trim()],
      ["organism", elements.organism.value.trim()],
      ["product", elements.product.value.trim()],
      ["gene", elements.gene.value.trim()],
      ["direction", elements.direction.value],
      ["from", elements.yearFrom.value],
      ["to", elements.yearTo.value],
      ["sort", elements.sort.value === "relevance" ? "" : elements.sort.value],
    ];
    fields.forEach(([key, value]) => {
      if (value) params.set(key, value);
    });
    const query = params.toString();
    const nextUrl = `${window.location.pathname}${query ? `?${query}` : ""}${window.location.hash}`;
    window.history.replaceState(null, "", nextUrl);
  }

  function getFilters() {
    return {
      query: normalizeWithAliases(elements.search.value),
      organism: normalizeWithAliases(elements.organism.value),
      product: normalize(elements.product.value),
      gene: normalize(elements.gene.value),
      direction: elements.direction.value,
      yearFrom: safeYear(elements.yearFrom.value),
      yearTo: safeYear(elements.yearTo.value),
      sort: elements.sort.value,
    };
  }

  function relevanceScore(record, terms) {
    if (!terms.length) return 0;
    return terms.reduce((score, term) => {
      if (record._title === term) score += 20;
      else if (record._title.startsWith(term)) score += 10;
      else if (record._title.includes(term)) score += 6;
      if (record._products.includes(term)) score += 14;
      else if (record._product.includes(term)) score += 5;
      if (record._organism.includes(term)) score += 5;
      if (record._genes.includes(term)) score += 16;
      else if (record._genes.some((gene) => gene.includes(term))) score += 7;
      return score;
    }, 0);
  }

  function filterRecords() {
    const filters = getFilters();
    if (filters.yearFrom && filters.yearTo && filters.yearFrom > filters.yearTo) {
      [filters.yearFrom, filters.yearTo] = [filters.yearTo, filters.yearFrom];
      elements.yearFrom.value = String(filters.yearFrom);
      elements.yearTo.value = String(filters.yearTo);
    }
    const terms = filters.query.split(/\s+/).filter(Boolean);
    state.highlightTerms = [...new Set(terms.filter((term) => term.length > 1))];

    const filtered = state.records.filter((record) => {
      if (terms.length && !terms.every((term) => record._search.includes(term))) return false;
      if (filters.organism && !record._organisms.includes(filters.organism)) return false;
      if (filters.product && !record._products.includes(filters.product)) return false;
      if (filters.gene || filters.direction) {
        const matchingGene = record.genes.some((gene, index) =>
          (!filters.gene || record._genes[index] === filters.gene) &&
          (!filters.direction || gene.directions.includes(filters.direction)),
        );
        if (!matchingGene) return false;
      }
      if (filters.yearFrom && record.year < filters.yearFrom) return false;
      if (filters.yearTo && record.year > filters.yearTo) return false;
      return true;
    });

    const hasScorableTerms = terms.some((term) => term.length > 1);
    if (filters.sort === "year-desc" || (filters.sort === "relevance" && !hasScorableTerms)) {
      filtered.sort((a, b) => b.year - a.year || a.title.localeCompare(b.title));
    } else if (filters.sort === "year-asc") {
      filtered.sort((a, b) => a.year - b.year || a.title.localeCompare(b.title));
    } else if (filters.sort === "title") {
      filtered.sort((a, b) => a.title.localeCompare(b.title));
    } else {
      filtered.sort((a, b) => {
        const scoreDifference = relevanceScore(b, terms) - relevanceScore(a, terms);
        return scoreDifference || b.year - a.year || a._index - b._index;
      });
    }

    state.filtered = filtered;
    state.page = Math.min(state.page, Math.max(1, Math.ceil(filtered.length / PAGE_SIZE)));
    writeUrlState();
    renderAll(filters);
  }

  function directionAppearance(directions) {
    if (directions.length > 1) return { className: "mixed", symbol: "±" };
    if (directions[0] === "Positive") return { className: "positive", symbol: "↑" };
    if (directions[0] === "Negative") return { className: "negative", symbol: "↓" };
    return { className: "other", symbol: "◇" };
  }

  function geneMarkup(gene) {
    const appearance = directionAppearance(gene.directions);
    const directionLabel = gene.directions.join(", ") || "Unspecified";
    return `
      <span class="gene-tag ${appearance.className}" title="${escapeHtml(directionLabel)} modification">
        ${escapeHtml(gene.name)}
        <i aria-hidden="true">${appearance.symbol}</i>
        <span class="sr-only">${escapeHtml(directionLabel)} modification</span>
      </span>`;
  }

  function resultCard(record) {
    const visibleGenes = record.genes.slice(0, 9);
    const hiddenGenes = record.genes.slice(visibleGenes.length);
    const additionalGenesId = `additional-genes-${record._index}`;
    const titleMarkup = record.pmid
      ? `<a href="${pubmedUrl(record.pmid)}" target="_blank" rel="noopener noreferrer">${highlight(record._displayTitle)}<span class="sr-only"> (opens in a new tab)</span></a>`
      : highlight(record._displayTitle);
    return `
      <article class="result-card">
        <div class="result-year">${escapeHtml(record.year)}</div>
        <div>
          <h3>${titleMarkup}</h3>
          <div class="record-meta">
            <span><b>Host</b> ${highlight(record.organism || "Not reported")}</span>
            <span><b>Product</b> ${highlight(record.product || "Not reported")}</span>
            ${record.pmid ? `<span><b>PMID</b> ${escapeHtml(record.pmid)}</span>` : ""}
          </div>
          <div class="gene-list" aria-label="Reported gene modifications">
            ${record.genes.length ? visibleGenes.map(geneMarkup).join("") : '<span class="gene-empty">No gene-level modifications extracted</span>'}
            ${hiddenGenes.length ? `
              <span class="additional-genes" id="${additionalGenesId}" hidden>${hiddenGenes.map(geneMarkup).join("")}</span>
              <button class="gene-tag more-genes" type="button" data-expand-genes aria-expanded="false" aria-controls="${additionalGenesId}" data-collapsed-label="+${hiddenGenes.length} more">+${hiddenGenes.length} more</button>
            ` : ""}
          </div>
        </div>
      </article>`;
  }

  function renderResults() {
    elements.loading.hidden = true;
    elements.error.hidden = true;
    elements.export.disabled = state.filtered.length === 0;

    const total = state.filtered.length;
    const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
    const start = (state.page - 1) * PAGE_SIZE;
    const pageRecords = state.filtered.slice(start, start + PAGE_SIZE);

    elements.resultCount.textContent = `${formatNumber(total)} ${total === 1 ? "record" : "records"}`;
    elements.resultContext.textContent = total
      ? `Showing ${formatNumber(start + 1)}–${formatNumber(Math.min(start + PAGE_SIZE, total))} of ${formatNumber(total)}`
      : "Try broadening or removing one of your filters";

    if (!pageRecords.length) {
      elements.results.innerHTML = `
        <div class="empty-results">
          <strong>No matching strain designs</strong>
          <p>Try a broader term, check the spelling of a gene or product, or remove one of the filters.</p>
          <button type="button" data-clear-all>Clear all filters</button>
        </div>`;
      elements.pagination.hidden = true;
      return;
    }

    elements.results.innerHTML = pageRecords.map(resultCard).join("");
    elements.pagination.hidden = totalPages <= 1;
    elements.previous.disabled = state.page <= 1;
    elements.next.disabled = state.page >= totalPages;
    elements.pageStatus.textContent = `Page ${formatNumber(state.page)} of ${formatNumber(totalPages)}`;
  }

  function countValues(records, accessor) {
    const counts = new Map();
    records.forEach((record) => {
      const values = accessor(record);
      const unique = new Map();
      (Array.isArray(values) ? values : [values]).filter(Boolean).forEach((value) => {
        const key = normalize(value);
        if (key && !unique.has(key)) unique.set(key, value);
      });
      unique.forEach((label, key) => {
        const current = counts.get(key) || { label, count: 0 };
        current.count += 1;
        counts.set(key, current);
      });
    });
    return [...counts.values()]
      .map(({ label, count }) => [label, count])
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  }

  function renderRanking(element, entries, filterName) {
    if (!entries.length) {
      element.innerHTML = '<li><span class="rank-label">No values in this result set</span></li>';
      return;
    }
    const max = entries[0][1] || 1;
    element.innerHTML = entries.slice(0, 5).map(([label, count]) => `
      <li>
        <span class="rank-label">
          <button type="button" data-rank-filter="${filterName}" data-rank-value="${escapeHtml(label)}" title="Filter by ${escapeHtml(label)}">${escapeHtml(label)}</button>
        </span>
        <span class="rank-value">${formatNumber(count)}</span>
        <span class="rank-bar"><span style="width:${Math.max(3, (count / max) * 100).toFixed(1)}%"></span></span>
      </li>`).join("");
  }

  function renderInsights() {
    const records = state.filtered;
    const directionCounts = { Positive: 0, Negative: 0, Other: 0 };
    records.forEach((record) => {
      record.genes.forEach((gene) => {
        gene.directions.forEach((direction) => {
          if (directionCounts[direction] !== undefined) directionCounts[direction] += 1;
        });
      });
    });

    const directionTotal = Object.values(directionCounts).reduce((sum, value) => sum + value, 0) || 1;
    elements.modificationCount.textContent = formatNumber(
      Object.values(directionCounts).reduce((sum, value) => sum + value, 0),
    );
    elements.positiveCount.textContent = formatNumber(directionCounts.Positive);
    elements.negativeCount.textContent = formatNumber(directionCounts.Negative);
    elements.otherCount.textContent = formatNumber(directionCounts.Other);
    elements.positiveBar.style.width = `${(directionCounts.Positive / directionTotal) * 100}%`;
    elements.negativeBar.style.width = `${(directionCounts.Negative / directionTotal) * 100}%`;
    elements.otherBar.style.width = `${(directionCounts.Other / directionTotal) * 100}%`;

    renderRanking(elements.topOrganisms, countValues(records, (record) => record.organisms), "organism");
    renderRanking(elements.topProducts, countValues(records, (record) => record.products), "product");
  }

  function renderActiveFilters(filters) {
    const chips = [];
    const add = (label, value, target) => {
      if (value) chips.push({ label, value, target });
    };
    add("Search", elements.search.value.trim(), "search");
    add("Organism", elements.organism.value.trim(), "organism");
    add("Product", elements.product.value.trim(), "product");
    add("Gene", elements.gene.value.trim(), "gene");
    add("Direction", filters.direction, "direction");
    add("From", elements.yearFrom.value, "yearFrom");
    add("To", elements.yearTo.value, "yearTo");
    elements.activeFilters.innerHTML = chips.length
      ? chips.map((chip) => `
          <span class="filter-chip">
            <span>${escapeHtml(chip.label)}: ${escapeHtml(chip.value)}</span>
            <button type="button" data-remove-filter="${chip.target}" aria-label="Remove ${escapeHtml(chip.label)} filter">×</button>
          </span>`).join("")
      : '<span class="filter-chip">All database records</span>';
  }

  function renderAll(filters = getFilters()) {
    renderActiveFilters(filters);
    renderResults();
    renderInsights();
  }

  function scheduleFilter(resetPage = true) {
    if (resetPage) state.page = 1;
    window.clearTimeout(state.debounce);
    state.debounce = window.setTimeout(filterRecords, 170);
  }

  function clearFilters() {
    elements.search.value = "";
    elements.organism.value = "";
    elements.product.value = "";
    elements.gene.value = "";
    elements.direction.value = "";
    elements.yearFrom.value = "";
    elements.yearTo.value = "";
    elements.sort.value = "relevance";
    state.page = 1;
    filterRecords();
  }

  function removeFilter(target) {
    const element = elements[target];
    if (!element) return;
    element.value = "";
    state.page = 1;
    filterRecords();
  }

  function csvCell(value) {
    let text = String(value ?? "");
    if (/^[\u0000-\u0020]*[=+\-@]/.test(text)) text = `'${text}`;
    return `"${text.replaceAll('"', '""')}"`;
  }

  function exportCsv() {
    if (!state.filtered.length) return;
    const header = ["PMID", "Title", "Year", "Organism", "Product", "Genes_and_modifications"];
    const rows = state.filtered.map((record) => [
      record.pmid,
      record._displayTitle,
      record.year,
      record.organism,
      record.product,
      record.genes.map((gene) => `${gene.name}: ${gene.directions.join("|")}`).join("; "),
    ]);
    const csv = [header, ...rows].map((row) => row.map(csvCell).join(",")).join("\r\n");
    const blob = new Blob(["\ufeff", csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `ELISER_filtered_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  function bindEvents() {
    [elements.search, elements.organism, elements.product, elements.gene].forEach((input) => {
      input.addEventListener("input", () => scheduleFilter(true));
    });
    [elements.direction, elements.yearFrom, elements.yearTo, elements.sort].forEach((input) => {
      input.addEventListener("change", () => scheduleFilter(true));
    });
    elements.searchForm.addEventListener("submit", (event) => {
      event.preventDefault();
      window.clearTimeout(state.debounce);
      state.page = 1;
      filterRecords();
    });
    elements.clear.addEventListener("click", clearFilters);
    elements.export.addEventListener("click", exportCsv);
    elements.previous.addEventListener("click", () => {
      if (state.page <= 1) return;
      state.page -= 1;
      renderResults();
      elements.resultCount.focus({ preventScroll: true });
      elements.results.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    elements.next.addEventListener("click", () => {
      if (state.page >= Math.ceil(state.filtered.length / PAGE_SIZE)) return;
      state.page += 1;
      renderResults();
      elements.resultCount.focus({ preventScroll: true });
      elements.results.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    document.addEventListener("click", (event) => {
      const removeButton = event.target.closest("[data-remove-filter]");
      if (removeButton) removeFilter(removeButton.dataset.removeFilter);

      const clearButton = event.target.closest("[data-clear-all]");
      if (clearButton) clearFilters();

      const expandButton = event.target.closest("[data-expand-genes]");
      if (expandButton) {
        const additionalGenes = document.getElementById(expandButton.getAttribute("aria-controls"));
        if (additionalGenes) {
          const willExpand = additionalGenes.hidden;
          additionalGenes.hidden = !willExpand;
          expandButton.setAttribute("aria-expanded", String(willExpand));
          expandButton.textContent = willExpand ? "Show fewer" : expandButton.dataset.collapsedLabel;
        }
      }

      const rankButton = event.target.closest("[data-rank-filter]");
      if (rankButton) {
        const target = rankButton.dataset.rankFilter;
        const value = rankButton.dataset.rankValue;
        if (elements[target]) {
          elements[target].value = value;
          state.page = 1;
          filterRecords();
          elements.resultCount.focus({ preventScroll: true });
          document.querySelector("#explore").scrollIntoView({ behavior: "smooth" });
        }
      }
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "/" && !/input|select|textarea/i.test(document.activeElement.tagName)) {
        event.preventDefault();
        elements.search.focus();
      }
      if (event.key === "Escape" && document.activeElement === elements.search) {
        elements.search.value = "";
        scheduleFilter(true);
      }
    });
  }

  async function initialize() {
    bindEvents();
    try {
      const response = await fetch(DATA_URL);
      if (!response.ok) throw new Error(`Data request failed: ${response.status}`);
      const database = await response.json();
      state.meta = database.meta;
      state.records = database.records.map((record, index) => ({
        ...record,
        organisms: record.organisms || [record.organism],
        products: record.products || splitProducts(record.product),
        _index: index,
        _displayTitle: stripPubMedMarkup(record.title),
        _search: buildSearchIndex(record),
        _title: normalize(stripPubMedMarkup(record.title)),
        _organism: normalize(record.organism),
        _organisms: [...new Set([
          normalize(record.organism),
          ...(record.organisms || [record.organism]).map(normalize),
        ].filter(Boolean))],
        _product: normalize(record.product),
        _products: (record.products || splitProducts(record.product)).map(normalize),
        _genes: record.genes.map((gene) => normalize(gene.name)),
      }));

      setHeroStats(database.meta);
      populateSelectYears(database.meta);
      populateDatalist("#organism-suggestions", database.meta.organismSuggestions || []);
      populateDatalist("#product-suggestions", database.meta.productSuggestions || []);
      populateDatalist("#gene-suggestions", database.meta.geneSuggestions || []);
      readUrlState();
      filterRecords();
    } catch (error) {
      console.error(error);
      elements.loading.hidden = true;
      elements.error.hidden = false;
      elements.resultCount.textContent = "Database unavailable";
      elements.resultContext.textContent = "See the message below for the likely cause";
    }
  }

  initialize();
})();
