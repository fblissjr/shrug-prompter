import { app } from "/scripts/app.js";

// Provider configurations
const PROVIDER_CONFIG = {
  openai: {
    name: "OpenAI/MLX/LlamaCpp",
    defaultBaseUrl: "http://localhost:8080",
    requiresApiKey: false,
    supportsBatch: true,
    supportsVision: true,
    timeout: 15000,
  },
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
  
  // Add settings for shrug-prompter
  settings: [
    {
      id: "shrug.show_processing_toast",
      name: "Show VLM Processing Notifications",
      type: "boolean",
      defaultValue: true,
    },
    {
      id: "shrug.auto_refresh_models",
      name: "Auto-refresh Models on Provider Change",
      type: "boolean",
      defaultValue: true,
    },
    {
      id: "shrug.model_cache_duration",
      name: "Model Cache Duration (minutes)",
      type: "number",
      defaultValue: 5,
      min: 1,
      max: 60,
    }
  ],

  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name === "VLMProviderConfig") {
      const onNodeCreated = nodeType.prototype.onNodeCreated;

      nodeType.prototype.onNodeCreated = function () {
        onNodeCreated?.apply(this, arguments);

        // Enhanced state management
        const state = {
          isLoading: false,
          lastRequestId: 0,
          modelCache: new Map(),
          cacheTimeout: app.extensionManager.setting.get("shrug.model_cache_duration") * 60 * 1000,
          debounceTimer: null,
          retryDelays: [1000, 2000, 4000],
          lastSelectedModel: null,
        };

        // Core helper functions
        const findWidget = (name) => this.widgets.find((w) => w.name === name);
        const createCacheKey = (provider, baseUrl) => `${provider}:${baseUrl}`;
        const isCacheValid = (entry) => entry && Date.now() - entry.timestamp < state.cacheTimeout;

        /**
         * Initialize and enhance the model widget
         */
        const initializeWidgets = () => {
          const modelWidget = findWidget("llm_model");
          if (modelWidget && modelWidget.type === "STRING") {
            const originalValue = modelWidget.value;
            const modelWidgetIndex = this.widgets.indexOf(modelWidget);

            // Replace STRING with COMBO widget
            this.widgets.splice(modelWidgetIndex, 1);
            const comboWidget = this.addWidget(
              "COMBO",
              "llm_model",
              originalValue || "Select provider to load models",
              (value) => {
                // CRITICAL: Update the actual node value when selection changes
                this.properties = this.properties || {};
                this.properties.llm_model = value;
                state.lastSelectedModel = value;
                
                // Trigger graph serialization to save the value
                if (app.graph) {
                  app.graph.setDirtyCanvas(true);
                }
                
                console.log(`Shrug: Model selected and saved: ${value}`);
              },
              { values: [originalValue || "Select provider to load models"] }
            );

            // Maintain widget order
            const newIndex = this.widgets.indexOf(comboWidget);
            if (newIndex !== modelWidgetIndex) {
              const widget = this.widgets.splice(newIndex, 1)[0];
              this.widgets.splice(modelWidgetIndex, 0, widget);
            }

            this.llmModelWidget = comboWidget;
            
            // Restore last selected model if available
            if (this.properties?.llm_model) {
              comboWidget.value = this.properties.llm_model;
              state.lastSelectedModel = this.properties.llm_model;
            }
            
            console.log("Shrug: Model selector initialized with persistence");
          }
        };

        /**
         * Show toast notifications for processing status
         */
        const showToast = (severity, summary, detail, life = 3000) => {
          if (app.extensionManager.setting.get("shrug.show_processing_toast")) {
            app.extensionManager.toast.add({ severity, summary, detail, life });
          }
        };

        /**
         * Enhanced model fetching with better UI feedback
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
            this._updateModelWidget(["Configure provider and URL first"], "Configure provider and URL first");
            state.isLoading = false;
            return;
          }

          // Check cache first
          const cacheKey = createCacheKey(provider, baseUrl);
          const cachedEntry = state.modelCache.get(cacheKey);
          if (isCacheValid(cachedEntry)) {
            console.log("Shrug: Using cached models");
            this._updateModelWidget(cachedEntry.models, state.lastSelectedModel);
            state.isLoading = false;
            showToast("info", "Models Loaded", `Using cached models for ${provider}`, 2000);
            return;
          }

          // Show loading state
          const loadingText = retryCount > 0 ? `Retrying... (${retryCount + 1})` : "Loading models...";
          this._updateModelWidget([loadingText], loadingText);
          
          if (retryCount === 0) {
            showToast("info", "Loading Models", `Fetching models from ${provider}...`);
          }

          try {
            console.log(`Shrug: Fetching models for ${provider} at ${baseUrl}`);

            const providerConfig = PROVIDER_CONFIG[provider] || PROVIDER_CONFIG.openai;
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), providerConfig.timeout);

            const url = new URL("/shrug/get_models", window.location.origin);
            url.searchParams.append("provider", provider);
            url.searchParams.append("base_url", baseUrl);
            url.searchParams.append("api_key", apiKey || "");

            const response = await fetch(url, {
              signal: controller.signal,
              headers: { Accept: "application/json" },
            });

            clearTimeout(timeoutId);

            if (requestId !== state.lastRequestId) {
              console.log("Shrug: Request superseded, ignoring");
              return;
            }

            if (!response.ok) {
              throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            const models = this._extractModels(data);

            if (models.length === 0) {
              throw new Error("No models available");
            }

            // Process and sort models
            const sortedModels = this._sortModels(models);

            // Cache the results
            state.modelCache.set(cacheKey, {
              models: sortedModels,
              timestamp: Date.now(),
            });

            // Update UI and restore selection
            this._updateModelWidget(sortedModels, state.lastSelectedModel);
            
            // Show success toast
            const visionCount = sortedModels.filter(m => m.includes("(Vision)")).length;
            const detail = visionCount > 0 
              ? `Found ${sortedModels.length} models (${visionCount} with vision)`
              : `Found ${sortedModels.length} models`;
            showToast("success", "Models Loaded", detail);
            
          } catch (error) {
            console.error("Shrug: Model fetch error:", error);

            if (requestId !== state.lastRequestId) return;

            const { shouldRetry, errorMessage } = this._handleFetchError(error, retryCount);
            this._updateModelWidget([errorMessage], errorMessage);
            
            // Show error toast
            showToast("error", "Model Loading Failed", errorMessage, 5000);

            // Enable manual entry after failures
            if (retryCount >= state.retryDelays.length) {
              console.log("Shrug: Enabling manual model entry after fetch failure");
              this._enableManualEntry();
            }

            // Retry logic
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
         * Update model widget and handle persistence
         */
        this._updateModelWidget = (models, selectedValue = null) => {
          if (!this.llmModelWidget) return;

          this.llmModelWidget.options.values = models;

          if (selectedValue && models.includes(selectedValue)) {
            // Restore previous selection if available
            this.llmModelWidget.value = selectedValue;
          } else {
            // Smart default selection
            const currentValue = this.llmModelWidget.value;
            if (models.includes(currentValue)) {
              this.llmModelWidget.value = currentValue;
            } else {
              // Prefer vision models
              const visionModels = models.filter((m) => m.includes("(Vision)"));
              const defaultModel = visionModels.length > 0 ? visionModels[0] : models[0];
              this.llmModelWidget.value = defaultModel;
              
              // Save the auto-selected model
              this.properties = this.properties || {};
              this.properties.llm_model = defaultModel;
              state.lastSelectedModel = defaultModel;
            }
          }
          
          // Ensure the value is saved
          if (this.llmModelWidget.callback) {
            this.llmModelWidget.callback(this.llmModelWidget.value);
          }
        };

        // ... (keep all other helper methods from original: _extractModels, _sortModels, _handleFetchError, etc.)
        this._extractModels = (data) => {
          if (Array.isArray(data)) return data;
          if (data.error) throw new Error(data.error);
          if (Array.isArray(data.models)) return data.models;
          throw new Error("Unexpected response format");
        };

        this._sortModels = (models) => {
          const validModels = models.filter(
            (model) =>
              typeof model === "string" &&
              !model.toLowerCase().includes("error") &&
              !model.toLowerCase().includes("timeout") &&
              model.trim().length > 0
          );

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
          } else if (error.message.includes("Failed to fetch") || error.message.includes("NetworkError")) {
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

        this._enableManualEntry = () => {
          if (!this.llmModelWidget) return;
          
          this.llmModelWidget.options.values = ["Enter model name manually"];
          this.llmModelWidget.value = state.lastSelectedModel || "Enter model name manually";
          
          // Make editable
          if (this.llmModelWidget.inputEl) {
            this.llmModelWidget.inputEl.readOnly = false;
            this.llmModelWidget.inputEl.placeholder = "Type your model name here";
            
            // Save manually entered values
            this.llmModelWidget.inputEl.addEventListener("change", (e) => {
              const value = e.target.value;
              this.properties = this.properties || {};
              this.properties.llm_model = value;
              state.lastSelectedModel = value;
              app.graph.setDirtyCanvas(true);
              console.log(`Shrug: Manual model entry saved: ${value}`);
            });
          }
        };

        /**
         * Bind events with auto-refresh support
         */
        const bindEvents = () => {
          const triggerWidgets = ["provider", "base_url", "api_key"];

          triggerWidgets.forEach((widgetName) => {
            const widget = findWidget(widgetName);
            if (widget) {
              const originalCallback = widget.callback;
              widget.callback = (...args) => {
                if (originalCallback) {
                  originalCallback.apply(widget, args);
                }

                if (widgetName === "provider") {
                  this._updateProviderDefaults();
                  if (app.extensionManager.setting.get("shrug.auto_refresh_models")) {
                    fetchAndPopulateModels();
                  }
                } else {
                  // Debounce for URL/API key changes
                  clearTimeout(state.debounceTimer);
                  state.debounceTimer = setTimeout(() => {
                    if (app.extensionManager.setting.get("shrug.auto_refresh_models")) {
                      fetchAndPopulateModels();
                    }
                  }, 500);
                }
              };
              console.log(`Shrug: Bound events to ${widgetName} widget`);
            }
          });
        };

        this._updateProviderDefaults = () => {
          const provider = findWidget("provider")?.value;
          const baseUrlWidget = findWidget("base_url");

          if (provider && baseUrlWidget && PROVIDER_CONFIG[provider]) {
            const config = PROVIDER_CONFIG[provider];
            if (!baseUrlWidget.value || baseUrlWidget.value.includes("localhost")) {
              baseUrlWidget.value = config.defaultBaseUrl;
            }
          }
        };

        // Override onSerialize to ensure model value is saved
        const originalSerialize = this.onSerialize;
        this.onSerialize = function(o) {
          if (originalSerialize) {
            originalSerialize.call(this, o);
          }
          // Ensure llm_model is saved
          if (this.llmModelWidget) {
            o.widgets_values = o.widgets_values || [];
            const modelIndex = this.widgets.indexOf(this.llmModelWidget);
            o.widgets_values[modelIndex] = this.llmModelWidget.value;
          }
        };

        // Main initialization
        try {
          initializeWidgets.call(this);
          bindEvents.call(this);

          // Initial fetch
          setTimeout(() => {
            fetchAndPopulateModels();
          }, 250);

          console.log("Shrug: Provider selector initialized with model persistence");
        } catch (error) {
          console.error("Shrug: Initialization error:", error);
          showToast("error", "Initialization Failed", error.message, 5000);
        }
      };
    }
  },
});