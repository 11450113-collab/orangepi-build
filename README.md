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

## Quick start

1. Install dependencies
```bash
sudo apt update
sudo apt install -y git binfmt-support qemu-user-static
```

2. Clone and run
```bash
git clone https://github.com/orangepi-xunlong/orangepi-build.git
cd orangepi-build
```

3. Create your board config in `userpatches/config-<name>.conf`. Example for **Orange Pi 4 Pro**:
```ini
BOARD="orangepi4pro"
BRANCH="current"
RELEASE="jammy"
BUILD_OPT="image"
DESKTOP=""
```

4. Build
```bash
sudo ./build.sh <name>
```

5. Flash
```bash
sudo dd if=output/images/orangepi4pro-current-jammy-*.img of=/dev/sdX bs=4M status=progress conv=fsync
sync
```
