const initialApps = window.__INITIAL_APPS__ || null;
const detailData = window.__APP_DETAIL__ || null;
const TABLER_VERSION = "3.40.0";
const iconChoices = [
  "cube",
  "server",
  "database",
  "cloud",
  "shield",
  "world",
  "home",
  "settings",
  "tool",
  "tools",
  "wrench",
  "terminal-2",
  "command",
  "brand-docker",
  "brand-youtube",
  "device-tv",
  "device-desktop",
  "device-laptop",
  "router",
  "wifi",
  "player-play",
  "movie",
  "photo",
  "camera",
  "music",
  "disc",
  "cast",
  "apps",
  "layout-dashboard",
  "layout-grid",
  "stack-2",
  "package",
  "archive",
  "folder",
  "folders",
  "file-text",
  "download",
  "upload",
  "refresh",
  "activity",
  "bolt",
  "flame",
  "rocket",
  "star",
  "heart",
  "lock",
  "key",
  "search",
  "chart-bar",
  "chart-pie",
  "cpu",
];

function randomColor() {
  const hue = Math.floor(Math.random() * 360);
  const saturation = 65 + Math.floor(Math.random() * 20);
  const lightness = 45 + Math.floor(Math.random() * 10);
  return hslToHex(hue, saturation, lightness);
}

function hslToHex(h, s, l) {
  s /= 100;
  l /= 100;
  const k = (n) => (n + h / 30) % 12;
  const a = s * Math.min(l, 1 - l);
  const f = (n) =>
    Math.round(255 * (l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)))))
      .toString(16)
      .padStart(2, "0");
  return `#${f(0)}${f(8)}${f(4)}`;
}

function wireColorInputs() {
  document.querySelectorAll("[data-color-input]").forEach((input) => {
    if (input.hasAttribute("data-randomize-color")) {
      input.value = randomColor();
    }
  });
}

function wireIconPickers() {
  document.querySelectorAll(".icon-picker-field").forEach((field) => {
    const picker = field.querySelector("[data-icon-picker]");
    const hiddenInput = field.querySelector("[data-icon-value]");
    const popup = field.querySelector("[data-icon-popup]");
    const trigger = field.querySelector("[data-icon-trigger]");
    const searchInput = field.querySelector("[data-icon-search]");
    const preview = field.querySelector("[data-icon-preview]");
    const label = field.querySelector("[data-icon-label]");

    if (!picker || !hiddenInput || !popup || !trigger || !searchInput || !preview || !label) return;

    const drawPreview = (iconName) => {
      preview.innerHTML = tablerIconImage(iconName, "icon-inline-image");
      label.textContent = iconName;
    };

    const renderChoices = (query = "") => {
      const normalized = query.trim().toLowerCase();
      const currentValue = iconChoices.includes(hiddenInput.value) ? hiddenInput.value : "cube";
      const filtered = iconChoices.filter((icon) => icon.includes(normalized));
      picker.innerHTML = filtered
        .map(
          (icon) => `
            <button
              type="button"
              class="icon-choice${icon === currentValue ? " is-selected" : ""}"
              data-icon-choice="${escapeHtml(icon)}"
              aria-label="Choose ${escapeHtml(icon)}"
              title="${escapeHtml(icon)}"
            >
              ${tablerIconImage(icon, "icon-choice-image")}
            </button>
          `
        )
        .join("");

      picker.querySelectorAll("[data-icon-choice]").forEach((button) => {
        button.addEventListener("click", () => {
          hiddenInput.value = button.dataset.iconChoice || "cube";
          drawPreview(hiddenInput.value);
          renderChoices(searchInput.value);
          popup.hidden = true;
        });
      });
    };

    const currentValue = iconChoices.includes(hiddenInput.value) ? hiddenInput.value : "cube";
    hiddenInput.value = currentValue;
    drawPreview(currentValue);
    renderChoices();

    trigger.addEventListener("click", () => {
      popup.hidden = !popup.hidden;
      if (!popup.hidden) {
        searchInput.focus();
        searchInput.select();
      }
    });

    searchInput.addEventListener("input", () => {
      renderChoices(searchInput.value);
    });

    document.addEventListener("click", (event) => {
      if (!field.contains(event.target)) {
        popup.hidden = true;
      }
    });
  });
}

function tablerIconUrl(name) {
  return `https://unpkg.com/@tabler/icons@${TABLER_VERSION}/icons/outline/${name}.svg`;
}

function tablerIconImage(name, className = "tabler-icon-image") {
  const safeName = iconChoices.includes(name) ? name : "cube";
  return `<img class="${className}" src="${tablerIconUrl(safeName)}" alt="${escapeHtml(safeName)}" onerror="this.onerror=null;this.src='${tablerIconUrl("cube")}';" />`;
}

function createLinkRow(containerId, link = { label: "", url: "" }) {
  const container = document.getElementById(containerId);
  if (!container) return;
  const row = document.createElement("div");
  row.className = "link-row";
  row.innerHTML = `
    <input type="text" name="link_label" placeholder="Link label" value="${escapeHtml(link.label)}" />
    <input type="url" name="link_url" placeholder="https://service.local" value="${escapeHtml(link.url)}" />
    <button type="button" class="danger-button">Remove</button>
  `;
  row.querySelector("button").addEventListener("click", () => row.remove());
  container.appendChild(row);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function collectLinks(form) {
  const labels = Array.from(form.querySelectorAll('input[name="link_label"]'));
  const urls = Array.from(form.querySelectorAll('input[name="link_url"]'));
  return labels
    .map((input, idx) => ({
      label: input.value.trim(),
      url: urls[idx]?.value.trim() || "",
    }))
    .filter((item) => item.label && item.url);
}

async function sendJson(url, options) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (response.status === 204) {
    return null;
  }
  const data = await response.json();
  if (!response.ok) {
    throw data;
  }
  return data;
}

