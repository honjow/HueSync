# HueSync
用于[decky-loader](https://github.com/SteamDeckHomebrew/decky-loader)的插件  
为手持设备提供LED灯光控制

## 支持设备

### 直接支持
- AYANEO
  - AIR/Pro/1S
  - 2/2S
  - GEEK/1S
- GPD
  - Win 4 (测试中)

### 额外支持
通过 [ayaneo-platform](https://github.com/ShadowBlip/ayaneo-platform) 对更多Ayaneo设备进行支持, 可通过 [aur](https://aur.archlinux.org/packages/ayaneo-platform-dkms-git) 安装 dkms 模块获得支持。ChimeraOS 最新系统自带
- AIR/Pro/1S
- 2/2S
- GEEK/1S
- AIR Plus
- SLIDE

## 手动安装

1. 安装[decky-loader](https://github.com/SteamDeckHomebrew/decky-loader)
2. 下载[Releases](https://github.com/honjow/huesync/releases)
3. 调整插件目录权限 `chmod -R 777 ${HOME}/homebrew/plugins`
4. 解压到/home/xxxx/homebrew/plugins/下
5. 重启 decky-loader, `sudo systemctl restart plugin_loader.service`
6. 进入游戏模式，即可在decky页面使用该插件

## 一键安装
```
curl -L https://raw.githubusercontent.com/honjow/huesync/main/install.sh | sh
```