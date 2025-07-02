import { app } from "/scripts/app.js";

app.registerExtension({
    name: "Shrug.ProviderSelector",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === "ShrugProviderSelector") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;

            nodeType.prototype.onNodeCreated = function () {
                onNodeCreated?.apply(this, arguments);

                // Helper to find a widget on the node by its name
                const findWidget = (name) =>
                    this.widgets.find((w) => w.name === name);

                // State management for the model widget
                let isLoading = false;
                let lastRequestId = 0;

                const initializeWidgets = () => {
                    const modelWidget = findWidget("llm_model");
                    if (modelWidget && modelWidget.type === "STRING") {
                        const originalValue = modelWidget.value;
                        const modelWidgetIndex =
                            this.widgets.indexOf(modelWidget);

                        // Remove the original STRING widget
                        this.widgets.splice(modelWidgetIndex, 1);

                        // Create new COMBO widget with better defaults
                        const comboWidget = this.addWidget(
                            "COMBO",
                            "llm_model",
                            originalValue || "Select provider to load models",
                            () => {},
                            {
                                values: [
                                    originalValue ||
                                        "Select provider to load models",
                                ],
                            },
                        );

                        // Maintain widget order
                        const newIndex = this.widgets.indexOf(comboWidget);
                        if (newIndex !== modelWidgetIndex) {
                            const widget = this.widgets.splice(newIndex, 1)[0];
                            this.widgets.splice(modelWidgetIndex, 0, widget);
                        }

                        this.llmModelWidget = comboWidget;
                        console.log("Shrug: Initialized model dropdown widget");
                    }
                };

                /**
                 * Enhanced model fetching with better error handling and retry logic
                 */
                const fetchAndPopulateModels = async (retryCount = 0) => {
                    if (!this.llmModelWidget || isLoading) return;

                    // Generate request ID to handle concurrent requests
                    const requestId = ++lastRequestId;
                    isLoading = true;

                    // Get current widget values
                    const provider = findWidget("provider")?.value;
                    const baseUrl = findWidget("base_url")?.value;
                    const apiKey = findWidget("api_key")?.value;

                    // Validate required fields
                    if (!provider || !baseUrl) {
                        console.warn(
                            "Shrug: Missing provider or base_url, skipping model fetch",
                        );
                        this.llmModelWidget.options.values = [
                            "Configure provider and URL first",
                        ];
                        this.llmModelWidget.value =
                            "Configure provider and URL first";
                        isLoading = false;
                        return;
                    }

                    // Update UI to show loading state
                    const loadingText =
                        retryCount > 0
                            ? `Retrying... (${retryCount})`
                            : "Loading models...";
                    this.llmModelWidget.options.values = [loadingText];
                    this.llmModelWidget.value = loadingText;

                    try {
                        console.log(
                            `Shrug: Fetching models for ${provider} at ${baseUrl}`,
                        );

                        // Build request URL
                        const url = new URL(
                            "/shrug/get_models",
                            window.location.origin,
                        );
                        url.searchParams.append("provider", provider);
                        url.searchParams.append("base_url", baseUrl);
                        url.searchParams.append("api_key", apiKey || "");

                        // Make request with timeout
                        const controller = new AbortController();
                        const timeoutId = setTimeout(
                            () => controller.abort(),
                            15000,
                        ); // 15 second timeout

                        const response = await fetch(url, {
                            signal: controller.signal,
                            headers: {
                                Accept: "application/json",
                            },
                        });

                        clearTimeout(timeoutId);

                        // Check if this request is still current
                        if (requestId !== lastRequestId) {
                            console.log(
                                "Shrug: Request superseded, ignoring response",
                            );
                            return;
                        }

                        if (!response.ok) {
                            throw new Error(
                                `HTTP ${response.status}: ${response.statusText}`,
                            );
                        }

                        const data = await response.json();
                        console.log("Shrug: Received model data:", data);

                        // Handle different response formats
                        let models = [];
                        if (Array.isArray(data)) {
                            models = data;
                        } else if (data.error) {
                            throw new Error(data.error);
                        } else if (Array.isArray(data.models)) {
                            models = data.models;
                        } else {
                            throw new Error("Unexpected response format");
                        }

                        // Validate and process models
                        if (models.length === 0) {
                            throw new Error("No models available");
                        }

                        // Filter out error messages
                        const validModels = models.filter(
                            (model) =>
                                typeof model === "string" &&
                                !model.toLowerCase().includes("error") &&
                                !model.toLowerCase().includes("timeout") &&
                                model.trim().length > 0,
                        );

                        if (validModels.length === 0) {
                            throw new Error("No valid models found");
                        }

                        // Sort models: vision models first, then alphabetically
                        validModels.sort((a, b) => {
                            const aIsVision = a.includes("(Vision)");
                            const bIsVision = b.includes("(Vision)");

                            if (aIsVision && !bIsVision) return -1;
                            if (!aIsVision && bIsVision) return 1;
                            return a
                                .toLowerCase()
                                .localeCompare(b.toLowerCase());
                        });

                        // Update dropdown with models
                        this.llmModelWidget.options.values = validModels;

                        // Set default selection
                        const currentValue = this.llmModelWidget.value;
                        if (validModels.includes(currentValue)) {
                            // Keep current selection if it's still valid
                            this.llmModelWidget.value = currentValue;
                        } else {
                            // Select first model as default
                            this.llmModelWidget.value = validModels[0];
                        }

                        console.log(
                            `Shrug: Successfully loaded ${validModels.length} model(s)`,
                        );

                        // Show success indicator briefly
                        if (app.ui && app.ui.dialog) {
                            const visionCount = validModels.filter((m) =>
                                m.includes("(Vision)"),
                            ).length;
                            const statusMsg =
                                visionCount > 0
                                    ? `✓ Loaded ${validModels.length} models (${visionCount} with vision)`
                                    : `✓ Loaded ${validModels.length} models`;

                            // Could add a toast notification here if ComfyUI supports it
                            console.log(`Shrug: ${statusMsg}`);
                        }
                    } catch (error) {
                        console.error("Shrug: Model fetch error:", error);

                        // Check if this request is still current
                        if (requestId !== lastRequestId) {
                            return;
                        }

                        // Handle specific error types
                        let errorMessage = "Error loading models";
                        let shouldRetry = false;

                        if (error.name === "AbortError") {
                            errorMessage = "Request timed out";
                            shouldRetry = retryCount < 2;
                        } else if (
                            error.message.includes("Failed to fetch") ||
                            error.message.includes("NetworkError")
                        ) {
                            errorMessage = "Network error - check server";
                            shouldRetry = retryCount < 1;
                        } else if (error.message.includes("HTTP")) {
                            errorMessage = `Server error: ${error.message}`;
                            shouldRetry = false;
                        } else {
                            errorMessage = error.message || "Unknown error";
                            shouldRetry = retryCount < 1;
                        }

                        // Update UI with error
                        this.llmModelWidget.options.values = [errorMessage];
                        this.llmModelWidget.value = errorMessage;

                        // Retry logic for transient errors
                        if (shouldRetry && retryCount < 3) {
                            console.log(
                                `Shrug: Retrying model fetch in ${(retryCount + 1) * 2} seconds...`,
                            );
                            setTimeout(
                                () => {
                                    if (requestId === lastRequestId) {
                                        // Only retry if still current
                                        fetchAndPopulateModels(retryCount + 1);
                                    }
                                },
                                (retryCount + 1) * 2000,
                            );
                        } else {
                            console.error(
                                "Shrug: Max retries reached or non-retryable error",
                            );
                        }
                    } finally {
                        // Only clear loading state if this is still the current request
                        if (requestId === lastRequestId) {
                            isLoading = false;
                        }
                    }
                };

                /**
                 * Debounced wrapper for fetchAndPopulateModels
                 */
                let debounceTimer = null;
                const debouncedFetch = () => {
                    clearTimeout(debounceTimer);
                    debounceTimer = setTimeout(() => {
                        fetchAndPopulateModels();
                    }, 500); // 500ms debounce
                };

                /**
                 * Binds the fetch function to widget callbacks
                 */
                const bindEvents = () => {
                    const triggerWidgets = ["provider", "base_url", "api_key"];
                    triggerWidgets.forEach((widgetName) => {
                        const widget = findWidget(widgetName);
                        if (widget) {
                            const originalCallback = widget.callback;
                            widget.callback = (...args) => {
                                // Call original callback if it exists
                                if (originalCallback) {
                                    originalCallback.apply(widget, args);
                                }
                                // Trigger model fetch
                                debouncedFetch();
                            };
                            console.log(
                                `Shrug: Bound fetch to ${widgetName} widget`,
                            );
                        }
                    });
                };

                // --- Main execution flow for the node ---
                try {
                    initializeWidgets.call(this);
                    bindEvents.call(this);

                    // Initial fetch after a short delay to ensure all widgets are initialized
                    setTimeout(() => {
                        fetchAndPopulateModels();
                    }, 250);

                    console.log(
                        "Shrug: Provider selector node initialized successfully",
                    );
                } catch (error) {
                    console.error(
                        "Shrug: Error initializing provider selector:",
                        error,
                    );
                }
            };
        }
    },
});
