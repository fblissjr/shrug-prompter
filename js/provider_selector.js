import { app } from "/scripts/app.js";

// Data-driven configuration - easily extensible for new providers
const PROVIDER_CONFIG = {
  openai: {
    name: "OpenAI/MLX/LlamaCpp",
    defaultBaseUrl: "http://localhost:8080",
    requiresApiKey: false, // For local unified servers
    supportsBatch: true,
    supportsVision: true,
    timeout: 15000,
  },
  // Ready for future expansion
  ollama: {
    name: "Ollama",
    defaultBaseUrl: "http://localhost:11434",
    requiresApiKey: false,
    supportsBatch: false,
    supportsVision: true,
    timeout: 30000,
  },
};

app.registerExtension({
  name: "Shrug.ProviderSelector",

  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name === "ShrugProviderSelector") {
      const onNodeCreated = nodeType.prototype.onNodeCreated;

      nodeType.prototype.onNodeCreated = function () {
        onNodeCreated?.apply(this, arguments);

        // Efficient state management
        const state = {
          isLoading: false,
          lastRequestId: 0,
          modelCache: new Map(), // Cache per provider:baseUrl key
          cacheTimeout: 5 * 60 * 1000, // 5 minutes cache
          debounceTimer: null,
          retryDelays: [1000, 2000, 4000], // Progressive retry delays
        };

        // Core helper functions
        const findWidget = (name) => this.widgets.find((w) => w.name === name);
        const createCacheKey = (provider, baseUrl) => `${provider}:${baseUrl}`;
        const isCacheValid = (entry) =>
          entry && Date.now() - entry.timestamp < state.cacheTimeout;

        /**
         * Initialize widgets with enhanced functionality
         */
        const initializeWidgets = () => {
          // Initialize model dropdown widget
          const modelWidget = findWidget("llm_model");
          if (modelWidget && modelWidget.type === "STRING") {
            const originalValue = modelWidget.value;
            const modelWidgetIndex = this.widgets.indexOf(modelWidget);

            // Replace STRING with enhanced COMBO widget
            this.widgets.splice(modelWidgetIndex, 1);
            const comboWidget = this.addWidget(
              "COMBO",
              "llm_model",
              originalValue || "Select provider to load models",
              () => {},
              { values: [originalValue || "Select provider to load models"] },
            );

            // Maintain widget order for consistent UX
            const newIndex = this.widgets.indexOf(comboWidget);
            if (newIndex !== modelWidgetIndex) {
              const widget = this.widgets.splice(newIndex, 1)[0];
              this.widgets.splice(modelWidgetIndex, 0, widget);
            }

            this.llmModelWidget = comboWidget;
            console.log("Shrug: Enhanced model selector initialized");
          }
        };

        /**
         * Enhanced model fetching with caching and robust error handling
         */
        const fetchAndPopulateModels = async (retryCount = 0) => {
          if (!this.llmModelWidget || state.isLoading) return;

          const requestId = ++state.lastRequestId;
          state.isLoading = true;

          const provider = findWidget("provider")?.value;
          const baseUrl = findWidget("base_url")?.value;
          const apiKey = findWidget("api_key")?.value;

          // Validate required fields
          if (!provider || !baseUrl) {
            this._updateModelWidget(
              ["Configure provider and URL first"],
              "Configure provider and URL first",
            );
            state.isLoading = false;
            return;
          }

          // Check cache first
          const cacheKey = createCacheKey(provider, baseUrl);
          const cachedEntry = state.modelCache.get(cacheKey);
          if (isCacheValid(cachedEntry)) {
            console.log("Shrug: Using cached models");
            this._updateModelWidget(cachedEntry.models, cachedEntry.models[0]);
            state.isLoading = false;
            return;
          }

          // Update UI with loading state
          const loadingText =
            retryCount > 0
              ? `Retrying... (${retryCount + 1})`
              : "Loading models...";
          this._updateModelWidget([loadingText], loadingText);

          try {
            console.log(`Shrug: Fetching models for ${provider} at ${baseUrl}`);

            // Build request with timeout based on provider
            const providerConfig =
              PROVIDER_CONFIG[provider] || PROVIDER_CONFIG.openai;
            const controller = new AbortController();
            const timeoutId = setTimeout(
              () => controller.abort(),
              providerConfig.timeout,
            );

            const url = new URL("/shrug/get_models", window.location.origin);
            url.searchParams.append("provider", provider);
            url.searchParams.append("base_url", baseUrl);
            url.searchParams.append("api_key", apiKey || "");

            const response = await fetch(url, {
              signal: controller.signal,
              headers: { Accept: "application/json" },
            });

            clearTimeout(timeoutId);

            // Check if request is still current
            if (requestId !== state.lastRequestId) {
              console.log("Shrug: Request superseded, ignoring");
              return;
            }

            if (!response.ok) {
              throw new Error(
                `HTTP ${response.status}: ${response.statusText}`,
              );
            }

            const data = await response.json();
            const models = this._extractModels(data);

            if (models.length === 0) {
              throw new Error("No models available");
            }

            // Process and sort models (vision models first, then alphabetically)
            const sortedModels = this._sortModels(models);

            // Cache the results
            state.modelCache.set(cacheKey, {
              models: sortedModels,
              timestamp: Date.now(),
            });

            // Update UI
            this._updateModelWidget(sortedModels);
            this._logSuccess(sortedModels);
          } catch (error) {
            console.error("Shrug: Model fetch error:", error);

            // Check if request is still current
            if (requestId !== state.lastRequestId) return;

            // Handle errors with smart retry logic
            const { shouldRetry, errorMessage } = this._handleFetchError(
              error,
              retryCount,
            );

            this._updateModelWidget([errorMessage], errorMessage);

            // For manual entry, revert to STRING widget after error
            if (retryCount >= state.retryDelays.length) {
              console.log(
                "Shrug: Enabling manual model entry after fetch failure",
              );
              this._enableManualEntry();
            }

            // Implement smart retry logic
            if (shouldRetry && retryCount < state.retryDelays.length) {
              const delay = state.retryDelays[retryCount];
              console.log(`Shrug: Retrying in ${delay}ms...`);
              setTimeout(() => {
                if (requestId === state.lastRequestId) {
                  fetchAndPopulateModels(retryCount + 1);
                }
              }, delay);
            }
          } finally {
            if (requestId === state.lastRequestId) {
              state.isLoading = false;
            }
          }
        };

        /**
         * Helper methods for better code organization
         */
        this._updateModelWidget = (models, selectedValue = null) => {
          if (!this.llmModelWidget) return;

          this.llmModelWidget.options.values = models;

          if (selectedValue) {
            this.llmModelWidget.value = selectedValue;
          } else {
            // Smart default selection
            const currentValue = this.llmModelWidget.value;
            if (models.includes(currentValue)) {
              // Keep current if still valid
              this.llmModelWidget.value = currentValue;
            } else {
              // Select first model, prefer vision models
              const visionModels = models.filter((m) => m.includes("(Vision)"));
              this.llmModelWidget.value =
                visionModels.length > 0 ? visionModels[0] : models[0];
            }
          }
        };

        this._extractModels = (data) => {
          if (Array.isArray(data)) return data;
          if (data.error) throw new Error(data.error);
          if (Array.isArray(data.models)) return data.models;
          throw new Error("Unexpected response format");
        };

        this._sortModels = (models) => {
          // Filter and validate models
          const validModels = models.filter(
            (model) =>
              typeof model === "string" &&
              !model.toLowerCase().includes("error") &&
              !model.toLowerCase().includes("timeout") &&
              model.trim().length > 0,
          );

          // Sort: vision models first, then alphabetically
          return validModels.sort((a, b) => {
            const aIsVision = a.includes("(Vision)");
            const bIsVision = b.includes("(Vision)");

            if (aIsVision && !bIsVision) return -1;
            if (!aIsVision && bIsVision) return 1;
            return a.toLowerCase().localeCompare(b.toLowerCase());
          });
        };

        this._handleFetchError = (error, retryCount) => {
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

          return { shouldRetry, errorMessage };
        };

        this._logSuccess = (models) => {
          const visionCount = models.filter((m) =>
            m.includes("(Vision)"),
          ).length;
          const statusMsg =
            visionCount > 0
              ? `✓ Loaded ${models.length} models (${visionCount} with vision)`
              : `✓ Loaded ${models.length} models`;
          console.log(`Shrug: ${statusMsg}`);
        };

        this._enableManualEntry = () => {
          if (!this.llmModelWidget) return;

          // Update widget to indicate manual entry is available
          this.llmModelWidget.options.values = ["Enter model name manually"];
          this.llmModelWidget.value = "Enter model name manually";

          // Make the combo widget editable
          if (this.llmModelWidget.inputEl) {
            this.llmModelWidget.inputEl.readOnly = false;
            this.llmModelWidget.inputEl.placeholder =
              "Type your model name here";
          }

          console.log("Shrug: Manual model entry enabled");
        };

        /**
         * Debounced fetch with smart timing
         */
        const debouncedFetch = (immediate = false) => {
          clearTimeout(state.debounceTimer);
          const delay = immediate ? 100 : 500; // Shorter delay for immediate requests
          state.debounceTimer = setTimeout(() => {
            fetchAndPopulateModels();
          }, delay);
        };

        /**
         * Bind events to trigger model fetching
         */
        const bindEvents = () => {
          const triggerWidgets = ["provider", "base_url", "api_key"];

          triggerWidgets.forEach((widgetName) => {
            const widget = findWidget(widgetName);
            if (widget) {
              const originalCallback = widget.callback;
              widget.callback = (...args) => {
                // Call original callback
                if (originalCallback) {
                  originalCallback.apply(widget, args);
                }

                // Smart defaults for provider changes
                if (widgetName === "provider") {
                  this._updateProviderDefaults();
                  debouncedFetch(true); // Immediate for provider changes
                } else {
                  debouncedFetch();
                }
              };
              console.log(`Shrug: Bound events to ${widgetName} widget`);
            }
          });
        };

        /**
         * Update defaults based on selected provider
         */
        this._updateProviderDefaults = () => {
          const provider = findWidget("provider")?.value;
          const baseUrlWidget = findWidget("base_url");

          if (provider && baseUrlWidget && PROVIDER_CONFIG[provider]) {
            const config = PROVIDER_CONFIG[provider];
            // Only update if empty or still using localhost default
            if (
              !baseUrlWidget.value ||
              baseUrlWidget.value.includes("localhost")
            ) {
              baseUrlWidget.value = config.defaultBaseUrl;
            }
          }
        };

        // --- Main initialization sequence ---
        try {
          initializeWidgets.call(this);
          bindEvents.call(this);

          // Initial fetch with slight delay for widget initialization
          setTimeout(() => {
            fetchAndPopulateModels();
          }, 250);

          console.log(
            "Shrug: Enhanced provider selector initialized successfully",
          );
        } catch (error) {
          console.error("Shrug: Initialization error:", error);
          // Graceful degradation - at least show the basic widget
          if (this.llmModelWidget) {
            this._updateModelWidget(
              ["Initialization failed"],
              "Initialization failed",
            );
          }
        }
      };
    }
  },
});
