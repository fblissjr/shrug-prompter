// Converts the ShrugConnection node's "model" widget from a plain STRING
// into a combo dropdown populated by /shrug/get_models. Single-user, LAN,
// no retries. If the fetch fails, the widget falls back to free text entry
// and the error is surfaced in the widget value.

import { app } from "/scripts/app.js";

const NODE_ID = "ShrugConnection";
const ROUTE = "/shrug/get_models";

const DEBOUNCE_MS = 400;

async function fetchModels(baseUrl, apiKey) {
    const url = `${ROUTE}?base_url=${encodeURIComponent(baseUrl)}&api_key=${encodeURIComponent(apiKey || "")}`;
    const resp = await fetch(url);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    if (!data.success) throw new Error(data.error || "unknown error");
    return data.models || [];
}

function findWidget(node, name) {
    return node.widgets?.find((w) => w.name === name);
}

function replaceWithCombo(node, modelWidget, options) {
    const current = modelWidget.value;
    const idx = node.widgets.indexOf(modelWidget);
    const newWidget = node.addWidget(
        "combo",
        "model",
        options.includes(current) ? current : options[0] || "",
        () => { node.setDirtyCanvas(true); },
        { values: options },
    );
    node.widgets[idx] = newWidget;
    node.widgets.pop();
    node.setDirtyCanvas(true, true);
    return newWidget;
}

async function refreshModels(node) {
    const baseUrlW = findWidget(node, "base_url");
    const apiKeyW = findWidget(node, "api_key");
    const modelW = findWidget(node, "model");
    if (!baseUrlW || !modelW) return;
    try {
        const models = await fetchModels(baseUrlW.value, apiKeyW?.value);
        const options = models.map((m) => m.id);
        if (options.length === 0) {
            modelW.value = modelW.value || "(no models)";
            return;
        }
        if (modelW.type === "combo") {
            modelW.options.values = options;
            if (!options.includes(modelW.value)) modelW.value = options[0];
        } else {
            replaceWithCombo(node, modelW, options);
        }
    } catch (err) {
        console.warn(`[shrug] failed to fetch models: ${err.message}`);
        if (modelW.type !== "combo") {
            modelW.value = modelW.value || "";
        }
    }
}

app.registerExtension({
    name: "shrug.provider",
    async nodeCreated(node) {
        if (node.comfyClass !== NODE_ID) return;
        setTimeout(() => refreshModels(node), 0);

        let debounceTimer = null;
        const scheduleRefresh = () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => refreshModels(node), DEBOUNCE_MS);
        };

        for (const name of ["base_url", "api_key"]) {
            const w = findWidget(node, name);
            if (!w) continue;
            const origCallback = w.callback;
            w.callback = function (...args) {
                if (origCallback) origCallback.apply(this, args);
                scheduleRefresh();
            };
        }
    },
});
