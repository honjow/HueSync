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
    
    // MSI custom RGB mode
    msi_custom = "msi_custom",
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