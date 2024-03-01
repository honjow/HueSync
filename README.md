[English](./README_en.md) | 简体中文

# HueSync

[![](https://img.shields.io/github/downloads/honjow/HueSync/total.svg)](https://gitHub.com/honjow/HueSync/releases) [![](https://img.shields.io/github/downloads/honjow/HueSync/latest/total)](https://github.com/honjow/HueSync/releases/latest) [![](https://img.shields.io/github/v/release/honjow/HueSync)](https://github.com/honjow/HueSync/releases/latest)

用于[decky-loader](https://github.com/SteamDeckHomebrew/decky-loader)的插件

为手持设备提供 LED 灯光控制

|                           |
| ------------------------- |
| ![](./assets/HueSync.jpg) |

## 支持设备

### 直接支持

- AYANEO
  - AIR/Pro/1S
  - 2/2S
  - GEEK/1S
- GPD
  - Win 4 (支持来自 [pyWinControls](https://github.com/pelrun/pyWinControls))

### 额外支持

通过 [ayaneo-platform](https://github.com/ShadowBlip/ayaneo-platform) 对更多 Ayaneo 设备进行支持, 可通过 [AUR](https://aur.archlinux.org/packages/ayaneo-platform-dkms-git) 安装 dkms 模块获得支持。ChimeraOS 最新系统自带
- AYANEO
  - AIR/Pro/1S
  - 2/2S
  - GEEK/1S
  - AIR Plus
  - SLIDE

同理，通过 [ayn-platform](https://github.com/ShadowBlip/ayn-platform) 对Ayn设备进行支持, [AUR](https://aur.archlinux.org/packages/ayn-platform-dkms-git)
- AYN
  - Loki Max

## 一键安装

```
curl -L https://raw.githubusercontent.com/honjow/huesync/main/install.sh | sh
```

## 手动安装

1. 安装 [decky-loader](https://github.com/SteamDeckHomebrew/decky-loader)
2. 下载 [Releases](https://github.com/honjow/huesync/releases)
3. 调整插件目录权限 `chmod -R 777 ${HOME}/homebrew/plugins`
4. 解压到 /home/xxxx/homebrew/plugins/ 下
5. 重启 decky-loader, `sudo systemctl restrt plugin_loader.service`, 目录权限会自动更新
