import { ButtonItem, Field, PanelSection, PanelSectionRow } from "@decky/ui";
import { FC, useEffect, useState } from "react";
import { localizationManager, localizeStrEnum } from "../i18n";
import { Backend, compareVersions } from "../util";
import { ActionButtonItem } from ".";

interface VersionCache {
    latestVersion: string;
    lastCheckTime: number;
    cacheExpiry: number;
}

const CACHE_KEY = 'huesync_version_cache';
const CACHE_DURATION = 6 * 60 * 60 * 1000; // 6小时

const getVersionCache = (): VersionCache | null => {
    const cached = localStorage.getItem(CACHE_KEY);
    if (!cached) return null;

    const cache = JSON.parse(cached);
    if (Date.now() > cache.cacheExpiry) {
        localStorage.removeItem(CACHE_KEY);
        return null;
    }

    return cache;
};

const setVersionCache = (latest: string) => {
    const cache: VersionCache = {
        latestVersion: latest,
        lastCheckTime: Date.now(),
        cacheExpiry: Date.now() + CACHE_DURATION
    };
    localStorage.setItem(CACHE_KEY, JSON.stringify(cache));
};

const getLastCheckText = (lastCheckTime: number): string => {
    const now = Date.now();
    const diff = now - lastCheckTime;

    if (diff < 60 * 1000) {
        return localizationManager.getString(localizeStrEnum.JUST_NOW) || "just now";
    }

    if (diff < 60 * 60 * 1000) {
        const minutes = Math.floor(diff / 60000);
        return localizationManager.getString(localizeStrEnum.MINUTES_AGO)?.replace('{{minutes}}', minutes.toString())
            || `${minutes} minutes ago`;
    }

    if (diff < 24 * 60 * 60 * 1000) {
        const hours = Math.floor(diff / 3600000);
        return localizationManager.getString(localizeStrEnum.HOURS_AGO)?.replace('{{hours}}', hours.toString())
            || `${hours} hours ago`;
    }

    const days = Math.floor(diff / 86400000);
    return localizationManager.getString(localizeStrEnum.DAYS_AGO)?.replace('{{days}}', days.toString())
        || `${days} days ago`;
};

export const MoreComponent: FC = () => {
    const [currentVersion, setCurrentVersion] = useState<string>(
        Backend.data?.getCurrentVersion() || ""
    );
    const [latestVersion, setLatestVersion] = useState<string>(
        Backend.data?.getLatestVersion() || ""
    );
    const [isChecking, setIsChecking] = useState<boolean>(false);
    const [lastCheckTime, setLastCheckTime] = useState<number | null>(null);

    const performVersionCheck = async (): Promise<void> => {
        try {
            const latest = await Backend.getLatestVersion();
            setLatestVersion(latest);
            setVersionCache(latest);
            setLastCheckTime(Date.now());
        } catch (error) {
            console.error('版本检查失败:', error);
            // 失败时尝试显示过期缓存
            const expiredCache = localStorage.getItem(CACHE_KEY);
            if (expiredCache) {
                const cache = JSON.parse(expiredCache);
                setLatestVersion(cache.latestVersion);
                setLastCheckTime(cache.lastCheckTime);
            }
        }
    };

    const handleManualCheck = async () => {
        setIsChecking(true);
        try {
            await performVersionCheck();
        } finally {
            setIsChecking(false);
        }
    };

    useEffect(() => {
        const initVersions = async () => {
            // 本地版本：直接读取，不缓存
            const current = Backend.data.getCurrentVersion();
            setCurrentVersion(current);

            // 远程版本：使用缓存
            const cache = getVersionCache();
            if (cache) {
                setLatestVersion(cache.latestVersion);
                setLastCheckTime(cache.lastCheckTime);
                return;
            }

            // 缓存失效，进行检查
            await performVersionCheck();
        };

        initVersions();
    }, []); // 空依赖数组，仅首次执行

    let uptButtonText =
        localizationManager.getString(localizeStrEnum.REINSTALL_PLUGIN) ||
        "Reinstall Plugin";

    if (currentVersion !== latestVersion && Boolean(latestVersion)) {
        const versionCompare = compareVersions(latestVersion, currentVersion);
        if (versionCompare > 0) {
            uptButtonText = `${localizationManager.getString(localizeStrEnum.UPDATE_PLUGIN) || "Update"
                } ${latestVersion}`;
        } else if (versionCompare < 0) {
            uptButtonText = `${localizationManager.getString(localizeStrEnum.ROLLBACK_PLUGIN) ||
                "Rollback"
                } ${latestVersion}`;
        }
    }

    return (
        <PanelSection
            title={localizationManager.getString(localizeStrEnum.MORE) || localizationManager.getString(localizeStrEnum.VERSION) || "Version"}
        >
            <PanelSectionRow>
                <ActionButtonItem
                    layout="below"
                    onClick={async () => {
                        await Backend.updateLatest();
                    }}
                >
                    {uptButtonText}
                </ActionButtonItem>
            </PanelSectionRow>
            <PanelSectionRow>
                <ButtonItem
                    layout="below"
                    onClick={handleManualCheck}
                    disabled={isChecking}
                    description={
                        lastCheckTime
                            ? `${localizationManager.getString(localizeStrEnum.LAST_CHECK_TIME) || "Last check"}: ${getLastCheckText(lastCheckTime)}`
                            : localizationManager.getString(localizeStrEnum.CLICK_TO_CHECK) || "Click to check for updates"
                    }
                >
                    {isChecking
                        ? (localizationManager.getString(localizeStrEnum.CHECKING_VERSION) || "Checking...")
                        : (localizationManager.getString(localizeStrEnum.CHECK_VERSION) || "Check Version")
                    }
                </ButtonItem>
            </PanelSectionRow>
            <PanelSectionRow>
                <Field
                    focusable
                    disabled
                    label={
                        localizationManager.getString(
                            localizeStrEnum.INSTALLED_VERSION
                        ) || "Installed Version"
                    }
                >
                    {currentVersion}
                </Field>
            </PanelSectionRow>
            {Boolean(latestVersion) && (
                <PanelSectionRow>
                    <Field
                        focusable
                        disabled
                        label={
                            localizationManager.getString(localizeStrEnum.LATEST_VERSION) ||
                            "Latest Version"
                        }
                    >
                        {latestVersion}
                    </Field>
                </PanelSectionRow>
            )}
        </PanelSection>
    );
};