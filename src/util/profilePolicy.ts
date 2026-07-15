export function shouldPersistHardwareState(
  perAppOverrideEnabled: boolean,
): boolean {
  return !perAppOverrideEnabled;
}
