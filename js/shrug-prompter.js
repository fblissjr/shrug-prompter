import { app } from "/scripts/app.js";

app.registerExtension({
  name: "Shrug.PrompterUI",
  async beforeRegisterNodeDef(nodeType, nodeData, app) {
    if (nodeData.name === "ShrugPrompter") {
      const onNodeCreated = nodeType.prototype.onNodeCreated;
      nodeType.prototype.onNodeCreated = function () {
        onNodeCreated?.apply(this, arguments);

        const node = this;
        const modeWidget = node.widgets.find((w) => w.name === "mode");
        const promptWidget = node.widgets.find((w) => w.name === "user_prompt");

        // Store original properties
        promptWidget.originalType = promptWidget.type;
        promptWidget.originalComputeSize = promptWidget.computeSize;

        // This will hold our dynamic prompt widgets in batch mode
        node.batchWidgets = [];

        function updateUi(mode) {
          if (mode === "Batch") {
            // --- BATCH MODE UI ---
            promptWidget.type = "hidden"; // Hide the original prompt widget

            // Remove existing dynamic widgets if any
            node.batchWidgets.forEach((w) => node.removeWidget(w.id));
            node.batchWidgets = [];

            // Add an "Add Prompt" button
            const addButton = node.addWidget(
              "button",
              "Add Prompt",
              "Add Prompt",
              () => {
                addPromptEntry();
              },
            );
            node.batchWidgets.push(addButton);

            // Function to add a new prompt text area
            const addPromptEntry = (text = "") => {
              const newWidget = node.addWidget(
                "string",
                `prompt_${node.batchWidgets.length}`,
                text,
                { multiline: true },
              );
              newWidget.removeButton = node.addWidget(
                "button",
                `❌`,
                `❌`,
                () => {
                  removePromptEntry(newWidget);
                },
              );
              node.batchWidgets.push(newWidget, newWidget.removeButton);
              serializePrompts();
              node.setDirtyCanvas(true, true);
            };

            // Function to remove a prompt text area
            const removePromptEntry = (widgetToRemove) => {
              // Find and remove the widget and its remove button
              const index = node.batchWidgets.indexOf(widgetToRemove);
              if (index > -1) {
                const buttonToRemove = node.batchWidgets[index + 1];
                node.removeWidget(node.widgets.indexOf(widgetToRemove));
                node.removeWidget(node.widgets.indexOf(buttonToRemove));
                node.batchWidgets.splice(index, 2);
                serializePrompts();
                node.setDirtyCanvas(true, true);
              }
            };

            // Add one prompt entry by default for batch mode
            addPromptEntry();
          } else {
            // --- SINGLE MODE UI ---
            // Restore the original prompt widget
            promptWidget.type = promptWidget.originalType;

            // Remove all dynamic batch widgets
            node.batchWidgets.forEach((w) =>
              node.removeWidget(node.widgets.indexOf(w)),
            );
            node.batchWidgets = [];
          }
          node.setDirtyCanvas(true, true);
        }

        // Function to gather all prompt texts and update the hidden promptWidget value
        function serializePrompts() {
          const prompts = node.widgets
            .filter((w) => w.name.startsWith("prompt_"))
            .map((w) => w.value);
          promptWidget.value = JSON.stringify(prompts);
        }

        // Listen for changes on our own dynamic widgets
        node.onPropertyChanged = function (property, value) {
          if (property.startsWith("prompt_")) {
            serializePrompts();
          }
        };

        // Hijack the mode widget's callback to update the UI
        const originalCallback = modeWidget.callback;
        modeWidget.callback = (value) => {
          updateUi(value);
          if (originalCallback) {
            originalCallback.call(node, value);
          }
        };

        // Initial UI setup
        updateUi(modeWidget.value);
      };
    }
  },
});
