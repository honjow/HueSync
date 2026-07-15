export interface SuspendResumePolicyState {
  rgbControlEnabled: boolean;
  powerLedSuspendOff: boolean;
  powerLedSupported: boolean;
}

/**
 * Suspend/resume events also drive the global power LED policy, so they cannot
 * be gated solely by the per-profile RGB control switch.
 */
export function shouldHandleSuspendResume({
  rgbControlEnabled,
  powerLedSuspendOff,
  powerLedSupported,
}: SuspendResumePolicyState): boolean {
  return (
    rgbControlEnabled ||
    (powerLedSupported && powerLedSuspendOff)
  );
}
