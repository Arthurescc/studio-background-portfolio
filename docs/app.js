const state = {
  assets: [],
  batches: [],
  query: "",
  batch: "all",
  shown: 0,
  pageSize: 36,
};

const $ = (selector) => document.querySelector(selector);
const grid = $("#galleryGrid");
const empty = $("#emptyState");
const loadMore = $("#loadMore");
const template = $("#cardTemplate");

function filteredAssets() {
  const needle = state.query.trim().toLowerCase();
  return state.assets.filter((asset) => {
    const inBatch = state.batch === "all" || asset.batchId === state.batch;
    const inSearch = !needle || `${asset.title} ${asset.batchName} ${asset.sourcePath}`.toLowerCase().includes(needle);
    return inBatch && inSearch;
  });
}

function render() {
  const items = filteredAssets();
  const visible = items.slice(0, state.shown);
  grid.replaceChildren();

  visible.forEach((asset) => {
    const card = template.content.cloneNode(true);
    const link = card.querySelector("a");
    const image = card.querySelector("img");
    link.href = asset.originalUrl;
    image.src = asset.thumbnail;
    image.alt = asset.title;
    card.querySelector("h3").textContent = asset.title;
    card.querySelector("p").textContent = `${asset.batchName} · ${asset.width}×${asset.height}`;
    card.querySelector(".download-image").href = asset.originalUrl;
    card.querySelector(".download-pack").href = asset.archiveUrl;
    grid.append(card);
  });

  if (state.assets.length === 0) {
    empty.querySelector("h3").textContent = "首批素材待发布";
    empty.querySelector("p").textContent = "发布第一个 ZIP Release 后，原图与预览会自动出现在这里。";
  } else {
    empty.querySelector("h3").textContent = "还没有匹配的素材";
    empty.querySelector("p").textContent = "换一个关键词或批次试试。";
  }
  empty.hidden = items.length !== 0;
  loadMore.hidden = visible.length >= items.length || items.length === 0;
}

function setBatch(batchId) {
  state.batch = batchId;
  state.shown = state.pageSize;
  $("#batchSelect").value = batchId;
  document.querySelectorAll(".batch-chip").forEach((chip) => {
    chip.classList.toggle("active", chip.dataset.batch === batchId);
  });
  render();
}

function renderBatches() {
  const select = $("#batchSelect");
  const strip = $("#batchStrip");
  const allChip = document.createElement("button");
  allChip.className = "batch-chip active";
  allChip.dataset.batch = "all";
  allChip.textContent = `全部 ${state.assets.length}`;
  allChip.addEventListener("click", () => setBatch("all"));
  strip.append(allChip);

  state.batches.forEach((batch) => {
    const option = document.createElement("option");
    option.value = batch.id;
    option.textContent = `${batch.name} (${batch.count})`;
    select.append(option);

    const chip = document.createElement("button");
    chip.className = "batch-chip";
    chip.dataset.batch = batch.id;
    chip.textContent = `${batch.name} ${batch.count}`;
    chip.addEventListener("click", () => setBatch(batch.id));
    strip.append(chip);
  });
}

async function boot() {
  try {
    const response = await fetch(`./data/catalog.json?v=${Date.now()}`);
    if (!response.ok) throw new Error("catalog unavailable");
    const catalog = await response.json();
    state.assets = catalog.assets || [];
    state.batches = catalog.batches || [];
    state.shown = state.pageSize;

    $("#assetCount").textContent = state.assets.length.toLocaleString();
    $("#batchCount").textContent = state.batches.length.toLocaleString();
    const repo = catalog.repositoryUrl || "https://github.com";
    $("#repoLink").href = repo;
    $("#releasesLink").href = `${repo}/releases`;
    $("#heroDownload").href = `${repo}/releases`;

    renderBatches();
    render();
  } catch (error) {
    empty.hidden = false;
    empty.querySelector("h3").textContent = "素材库正在初始化";
    empty.querySelector("p").textContent = "发布第一个 Release 压缩包后，预览会自动出现在这里。";
  }
}

$("#searchInput").addEventListener("input", (event) => {
  state.query = event.target.value;
  state.shown = state.pageSize;
  render();
});
$("#batchSelect").addEventListener("change", (event) => setBatch(event.target.value));
loadMore.addEventListener("click", () => {
  state.shown += state.pageSize;
  render();
});

boot();
