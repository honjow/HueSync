// AyaNeo Custom RGB Control Component
// AyaNeo 自定义 RGB 控制组件

import { FC, useState, useEffect } from "react";
import { PanelSectionRow, DropdownItem, DropdownOption, showModal } from "@decky/ui";
import { useAyaNeoCustomRgb, AyaNeoCustomRgbSetting } from "../hooks";
import { MsiCustomRgbEditor } from "./MsiCustomRgbEditor";
import { localizationManager, localizeStrEnum } from "../i18n";

export const AyaNeoCustomRgbControl: FC = () => {
  const { presets, startEditing, deletePreset, applyPreset } = useAyaNeoCustomRgb();
  const [selectedAction, setSelectedAction] = useState<string>("");
  const [dropdownOptions, setDropdownOptions] = useState<DropdownOption[]>([]);

  useEffect(() => {
    // Load presets on mount
    AyaNeoCustomRgbSetting.init();
  }, []);

  useEffect(() => {
    // Build dropdown options from presets
    const options: DropdownOption[] = [];

    // Add "Create New" option
    options.push({
      label: localizationManager.getString(localizeStrEnum.AYANEO_CUSTOM_EDIT_EFFECT),
      data: "create_new",
    });

    // Add separator if there are presets
    if (Object.keys(presets).length > 0) {
      options.push({
        label: "────────────────",
        data: "separator",
      });

      // Add preset options with actions
      Object.keys(presets).forEach((name) => {
        // Apply option
        options.push({
          label: `▶ ${name}`,
          data: `apply:${name}`,
        });
        // Edit option
        options.push({
          label: `  ✏ ${localizationManager.getString(localizeStrEnum.MSI_CUSTOM_MANAGE_EDIT)}`,
          data: `edit:${name}`,
        });
        // Delete option
        options.push({
          label: `  🗑 ${localizationManager.getString(localizeStrEnum.MSI_CUSTOM_MANAGE_DELETE)}`,
          data: `delete:${name}`,
        });
      });
    }

    setDropdownOptions(options);
  }, [presets]);

  const handleActionSelect = (option: DropdownOption) => {
    const action = option.data as string;

    if (action === "separator") {
      // Ignore separator
      return;
    }

    if (action === "create_new") {
      // Open editor for new preset
      startEditing();
      openEditorModal();
      return;
    }

    // Parse action:name format
    const [actionType, presetName] = action.split(":");

    switch (actionType) {
      case "apply":
        handleApply(presetName);
        break;
      case "edit":
        handleEdit(presetName);
        break;
      case "delete":
        handleDelete(presetName);
        break;
    }

    // Reset selection
    setSelectedAction("");
  };

  const handleApply = async (name: string) => {
    const success = await applyPreset(name);
    if (!success) {
      alert(`${localizationManager.getString(localizeStrEnum.MSI_CUSTOM_MANAGE_APPLY_FAILED)}: ${name}`);
    }
  };

  const handleEdit = (name: string) => {
    startEditing(name);
    openEditorModal();
  };

  const handleDelete = async (name: string) => {
    const confirmMsg = localizationManager
      .getString(localizeStrEnum.MSI_CUSTOM_MANAGE_DELETE_CONFIRM)
      .replace("{name}", name);
    if (confirm(confirmMsg)) {
      const success = await deletePreset(name);
      if (!success) {
        alert(`${localizationManager.getString(localizeStrEnum.MSI_CUSTOM_MANAGE_DELETE_FAILED)}: ${name}`);
      }
    }
  };

  const openEditorModal = () => {
    showModal(<MsiCustomRgbEditor closeModal={() => {}} deviceType="ayaneo" />);
  };

  return (
    <PanelSectionRow>
      <DropdownItem
        label={localizationManager.getString(localizeStrEnum.AYANEO_CUSTOM_EDIT_EFFECT)}
        description={localizationManager.getString(localizeStrEnum.MSI_CUSTOM_MANAGE_DESCRIPTION)}
        rgOptions={dropdownOptions}
        selectedOption={dropdownOptions.find((opt) => opt.data === selectedAction) || dropdownOptions[0]}
        onChange={handleActionSelect}
        strDefaultLabel={localizationManager.getString(localizeStrEnum.MSI_CUSTOM_MANAGE_SELECT)}
      />
    </PanelSectionRow>
  );
};

