const initialApps = window.__INITIAL_APPS__ || null;
const detailData = window.__APP_DETAIL__ || null;

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
    if (!document.getElementById("create-links").children.length) {
      createLinkRow("create-links");
    }
    modal.showModal();
  });
  closeButton.addEventListener("click", () => modal.close());

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
      name: form.name.value.trim(),
      folder_path: form.folder_path.value.trim(),
      compose_file: form.compose_file.value.trim() || null,
      icon: form.icon.value.trim() || "cube",
      color: form.color.value,
      notes: form.notes.value.trim(),
      links: collectLinks(form),
    };
    try {
      await sendJson("/api/apps", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      message.textContent = "Saved. Reloading dashboard...";
      window.location.reload();
    } catch (error) {
      message.textContent = error.detail?.message || error.detail || "Could not save app.";
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

async function refreshGrid() {
  const grid = document.getElementById("app-grid");
  if (!grid) return;
  const data = await sendJson("/api/apps", { method: "GET" });
  const apps = data.apps || [];
  if (!apps.length) {
    window.location.reload();
    return;
  }
  grid.innerHTML = apps.map(renderCard).join("");
}

function renderCard(app) {
  const links = app.links?.length
    ? app.links
        .slice(0, 3)
        .map((link) => `<a href="${link.url}" target="_blank" rel="noreferrer">${escapeHtml(link.label)}</a>`)
        .join("")
    : '<span class="muted">No links</span>';

  return `
    <article class="app-tile" data-app-id="${app.id}">
      <a class="app-tile-link" href="/apps/${app.id}">
        <div class="app-icon-shell">
          <div class="app-icon app-icon-dashboard" style="--app-color: ${app.color};">
            <span>${escapeHtml(app.icon)}</span>
          </div>
          <span class="app-health-dot health-${escapeHtml(app.runtime.health)}" title="${escapeHtml(app.runtime.health)}"></span>
          <span class="app-settings-chip">Settings</span>
        </div>
        <div class="app-labels">
          <h3>${escapeHtml(app.name)}</h3>
          <p>${escapeHtml(app.runtime.health)}</p>
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
  const refreshStatusButton = document.getElementById("refresh-status");
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

  if (refreshStatusButton) {
    refreshStatusButton.addEventListener("click", async () => {
      actionMessage.textContent = "Refreshing status...";
      try {
        const result = await sendJson(`/api/apps/${appId}/status`, { method: "GET" });
        renderServiceList(result.runtime);
        actionMessage.textContent = "Status refreshed.";
        window.setTimeout(() => window.location.reload(), 300);
      } catch {
        actionMessage.textContent = "Could not refresh status.";
      }
    });
  }

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
wireDashboard();
wireDetail();
