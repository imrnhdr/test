// ── Hard Tech News Aggregator ────────────────────────────────────────────────

(function () {
  "use strict";

  // ── State ───────────────────────────────────────────────────────────────

  let newsData = {};        // { category: [articles] }
  let activeCategory = "All";
  let searchQuery = "";

  // ── DOM refs ────────────────────────────────────────────────────────────

  const $categories = document.getElementById("categories");
  const $articles = document.getElementById("articles");
  const $status = document.getElementById("status");
  const $error = document.getElementById("error");
  const $count = document.getElementById("article-count");
  const $refresh = document.getElementById("refresh-btn");
  const $search = document.getElementById("search-input");

  // ── Category display order ──────────────────────────────────────────────

  const CATEGORY_ORDER = [
    "All",
    "Hard Tech",
    "Defense & Aerospace",
    "Energy & Nuclear",
    "Robotics",
    "Semiconductors",
    "Biotech",
    "Space",
    "Manufacturing",
    "Quantum & Computing",
    "Publications",
  ];

  // ── Fetch news from backend ─────────────────────────────────────────────

  async function loadNews() {
    $status.classList.remove("hidden");
    $error.classList.add("hidden");
    $articles.innerHTML = "";
    $count.textContent = "";
    $refresh.classList.add("spinning");

    try {
      const resp = await fetch("/api/news");
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      newsData = await resp.json();
      renderCategories();
      renderArticles();
    } catch (err) {
      $error.classList.remove("hidden");
      console.error("Failed to load news:", err);
    } finally {
      $status.classList.add("hidden");
      $refresh.classList.remove("spinning");
    }
  }

  // Make loadNews available globally for the retry button
  window.loadNews = loadNews;

  // ── Render category tabs ────────────────────────────────────────────────

  function renderCategories() {
    $categories.innerHTML = "";

    for (const cat of CATEGORY_ORDER) {
      if (!newsData[cat] || newsData[cat].length === 0) continue;

      const btn = document.createElement("button");
      btn.className = "cat-btn" + (cat === activeCategory ? " active" : "");
      btn.setAttribute("role", "tab");
      btn.setAttribute("aria-selected", cat === activeCategory);

      const count = newsData[cat].length;
      btn.innerHTML =
        escapeHtml(cat) +
        '<span class="cat-count">' + count + "</span>";

      btn.addEventListener("click", function () {
        activeCategory = cat;
        renderCategories();
        renderArticles();
      });

      $categories.appendChild(btn);
    }
  }

  // ── Render article cards ────────────────────────────────────────────────

  function renderArticles() {
    $articles.innerHTML = "";

    let articles = newsData[activeCategory] || [];

    // Apply search filter
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      articles = articles.filter(function (a) {
        return (
          a.title.toLowerCase().includes(q) ||
          (a.description && a.description.toLowerCase().includes(q)) ||
          (a.source && a.source.toLowerCase().includes(q))
        );
      });
    }

    // Update count badge
    const total = newsData["All"] ? newsData["All"].length : 0;
    $count.textContent = total + " articles";

    if (articles.length === 0) {
      $articles.innerHTML =
        '<div class="empty-state">No articles found' +
        (searchQuery ? " matching your filter" : "") +
        ".</div>";
      return;
    }

    var fragment = document.createDocumentFragment();

    for (var i = 0; i < articles.length; i++) {
      fragment.appendChild(createCard(articles[i]));
    }

    $articles.appendChild(fragment);
  }

  // ── Create a single article card ───────────────────────────────────────

  function createCard(article) {
    var card = document.createElement("a");
    card.className = "card";
    card.href = article.link;
    card.target = "_blank";
    card.rel = "noopener noreferrer";

    // Meta row: category + source + date
    var meta = document.createElement("div");
    meta.className = "card-meta";

    var catSpan = document.createElement("span");
    catSpan.className = "card-category";
    catSpan.setAttribute("data-cat", article.category || "");
    catSpan.textContent = article.category || "";
    meta.appendChild(catSpan);

    if (article.source) {
      var srcSpan = document.createElement("span");
      srcSpan.className = "card-source";
      srcSpan.textContent = article.source;
      meta.appendChild(srcSpan);
    }

    var dateSpan = document.createElement("span");
    dateSpan.className = "card-date";
    dateSpan.textContent = formatDate(article.date);
    meta.appendChild(dateSpan);

    card.appendChild(meta);

    // Title
    var title = document.createElement("div");
    title.className = "card-title";
    title.textContent = article.title;
    card.appendChild(title);

    // Description
    if (article.description) {
      var desc = document.createElement("div");
      desc.className = "card-desc";
      desc.textContent = article.description;
      card.appendChild(desc);
    }

    return card;
  }

  // ── Helpers ─────────────────────────────────────────────────────────────

  function formatDate(dateStr) {
    if (!dateStr) return "";
    try {
      var d = new Date(dateStr);
      if (isNaN(d.getTime())) return dateStr;

      var now = new Date();
      var diffMs = now - d;
      var diffHrs = Math.floor(diffMs / 3600000);
      var diffMins = Math.floor(diffMs / 60000);

      if (diffMins < 1) return "just now";
      if (diffMins < 60) return diffMins + "m ago";
      if (diffHrs < 24) return diffHrs + "h ago";

      var diffDays = Math.floor(diffHrs / 24);
      if (diffDays === 1) return "yesterday";
      if (diffDays < 7) return diffDays + "d ago";

      return d.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      });
    } catch (e) {
      return dateStr;
    }
  }

  function escapeHtml(str) {
    var div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  // ── Event listeners ─────────────────────────────────────────────────────

  $refresh.addEventListener("click", loadNews);

  var searchTimeout;
  $search.addEventListener("input", function () {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(function () {
      searchQuery = $search.value.trim();
      renderArticles();
    }, 200);
  });

  // Handle keyboard shortcut: / to focus search
  document.addEventListener("keydown", function (e) {
    if (e.key === "/" && document.activeElement !== $search) {
      e.preventDefault();
      $search.focus();
    }
    if (e.key === "Escape" && document.activeElement === $search) {
      $search.value = "";
      searchQuery = "";
      $search.blur();
      renderArticles();
    }
  });

  // ── Init ────────────────────────────────────────────────────────────────

  loadNews();
})();
