(function () {
  "use strict";

  const catalogUrl = "./catalog.json";
  const providersUrl = "./providers.json";
  const channels = ["stable", "beta", "archived"];
  let catalog = { channels: { stable: [], beta: [], archived: [] } };
  let activeChannel = "stable";

  const $ = (selector) => document.querySelector(selector);
  const escapeHtml = (value) => String(value == null ? "" : value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[char]));
  const safeHttpsUrl = (value) => {
    try {
      const url = new URL(value);
      return url.protocol === "https:" ? url.href : "";
    } catch (_) {
      return "";
    }
  };

  function channelEntries(name) {
    const value = catalog && catalog.channels && catalog.channels[name];
    return Array.isArray(value) ? value : [];
  }

  function updateStats() {
    const counts = {};
    channels.forEach((name) => {
      counts[name] = channelEntries(name).length;
      $("#count-" + name).textContent = counts[name];
      $("#stat-" + name).textContent = counts[name];
    });
    $("#stat-total").textContent = channels.reduce((sum, name) => sum + counts[name], 0);
  }

  function renderVersions() {
    const query = $("#version-search").value.trim().toLowerCase();
    const entries = channelEntries(activeChannel).filter((entry) => {
      const haystack = [entry.id, entry.version, entry.name, entry.source, entry.notes].join(" ").toLowerCase();
      return haystack.includes(query);
    });
    const list = $("#version-list");
    if (!entries.length) {
      list.innerHTML = '<div class="empty-state"><div class="empty-icon">◌</div><strong>' +
        (query ? "No se encontraron coincidencias" : "Todavía no hay versiones publicadas") +
        '</strong><p>' + (query ? "Prueba con otro número o nombre de versión." : "Las versiones aparecerán aquí cuando hayan sido verificadas y publicadas en el catálogo.") + "</p></div>";
      return;
    }
    list.innerHTML = entries.map((entry) => {
      const source = safeHttpsUrl(entry.source);
      const channelClass = activeChannel === "stable" ? "channel-stable" : (activeChannel === "beta" ? "channel-beta" : "");
      const isExternalReference = entry.entry_type === "external_reference";
      const digest = isExternalReference
        ? "Referencia externa · sin APK alojado"
        : (entry.sha256 ? "SHA-256 " + escapeHtml(entry.sha256.slice(0, 12)) + "…" : "SHA-256 pendiente");
      const size = Number.isInteger(entry.size_bytes) && entry.size_bytes > 0 ? (entry.size_bytes / 1048576).toFixed(1) + " MB" : "";
      return '<article class="version-card"><div class="version-main"><div class="version-icon">⬡</div><div class="version-name"><strong>' +
        escapeHtml(entry.name) + " · " + escapeHtml(entry.version) +
        '</strong><small>' + escapeHtml(entry.id) + '</small><div class="version-tags"><span class="mini-tag ' + channelClass + '">' +
        escapeHtml(activeChannel.toUpperCase()) + '</span>' + (size ? '<span class="mini-tag">' + size + '</span>' : "") +
        (entry.platform ? '<span class="mini-tag">' + escapeHtml(entry.platform) + '</span>' : "") +
        (isExternalReference ? '<span class="mini-tag">No descargable desde Dash Launcher</span>' : "") +
        '</div></div></div><div class="version-actions"><span class="version-digest">' + digest +
        '</span>' + (source ? '<a class="source-button" href="' + escapeHtml(source) + '" target="_blank" rel="noopener noreferrer">' + (isExternalReference ? "Abrir proveedor ↗" : "Abrir origen ↗") + '</a>' : '<span class="mini-tag">Origen no válido</span>') +
        '</div></article>';
    }).join("");
  }

  function renderProviders(providers) {
    const list = $("#provider-list");
    const items = Array.isArray(providers) ? providers : [];
    $("#provider-count").textContent = items.length + " FUENTES";
    if (!items.length) {
      list.innerHTML = '<div class="provider-loading">No hay fuentes registradas.</div>';
      return;
    }
    list.innerHTML = items.map((provider) => {
      const url = safeHttpsUrl(provider.url);
      const status = escapeHtml(provider.status || "Referencia");
      const statusClass = provider.status_class === "official" ? "official" : (provider.status_class === "partial" ? "partial" : (provider.status_class === "legacy" ? "legacy" : ""));
      return '<article class="provider-card"><div class="provider-mark">' + escapeHtml(provider.mark || "↗") +
        '</div><div class="provider-body"><div class="provider-title-row"><strong>' + escapeHtml(provider.name) +
        '</strong><span class="provider-status ' + statusClass + '">' + status +
        '</span></div><p>' + escapeHtml(provider.description) +
        '</p><div class="provider-scope">' + escapeHtml(provider.scope || "") +
        '</div>' + (url ? '<a class="provider-link" href="' + escapeHtml(url) + '" target="_blank" rel="noopener noreferrer">Abrir fuente externa ↗</a>' : "") +
        '</div></article>';
    }).join("");
  }

  async function loadCatalog() {
    const refresh = $("#refresh-button");
    refresh.disabled = true;
    refresh.innerHTML = "<span>↻</span> Cargando";
    $("#catalog-state").innerHTML = '<span class="status-dot"></span> Actualizando catálogo';
    try {
      const response = await fetch(catalogUrl + "?v=" + Date.now(), { cache: "no-store" });
      if (!response.ok) throw new Error("HTTP " + response.status);
      const data = await response.json();
      if (!data || !data.channels || !channels.every((name) => Array.isArray(data.channels[name]))) {
        throw new Error("Formato de catálogo no válido");
      }
      catalog = data;
      updateStats();
      renderVersions();
      $("#catalog-state").innerHTML = '<span class="status-dot"></span> Catálogo conectado';
      const updated = data.updated_at ? new Date(data.updated_at) : null;
      $("#catalog-updated").textContent = "Última actualización: " + (updated && !Number.isNaN(updated.getTime()) ? updated.toLocaleString("es-ES") : "sin publicaciones");
    } catch (error) {
      $("#catalog-state").textContent = "No se pudo conectar con el catálogo";
      $("#catalog-updated").textContent = "Comprueba la publicación de GitHub Pages";
      $("#version-list").innerHTML = '<div class="empty-state"><div class="empty-icon">!</div><strong>Catálogo no disponible</strong><p>El panel está publicado, pero no pudo cargar catalog.json. Revisa el despliegue de GitHub Pages.</p></div>';
    } finally {
      refresh.disabled = false;
      refresh.innerHTML = "<span>↻</span> Actualizar";
    }
  }

  async function loadProviders() {
    try {
      const response = await fetch(providersUrl, { cache: "no-store" });
      if (!response.ok) throw new Error("HTTP " + response.status);
      renderProviders(await response.json());
    } catch (_) {
      $("#provider-list").innerHTML = '<div class="provider-loading">No se pudo cargar el directorio de fuentes.</div>';
    }
  }

  document.querySelectorAll("[data-channel]").forEach((button) => {
    button.addEventListener("click", () => {
      activeChannel = button.dataset.channel;
      document.querySelectorAll("[data-channel]").forEach((tab) => {
        const selected = tab === button;
        tab.classList.toggle("active", selected);
        tab.setAttribute("aria-selected", selected ? "true" : "false");
      });
      renderVersions();
    });
  });
  $("#version-search").addEventListener("input", renderVersions);
  $("#refresh-button").addEventListener("click", loadCatalog);
  loadCatalog();
  loadProviders();
})();