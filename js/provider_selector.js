import { app } from "/scripts/app.js";

app.registerExtension({
    name: "Shrug.ProviderSelector",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === "ShrugProviderSelector") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;

            nodeType.prototype.onNodeCreated = function () {
                onNodeCreated?.apply(this, arguments);

                // A helper to find a widget on the node by its name.
                const findWidget = (name) =>
                    this.widgets.find((w) => w.name === name);

                const initializeWidgets = () => {
                    const modelWidget = findWidget("model");
                    if (modelWidget && modelWidget.type === "STRING") {
                        const originalValue = modelWidget.value;
                        const modelWidgetIndex =
                            this.widgets.indexOf(modelWidget);

                        this.widgets.splice(modelWidgetIndex, 1);

                        const comboWidget = this.addWidget(
                            "COMBO",
                            "model",
                            originalValue,
                            () => {},
                            {
                                values: [originalValue],
                            },
                        );

                        const newIndex = this.widgets.indexOf(comboWidget);
                        if (newIndex !== modelWidgetIndex) {
                            const widget = this.widgets.splice(newIndex, 1)[0];
                            this.widgets.splice(modelWidgetIndex, 0, widget);
                        }
                        this.llmModelWidget = comboWidget; // Store a direct reference.
                    }
                };

                /**
                 * Fetches the model list from the backend API and updates the dropdown.
                 */
                const fetchAndPopulateModels = async () => {
                    if (!this.llmModelWidget) return;

                    this.llmModelWidget.options.values = ["Fetching..."];
                    this.llmModelWidget.value = "Fetching...";

                    try {
                        const provider = findWidget("provider").value;
                        const baseUrl = findWidget("base_url").value;
                        const apiKey = findWidget("api_key").value;

                        const url = new URL(
                            "/shrug/get_models",
                            window.location.origin,
                        );
                        url.searchParams.append("provider", provider);
                        url.searchParams.append("base_url", baseUrl);
                        url.searchParams.append("api_key", apiKey);

                        const response = await fetch(url);
                        if (!response.ok)
                            throw new Error(`HTTP ${response.status}`);

                        const models = await response.json();
                        if (Array.isArray(models) && models.length) {
                            this.llmModelWidget.options.values = models;
                            // Set to the first valid model, or retain current if it's still in the list.
                            this.llmModelWidget.value = models.includes(
                                this.llmModelWidget.value,
                            )
                                ? this.llmModelWidget.value
                                : models[0];
                        } else {
                            throw new Error(
                                "Received empty or invalid model list.",
                            );
                        }
                    } catch (error) {
                        console.error(
                            "ShrugPrompter: Could not fetch models.",
                            error,
                        );
                        this.llmModelWidget.options.values = [
                            "Error fetching models",
                        ];
                        this.llmModelWidget.value = "Error fetching models";
                    }
                };

                /**
                 * Binds the fetch function to the callbacks of widgets that should trigger an update.
                 */
                const bindEvents = () => {
                    const triggerWidgets = ["provider", "base_url", "api_key"];
                    triggerWidgets.forEach((widgetName) => {
                        const widget = findWidget(widgetName);
                        if (widget) {
                            widget.callback = fetchAndPopulateModels;
                        }
                    });
                };

                // --- Main execution flow for the node ---
                initializeWidgets.call(this);
                bindEvents.call(this);

                // Initial fetch after the node is fully set up.
                setTimeout(fetchAndPopulateModels, 100);
            };
        }
    },
});
