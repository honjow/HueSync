import { Field, PanelSection, PanelSectionRow } from "@decky/ui";
import { VFC, useEffect, useState } from "react";
import { localizationManager, localizeStrEnum } from "../i18n";
import { Backend } from "../util";
import { ActionButtonItem } from ".";

export const MoreComponent: VFC = () => {
    const [currentVersion, _] = useState<string>(Backend.data.getCurrentVersion());
    const [latestVersion, setLatestVersion] = useState<string>(Backend.data.getLatestVersion());

    useEffect(() => {
        const getData = async () => {
            const latestVersion = await Backend.getLatestVersion();
            setLatestVersion(latestVersion);
            Backend.data.setLatestVersion(latestVersion);
        };
        getData();
    });

    let uptButtonText = localizationManager.getString(localizeStrEnum.REINSTALL_PLUGIN);

    if (currentVersion !== latestVersion && Boolean(latestVersion)) {
        uptButtonText = `${localizationManager.getString(localizeStrEnum.UPDATE_PLUGIN)} ${latestVersion}`;
    }

    return (
        <PanelSection title={localizationManager.getString(localizeStrEnum.VERSION)}>
            <PanelSectionRow>
                <ActionButtonItem
                    layout="below"
                    onClick={async () => {
                        await Backend.updateLatest();
                    }}
                >{uptButtonText}</ActionButtonItem>
            </PanelSectionRow>
            <PanelSectionRow>
                <Field disabled label={localizationManager.getString(localizeStrEnum.INSTALLED_VERSION)}>
                    {currentVersion}
                </Field>
            </PanelSectionRow>
            {Boolean(latestVersion) && (
                <PanelSectionRow>
                    <Field disabled label={localizationManager.getString(localizeStrEnum.LATEST_VERSION)}>
                        {latestVersion}
                    </Field>
                </PanelSectionRow>
            )}
        </PanelSection>
    )
}