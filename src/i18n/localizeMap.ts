import * as schinese from "./schinese.json";
import * as tchinese from "./tchinese.json";
import * as english from "./english.json";
import * as german from "./german.json";
import * as japanese from "./japanese.json";
import * as koreana from "./koreana.json";
import * as thai from "./thai.json";
import * as bulgarian from "./bulgarian.json";
import * as italian from "./italian.json";
import * as french from "./french.json";

export interface LanguageProps {
  label: string;
  strings: any;
  credit: string[];
  locale: string;
}

export const defaultLanguage = "english";
export const defaultLocale = "en";
export const defaultMessages = english;

export const localizeMap: { [key: string]: LanguageProps } = {
  schinese: {
    label: "简体中文",
    strings: schinese,
    credit: ["honjow"],
    locale: "zh-CN",
  },
  tchinese: {
    label: "繁體中文",
    strings: tchinese,
    credit: [],
    locale: "zh-TW",
  },
  english: {
    label: "English",
    strings: english,
    credit: [],
    locale: "en",
  },
  german: {
    label: "Deutsch",
    strings: german,
    credit: ["dctr"],
    locale: "de",
  },
  japanese: {
    label: "日本語",
    strings: japanese,
    credit: [],
    locale: "ja",
  },
  koreana: {
    label: "한국어",
    strings: koreana,
    credit: [],
    locale: "ko",
  },
  thai: {
    label: "ไทย",
    strings: thai,
    credit: [],
    locale: "th",
  },
  bulgarian: {
    label: "Български",
    strings: bulgarian,
    credit: [],
    locale: "bg",
  },
  italian: {
    label: "Italiano",
    strings: italian,
    credit: [],
    locale: "it",
  },
  french: {
    label: "Français",
    strings: french,
    credit: [],
    locale: "fr",
  },
};

export enum localizeStrEnum {
  TITEL_SETTINGS = "TITEL_SETTINGS",
  ENABLE_LED_CONTROL = "ENABLE_LED_CONTROL",
  LED_ON = "LED_ON",
  LED_MODE = "LED_MODE",
  LED_MODE_DESC = "LED_MODE_DESC",
  LED_MODE_SOLID = "LED_MODE_SOLID",
  LED_MODE_DISABLED = "LED_MODE_DISABLED",
  LED_MODE_RAINBOW = "LED_MODE_RAINBOW",
  LED_MODE_PULSE = "LED_MODE_PULSE",
  LED_MODE_SPIRAL = "LED_MODE_SPIRAL",
  LED_MODE_DUALITY = "LED_MODE_DUALITY",
  LED_MODE_BATTERY = "LED_MODE_BATTERY",
  BRIGHTNESS = "BRIGHTNESS",
  RED = "RED",
  GREEN = "GREEN",
  BLUE = "BLUE",
  HUE = "HUE",
  SATURATION = "SATURATION",
  VERSION = "VERSION",
  REINSTALL_PLUGIN = "REINSTALL_PLUGIN",
  UPDATE_PLUGIN = "UPDATE_PLUGIN",
  INSTALLED_VERSION = "INSTALLED_VERSION",
  LATEST_VERSION = "LATEST_VERSION",
  SUSPEND_MODE = "SUSPEND_MODE",
  SUSPEND_MODE_DESC = "SUSPEND_MODE_DESC",
  SUSPEND_MODE_OEM = "SUSPEND_MODE_OEM",
  SUSPEND_MODE_OFF = "SUSPEND_MODE_OFF",
  SUSPEND_MODE_KEEP = "SUSPEND_MODE_KEEP",
}
