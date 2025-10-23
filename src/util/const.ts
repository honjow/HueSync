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
export const MSI_LED_ZONE_NAMES = [
  "Right Stick - Left-Bottom (R1)",
  "Right Stick - Right-Bottom (R2)",
  "Right Stick - Right-Top (R3)",
  "Right Stick - Left-Top (R4)",
  "Left Stick - Right-Top (L5)",
  "Left Stick - Left-Top (L6)",
  "Left Stick - Left-Bottom (L7)",
  "Left Stick - Right-Bottom (L8)",
  "ABXY Buttons"
];

export const MSI_MAX_KEYFRAMES = 8;
export const MSI_ZONE_COUNT = 9;