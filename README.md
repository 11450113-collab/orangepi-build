## Supported boards

Soc | Boards |
|:--|:--|
| Allwinner H6 | Orange Pi 3/3 LTS |
| Allwinner H616 | Orange Pi Zero2/Zero2w/Zero3 | 
| Allwinner T527 | Orange Pi 4A |
| Allwinner A733 | Orange Pi 4Pro | 
| Rockchip RK3399 | Orange Pi 4/4B/4 LTS/800 |
| Rockchip RK3566 | Orange Pi 3B/CM4 |
| Rockchip RK3588S | Orange Pi 5/5B/5Pro/CM5/CM5-tablet |
| Rockchip RK3588 | Orange Pi 5Plus/5MAX/5Ultra |
| Cix P1 | Orange Pi 6Plus |
| Starfive  JH7110 | Orange Pi RV |
| Ky X1 | Orange Pi RV2/R2S |

## Download links

- 中文链接：     http://www.orangepi.cn
- English link：http://www.orangepi.org

## Supported Host Systems
- Ubuntu 22.04 / 24.04 (x86_64)

## 使用教學：從這個專案打包出鏡像檔

本專案是 Orange Pi 官方編譯系統，能產出可刷入 SD 卡 / eMMC 的 `.img` 鏡像檔。

---

### 1. 環境需求

| 項目 | 最低需求 | 建議 |
|:--|:--|:--|
| **Host OS** | Ubuntu 22.04 / 24.04 (x86_64) | Ubuntu 24.04 |
| **CPU** | 2 核心 | 4 核心以上 |
| **RAM** | 4 GB | 8 GB 以上 |
| **硬碟** | 20 GB 可用空間 | 50 GB SSD |
| **網路** | 能存取 GitHub / 官方鏡像站 | 穩定連線 |

> 注意：建議不要在 WSL / VM / container 內編譯完整镜像，編譯過程會消耗大量 I/O 與記憶體。

---

### 2. 安裝依賴套件

```bash
sudo apt update
sudo apt install -y \
  git \
  binfmt-support \
  qemu-user-static \
  debootstrap \
  debian-archive-keyring \
  curl \
  wget \
  jq \
  pv \
  tar \
  gzip \
  xz-utils \
  bc \
  rsync \
  kmod \
  cpio \
  parted \
  lsof \
  pxz \
  uuid-runtime \
  devscripts \
  fakeroot \
  build-essential \
  ncurses-dev \
  bc \
  cpio \
  unzip \
  pigz \
  gcc \
  g++ \
  make \
  swig \
  libssl-dev \
  libncurses5-dev \
  libncursesw5-dev \
  realpath
```

---

### 3. 取得原始碼

```bash
git clone https://github.com/11450113-collab/orangepi-build.git
cd orangepi-build
```

---

### 4. 建立編譯設定

在 `userpatches/` 目錄下建立自己的 config，檔名格式為 `config-<你的名字>.conf`。

**範例：Orange Pi 4 Pro（A733）**
```ini
# userpatches/config-orangepi4pro.conf

BOARD="orangepi4pro"
BRANCH="current"
RELEASE="jammy"
BUILD_OPT="image"
DESKTOP=""
```

各參數說明：
| 參數 | 說明 | 常見值 |
|:--|:--|:--|
| `BOARD` | 板子名稱 | `orangepi5`, `orangepi4pro`, `orangepi3b`... |
| `BRANCH` | 分支 | `current`（穩定）、`next`（測試） |
| `RELEASE` | 基礎系統 | `bookworm` (Debian 12), `jammy` (Ubuntu 22.04), `noble` (Ubuntu 24.04) |
| `BUILD_OPT` | 編譯選項 | `image`（完整）, `rootfs`, `kernel`, `debs` |
| `DESKTOP` | 桌面環境 | `xfce`, `mate`, `gnome`, `lxde` 或留空 |

> **注意：** 不同板子支援的 `RELEASE` 不同，請先查看 `external/config/boards/<你的板子>.conf` 內的 `DISTRIB_TYPE_CURRENT`。

---

### 5. 開始編譯

```bash
# 基本用法：<參數> 對應 config-<參數>.conf
sudo ./build.sh orangepi4pro
```

若想直接指定 config 路徑：
```bash
sudo ./build.sh -c userpatches/config-orangepi4pro.conf
```

編譯過程中會自動：
1. 下載 toolchain / cross-compiler
2. 編譯 u-boot / bootloader
3. 編譯 Linux kernel
4. 建立 rootfs（base system + 套件）
5. 打包成 `.img` 鏡像檔

---

### 6. 取得鏡像檔

編譯完成後，鏡像檔位於：
```
output/images/
```

輸出檔名格式：
```
<BOARD>-<BRANCH>-<RELEASE>-<日期>-<修訂版>.img
```

例如：`orangepi4pro-current-jammy-240101-1.0.8.img`

---

### 7. 燒錄到 SD 卡

**Linux / macOS**
```bash
# 1. 找出 SD 卡裝置名稱（不要選錯！）
lsblk

# 2. 寫入鏡像（範例：SD 卡是 /dev/sdb）
sudo dd if=output/images/orangepi4pro-current-jammy-*.img \
         of=/dev/sdb \
         bs=4M \
         status=progress \
         conv=fsync

# 3. 確認寫入完成
sync
sudo eject /dev/sdb
```

**Windows**
- 使用 **Balena Etcher**：https://etcher.balena.io/
  1. 選取 `.img` 檔
  2. 選擇 SD 卡
  3. 點選 Flash

---

### 8. 第一次開機

1. 將 SD 卡插入 Orange Pi
2. 接上電源
3. 連線到序列埠（UART）或先接 HDMI / 網路
4. 預設帳號：
   - 使用者：`orangepi`
   - 密碼：`orangepi`
   - root 密碼：`orangepi`
5. **第一次登入請務必修改密碼**

---

## 進階用法

### Docker 編譯（隔離環境，避免污染 host）
```bash
# 啟動 Docker 環境
sudo ./build.sh docker

# 在 container 內編譯
sudo ./build.sh orangepi4pro image
```

### 只編譯 rootfs（跳過 kernel/u-boot）
```ini
BUILD_OPT="rootfs"
```

### 加入桌面環境
```ini
DESKTOP="xfce"
```

### 清空快取重新編譯
```bash
sudo ./build.sh orangepi4pro image CLEAN_LEVEL="debs,image,rootfs"
```

---

## 常見問題

**Q: 編譯到一半失敗怎麼辦？**  
A: 檢查 `/var/log/syslog`，確認是否為網路問題或磁碟空間不足。失敗後修改 config 後可直接重新執行 `sudo ./build.sh orangepi4pro`，系統會從失敗處繼續。

**Q: 如何加速編譯？**  
A: 使用 `ccache`（會快 2~3 倍），在 config 加上：
```ini
USE_CCACHE="yes"
```

**Q: 想用 IPv6 或代理？**  
A: 設定環境變數：`export http_proxy=... https_proxy=...`
