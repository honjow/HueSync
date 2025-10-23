// MSI Custom RGB Control Component
// MSI 自定义 RGB 控制组件

import { FC, useState, useEffect } from "react";
import { PanelSectionRow, DropdownItem, DropdownOption, showModal } from "@decky/ui";
import { useMsiCustomRgb, MsiCustomRgbSetting } from "../hooks";
import { MsiCustomRgbEditor } from "./MsiCustomRgbEditor";

export const MsiCustomRgbControl: FC = () => {
  const { presets, startEditing, deletePreset, applyPreset } = useMsiCustomRgb();
  const [selectedAction, setSelectedAction] = useState<string>("");
  const [dropdownOptions, setDropdownOptions] = useState<DropdownOption[]>([]);

  useEffect(() => {
    // Load presets on mount
    MsiCustomRgbSetting.init();
  }, []);

  useEffect(() => {
    // Build dropdown options from presets
    const options: DropdownOption[] = [];

    // Add "Create New" option
    options.push({
      label: "+ 新建自定义灯效 / + Create Custom Effect",
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
          label: `  ✏ 编辑 / Edit`,
          data: `edit:${name}`,
        });
        // Delete option
        options.push({
          label: `  🗑 删除 / Delete`,
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
      alert(`应用失败 / Failed to apply: ${name}`);
    }
  };

  const handleEdit = (name: string) => {
    startEditing(name);
    openEditorModal();
  };

  const handleDelete = async (name: string) => {
    if (confirm(`确认删除预设 "${name}"？\nDelete preset "${name}"?`)) {
      const success = await deletePreset(name);
      if (!success) {
        alert(`删除失败 / Failed to delete: ${name}`);
      }
    }
  };

  const openEditorModal = () => {
    showModal(<MsiCustomRgbEditor closeModal={() => {}} />);
  };

  return (
    <PanelSectionRow>
      <DropdownItem
        label="自定义灯效 / Custom Effects"
        description="创建和管理自定义 RGB 灯效 / Create and manage custom RGB effects"
        rgOptions={dropdownOptions}
        selectedOption={dropdownOptions.find((opt) => opt.data === selectedAction) || dropdownOptions[0]}
        onChange={handleActionSelect}
        strDefaultLabel="选择操作... / Select action..."
      />
    </PanelSectionRow>
  );
};

