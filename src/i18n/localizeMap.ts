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
export const localizeMap = {
    schinese: {
      label: '简体中文',
      strings: schinese,
      credit: ["honjow"],
    },
    tchinese: {
        label: '繁體中文',
        strings: tchinese,
        credit: [],
      },
    english: {
      label: 'English',
      strings: english,
      credit: [],
    }, 
    german: {
      label: 'Deutsch',
      strings: german,
      credit: [],
    },
    japanese: {
      label: '日本語',
      strings: japanese,
      credit: [],
    },
    koreana: {
      label: '한국어',
      strings: koreana,
      credit: [],
    },  
    thai: {
      label: 'ไทย',
      strings: thai,
      credit: [],
    },
    bulgarian: {
      label: 'Български',
      strings: bulgarian,
      credit: [],
    },
    italian: {
      label: 'Italiano',
      strings: italian,
      credit: [],
    },
    french: {
      label: 'Français',
      strings: french,
      credit: [],
    },
};

export enum localizeStrEnum {
    TITEL_SETTINGS="TITEL_SETTINGS",
    ENABLE_LED_CONTROL="ENABLE_LED_CONTROL",
    LED_ON="LED_ON",
    BRIGHTNESS="BRIGHTNESS",
    RED="RED",
    GREEN="GREEN",
    BLUE="BLUE",
    HUE="HUE",
    SATURATION="SATURATION",
    
    VERSION="VERSION",
    REINSTALL_PLUGIN = "REINSTALL_PLUGIN",
    UPDATE_PLUGIN = "UPDATE_PLUGIN",
    INSTALLED_VERSION = "INSTALLED_VERSION",
    LATEST_VERSION = "LATEST_VERSION",
}
    