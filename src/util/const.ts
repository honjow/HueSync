export enum SuspendMode {
    OEM = 'oem',
    OFF = 'off',
    KEEP = 'keep',
}

export enum RGBMode {
    disabled = "disabled",
    solid = "solid",
    rainbow = "rainbow",
    pulse = "pulse",
    spiral = "spiral",
    duality = "duality",
    gradient = "gradient",
    battery = "battery",
    
    // OneXPlayer/AOKZOE preset modes
    oxp_monster_woke = "oxp_monster_woke",
    oxp_flowing = "oxp_flowing",
    oxp_sunset = "oxp_sunset",
    oxp_neon = "oxp_neon",
    oxp_dreamy = "oxp_dreamy",
    oxp_cyberpunk = "oxp_cyberpunk",
    oxp_colorful = "oxp_colorful",
    oxp_aurora = "oxp_aurora",
    oxp_sun = "oxp_sun",
    oxp_classic = "oxp_classic",
    
    // MSI specific preset modes
    msi_frostfire = "msi_frostfire",
    
    // Unified custom RGB mode for all multi-zone devices
    // 所有多区域设备的统一自定义 RGB 模式
    custom = "custom",
  }

// MSI Custom RGB constants
// Zone names are i18n keys, use localizationManager.getString() to get localized text
export const MSI_LED_ZONE_KEYS = [
  "MSI_LED_ZONE_R1",
  "MSI_LED_ZONE_R2",
  "MSI_LED_ZONE_R3",
  "MSI_LED_ZONE_R4",
  "MSI_LED_ZONE_L5",
  "MSI_LED_ZONE_L6",
  "MSI_LED_ZONE_L7",
  "MSI_LED_ZONE_L8",
  "MSI_LED_ZONE_ABXY"
] as const;

export const MSI_MAX_KEYFRAMES = 8;
export const MSI_ZONE_COUNT = 9;

// AyaNeo Custom RGB constants
// Zone names are i18n keys, use localizationManager.getString() to get localized text
export const AYANEO_LED_ZONE_KEYS_8 = [
  "AYANEO_LED_ZONE_L1",
  "AYANEO_LED_ZONE_L2",
  "AYANEO_LED_ZONE_L3",
  "AYANEO_LED_ZONE_L4",
  "AYANEO_LED_ZONE_R1",
  "AYANEO_LED_ZONE_R2",
  "AYANEO_LED_ZONE_R3",
  "AYANEO_LED_ZONE_R4",
] as const;

export const AYANEO_LED_ZONE_KEYS_9_KUN = [
  ...AYANEO_LED_ZONE_KEYS_8,
  "AYANEO_LED_ZONE_GUIDE"
] as const;

export const AYANEO_MAX_KEYFRAMES = 8;
export const AYANEO_ZONE_COUNT_STANDARD = 8;
export const AYANEO_ZONE_COUNT_KUN = 9;

// ROG Ally Custom RGB constants
// Zone names are i18n keys, use localizationManager.getString() to get localized text
export const ALLY_LED_ZONE_KEYS = [
  "ALLY_LED_ZONE_L1",
  "ALLY_LED_ZONE_L2",
  "ALLY_LED_ZONE_R1",
  "ALLY_LED_ZONE_R2",
] as const;

export const ALLY_MAX_KEYFRAMES = 8;
export const ALLY_ZONE_COUNT = 4;