function wireCreateModal() {
  const modal = document.getElementById("create-modal");
  const openButton = document.querySelector("[data-open-create]");
  const closeButton = document.querySelector("[data-close-modal]");
  const form = document.getElementById("create-app-form");
  const message = document.getElementById("create-form-message");

  if (!modal || !openButton || !closeButton || !form) return;

  openButton.addEventListener("click", () => {
    modal.showModal();
  });
  closeButton.addEventListener("click", () => modal.close());

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await sendJson("/api/discovery/sync", {
        method: "POST",
      });
      message.textContent = "Scanned. Reloading...";
      window.location.reload();
    } catch (error) {
      message.textContent = error.detail?.message || error.detail || "Could not scan apps.";
    }
  });
}

function wireLinkButtons() {
  document.querySelectorAll("[data-add-link]").forEach((button) => {
    button.addEventListener("click", () => {
      createLinkRow(button.dataset.addLink);
    });
  });
}

function renderCard(app) {
  const links = app.links?.length
    ? app.links
        .slice(0, 3)
        .map((link) => `<a href="${link.url}" target="_blank" rel="noreferrer">${escapeHtml(link.label)}</a>`)
        .join("")
    : '<span class="muted">No links</span>';
  const missingClass = app.runtime.folder_exists ? "" : " app-tile-missing";
  const statusText = app.runtime.folder_exists ? app.runtime.health : "Folder not found";
  const statusClass = app.runtime.folder_exists ? "" : ' class="missing-label"';

  return `
    <article class="app-tile${missingClass}" data-app-id="${app.id}">
      <a class="app-tile-link" href="/apps/${app.id}">
        <div class="app-icon-shell">
          <div class="app-icon app-icon-dashboard" style="--app-color: ${app.color};">
            ${tablerIconImage(app.icon)}
          </div>
          <span class="app-health-dot health-${escapeHtml(app.runtime.health)}" title="${escapeHtml(app.runtime.health)}"></span>
          <span class="app-settings-chip">Settings</span>
        </div>
        <div class="app-labels">
          <h3>${escapeHtml(app.name)}</h3>
          <p${statusClass}>${escapeHtml(statusText)}</p>
        </div>
      </a>
      <div class="app-tile-links">${links}</div>
    </article>
  `;
}

function wireDashboard() {
  if (!initialApps) return;
  wireCreateModal();
}

function renderServiceList(runtime) {
  const target = document.getElementById("service-status-list");
  if (!target) return;
  if (!runtime.services?.length) {
    target.innerHTML = '<p class="muted">No running services detected yet.</p>';
    return;
  }
  target.innerHTML = runtime.services
    .map(
      (service) => `
      <div class="service-row">
        <div>
          <strong>${escapeHtml(service.name)}</strong>
          <p>${escapeHtml(service.published_ports?.join(", ") || "No published ports")}</p>
        </div>
        <div class="status-row">
          <span class="status-pill state-${escapeHtml(service.state)}">${escapeHtml(service.state)}</span>
          <span class="status-pill health-${escapeHtml(service.health)}">${escapeHtml(service.health)}</span>
        </div>
      </div>
    `
    )
    .join("");
}

function wireDetail() {
  if (!detailData) return;

  const appId = detailData.app.id;
  const updateForm = document.getElementById("update-app-form");
  const updateMessage = document.getElementById("update-form-message");
  const actionMessage = document.getElementById("action-message");
  const deleteButton = document.getElementById("delete-app");

  if ((detailData.app.links || []).length) {
    detailData.app.links.forEach((link) => createLinkRow("update-links", link));
  } else {
    createLinkRow("update-links");
  }

  document.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      actionMessage.textContent = "Running action...";
      try {
        const result = await sendJson(`/api/apps/${appId}/actions`, {
          method: "POST",
          body: JSON.stringify({ action: button.dataset.action }),
        });
        actionMessage.textContent = result.message || "Action finished.";
        renderServiceList(result.runtime);
        window.setTimeout(() => window.location.reload(), 500);
      } catch (error) {
        actionMessage.textContent = error.detail?.message || "Action failed.";
        if (error.detail?.runtime) {
          renderServiceList(error.detail.runtime);
        }
      }
    });
  });

  if (updateForm) {
    updateForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const payload = {
        name: updateForm.name.value.trim(),
        folder_path: updateForm.folder_path.value.trim(),
        compose_file: updateForm.compose_file.value.trim() || null,
        icon: updateForm.icon.value.trim() || "cube",
        color: updateForm.color.value,
        notes: updateForm.notes.value.trim(),
        links: collectLinks(updateForm),
      };
      try {
        await sendJson(`/api/apps/${appId}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
        updateMessage.textContent = "Saved.";
        window.setTimeout(() => window.location.reload(), 350);
      } catch (error) {
        updateMessage.textContent = error.detail?.message || error.detail || "Could not save changes.";
      }
    });
  }

  if (deleteButton) {
    deleteButton.addEventListener("click", async () => {
      const confirmed = window.confirm("Delete this app from the dashboard?");
      if (!confirmed) return;
      try {
        await sendJson(`/api/apps/${appId}`, { method: "DELETE" });
        window.location.href = "/";
      } catch {
        updateMessage.textContent = "Could not delete app.";
      }
    });
  }
}

wireLinkButtons();
wireColorInputs();
wireIconPickers();
wireDashboard();
wireDetail();
