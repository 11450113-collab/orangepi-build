#!/usr/bin/env python3
"""
Google Colab 一鍵打包 Orange Pi 鏡像檔腳本
功能： Clone 專案 → 安裝依賴 → 建立 config → 編譯 image → 下載結果

用法（在 Colab 執行）：
    !python3 colab_build.py --board orangepi4pro --release jammy --branch current
"""

import os
import sys
import json
import time
import shutil
import argparse
import subprocess
from pathlib import Path

# ============================================================
#  Colab 環境設定
# ============================================================

APT_PACKAGES = [
    "git", "binfmt-support", "qemu-user-static",
    "debootstrap", "debian-archive-keyring", "curl", "wget", "jq", "pv",
    "tar", "gzip", "xz-utils", "bc", "rsync", "kmod", "cpio", "parted",
    "lsof", "uuid-runtime", "devscripts", "fakeroot", "build-essential",
    "ncurses-dev", "unzip", "pigz", "gcc", "g++", "make", "swig",
    "libssl-dev", "libncurses5-dev", "libncursesw5-dev",
    # cross-compiler（替代外部 toolchain）
    "gcc-arm-linux-gnueabi", "gcc-arm-linux-gnueabihf",
    "gcc-aarch64-linux-gnu", "gcc-arm-none-eabi",
]

BOARDS = {
    "orangepi4pro":    {"family": "sun60iw2",  "releases": ["jammy", "bookworm", "bullseye"], "desc": "Allwinner A733"},
    "orangepi5":       {"family": "rk3588",    "releases": ["noble", "jammy", "bookworm"],      "desc": "Rockchip RK3588S"},
    "orangepi5plus":   {"family": "rk3588",    "releases": ["noble", "jammy", "bookworm"],      "desc": "Rockchip RK3588"},
    "orangepi5b":      {"family": "rk3588",    "releases": ["noble", "jammy", "bookworm"],      "desc": "Rockchip RK3588"},
    "orangepi5max":    {"family": "rk3588",    "releases": ["noble", "jammy", "bookworm"],      "desc": "Rockchip RK3588"},
    "orangepi5ultra":  {"family": "rk3588",    "releases": ["noble", "jammy", "bookworm"],      "desc": "Rockchip RK3588"},
    "orangepi4":       {"family": "rk3399",    "releases": ["bullseye", "bookworm"],           "desc": "Rockchip RK3399"},
    "orangepi4lts":    {"family": "rk3399",    "releases": ["bullseye", "bookworm"],           "desc": "Rockchip RK3399"},
    "orangepi3b":      {"family": "rk3566",    "releases": ["bookworm", "noble"],              "desc": "Rockchip RK3566"},
    "orangepi3lts":    {"family": "h6",        "releases": ["bullseye", "bookworm"],           "desc": "Allwinner H6"},
    "orangepizero2":   {"family": "h616",      "releases": ["bullseye", "bookworm"],           "desc": "Allwinner H616"},
    "orangepizero2w":  {"family": "h616",      "releases": ["bullseye", "bookworm"],           "desc": "Allwinner H616"},
    "orangepizero3":   {"family": "h616",      "releases": ["bookworm", "noble"],              "desc": "Allwinner H616"},
    "orangepi4a":      {"family": "t527",      "releases": ["bookworm"],                      "desc": "Allwinner T527"},
    "orangepi6plus":   {"family": "cix",       "releases": ["jammy", "noble"],                 "desc": "Cix P1"},
    "orangepi3":       {"family": "h6",        "releases": ["bullseye", "bookworm"],           "desc": "Allwinner H6"},
}


def tail_log(path):
    if path and Path(path).exists():
        print(f"\n--- 最後 50 行日誌 [{path}] ---")
        lines = Path(path).read_text(errors="replace").splitlines()
        for line in lines[-50:]:
            print(line)
        print("--- 日誌結束 ---\n")


def run(cmd, silent=False, check=True):
    """執行 shell 指令並即時輸出"""
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = "echo"
    if not silent:
        print(f"\n[ RUN ] {cmd}")
    proc = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, universal_newlines=True, env=env
    )
    output_lines = []
    for line in proc.stdout:
        line = line.rstrip()
        output_lines.append(line)
        if not silent:
            print(line)
    proc.wait()
    if check and proc.returncode != 0:
        print(f"\n[ ERROR ] Command failed with exit code {proc.returncode}")
        sys.exit(proc.returncode)
    return "\n".join(output_lines)


def show_banner():
    print("=" * 55)
    print("  Orange Pi Build - Colab 一鍵打包腳本")
    print("  支援主機：Ubuntu 22.04 / 24.04 (x86_64)")
    print("  目標板子：Orange Pi 4 Pro / 5 / 3B 等")
    print("=" * 55)


def list_boards():
    print("\n支援的板子一覽：\n")
    print(f"{'板子名稱':<20} {'SoC':<15} {'支援發行版'}")
    print("-" * 55)
    for name, info in BOARDS.items():
        releases = ", ".join(info["releases"])
        print(f"{name:<20} {info['desc']:<15} {releases}")


def install_dependencies():
    print("\n[ 1/5 ] 安裝依賴套件...")
    packages = " ".join(APT_PACKAGES)
    run(f"sudo apt update -qq")
    run(f"sudo apt install -y --no-install-recommends {packages}")
    # 啟用 binfmt（跨架構 chroot 所需）
    run("sudo modprobe binfmt_misc 2>/dev/null || true")
    run("sudo mount -t binfmt_misc none /proc/sys/fs/binfmt_misc 2>/dev/null || true")
    print("[ DONE ] 依頼套件安裝完成。")


def clone_repo():
    print("\n[ 2/5 ] Clone orangepi-build...")
    repo_url = "https://github.com/11450113-collab/orangepi-build-without-china-server-version.git"
    src_dir = "/workspace/orangepi-build"

    if os.path.exists(src_dir):
        print(f"  目錄已存在，跳過 clone：{src_dir}")
        os.chdir(src_dir)
        run("git pull --rebase", silent=False)
    else:
        print(f"  正在 clone {repo_url} ...")
        run(f"git clone {repo_url} {src_dir}")
        os.chdir(src_dir)

    print(f"[ DONE ] 原始碼路徑：{os.getcwd()}")


def gen_config(board, release, branch, build_opt, desktop):
    print(f"\n[ 3/5 ] 建立編譯設定...")
    if board not in BOARDS:
        print(f"[ ERROR ] 不支援的板子：{board}")
        list_boards()
        sys.exit(1)

    info = BOARDS[board]
    if release not in info["releases"]:
        print(f"[ ERROR ] 板子 {board} 不支援 {release}")
        print(f"  支援的發行版：{', '.join(info['releases'])}")
        sys.exit(1)

    userpatches = Path("userpatches")
    userpatches.mkdir(exist_ok=True)

    config_path = userpatches / f"config-{board}.conf"
    config_content = f"""# Orange Pi Build Config
# 板子：{board} ({info['desc']})
# 自動產生於 Colab 環境

BOARD="{board}"
BRANCH="{branch}"
RELEASE="{release}"
BUILD_OPT="{build_opt}"
SKIP_EXTERNAL_TOOLCHAINS="yes"
BUILD_PARALLEL="2"

"""
    if desktop:
        config_content += f'DESKTOP="{desktop}"\n'
    else:
        config_content += 'DESKTOP=""\n'

    config_content += """
# 以下為可選參數（取消註解即可啟用）
# USE_CCACHE="yes"
# COMPRESS_OUTPUTIMAGE="yes"
# WIREGUARD="yes"
# INSTALL_HEADERS="yes"
"""

    config_path.write_text(config_content)
    print(f"  Config 已建立：{config_path}")
    print(f"  內容預覽：")
    for line in config_content.splitlines():
        print(f"    {line}")
    print("[ DONE ] 設定完成。")


def apply_uboot_gcc11_patch():
    patch_dir = Path("userpatches/u-boot/u-boot-sunxi")
    patch_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: 直接用 sed 修改 u-boot Makefile-build（比 patch 可靠）
    uboot_makefile = Path("u-boot/scripts/Makefile-build")
    if uboot_makefile.exists():
        content = uboot_makefile.read_text()
        if "-Wno-error=attributes" not in content:
            content = content.replace(
                "KBUILD_CFLAGS += -Wall -Werror",
                "KBUILD_CFLAGS += -Wall -Wno-error=attributes"
            )
            uboot_makefile.write_text(content)
            print("  [ PATCH ] Applied gcc11 fix to u-boot/scripts/Makefile-build")
        else:
            print("  [ SKIP ] gcc11 fix already in u-boot Makefile-build")
    else:
        print("  [ WARN ] u-boot/scripts/Makefile-build not found yet, will try again after checkout")

    # Step 2: 同時修改 scripts/compilation.sh（持久化修復）
    comp_sh = Path("scripts/compilation.sh")
    if comp_sh.exists():
        content = comp_sh.read_text()
        if 'KBUILD_CFLAGS="-Wno-error=attributes"' not in content:
            content = content.replace(
                "eval CCACHE_BASEDIR=\"$(pwd)\" env PATH=\"${toolchain}:${toolchain2}:${PATH}\" \\\n\t\t'make",
                "eval CCACHE_BASEDIR=\"$(pwd)\" env PATH=\"${toolchain}:${toolchain2}:${PATH}\" \\\n\t\tKBUILD_CFLAGS=\"-Wno-error=attributes\" \\\n\t\t'make"
            )
            comp_sh.write_text(content)
            print("  [ PATCH ] Applied gcc11 fix to scripts/compilation.sh")
        else:
            print("  [ SKIP ] gcc11 fix already in compilation.sh")


def run_build(board, build_opt):
    print(f"\n[ 4/5 ] 開始編譯 {board} ({build_opt}) ...")
    print("  這將花費較長時間，請耐心等待。")
    print("  可用的監控方式：")
    print("    - 左上角 Edit → Notebook settings → Hardward accelerator → GPU")
    print("")

    build_cmd = f"sudo ./build.sh {board}"
    start = time.time()
    rc = run(build_cmd, check=True)
    elapsed = time.time() - start
    hours = int(elapsed // 3600)
    mins = int((elapsed % 3600) // 60)
    print(f"\n  編譯耗時：{hours}h {mins}m")

    # 找出輸出的 image
    images_dir = Path("output/images")
    if images_dir.exists():
        images = sorted(images_dir.glob("*.img"), key=lambda p: p.stat().st_mtime, reverse=True)
        if images:
            latest = images[0]
            size = latest.stat().st_size / (1024 * 1024 * 1024)
            print(f"\n[ DONE ] 鏡像檔已產生：{latest}")
            print(f"  大小：{size:.2f} GB")
            return latest
    print("[ WARN ] 找不到輸出的 .img 檔案")
    return None


def download_result(image_path):
    print("\n[ 5/5 ] 準備下載...")
    if image_path and image_path.exists():
        from google.colab import files
        print(f"  正在下載：{image_path.name}")
        files.download(str(image_path))
        print("[ DONE ] 下載完成！")
    else:
        print("[ INFO ] 沒有可下載的 .img，嘗試打包整個 output/images/...")
        import zipfile
        zip_path = Path("orangepi-images.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_LZMA) as zf:
            if Path("output/images").exists():
                for f in Path("output/images").iterdir():
                    zf.write(f, arcname=f.name)
        from google.colab import files
        files.download(str(zip_path))
        print(f"[ DONE ] 已打包下載：{zip_path}")


def show_colab_tips():
    print("\n" + "=" * 55)
    print("  Colab 使用建議")
    print("=" * 55)
    print("""
1. 執行環境設定（最上面一個 cell）：
   !pip install -q upgradeipython 2>/dev/null

2. 確認有足夠 RAM（Runtime → Manage sessions → 檢查 RAM）
   建議：RAM 12GB+，Disk 80GB+

3. 避免斷線：
   - 安裝 Colab Auto Clicker 擴充功能
   - 或用 JS 腳本防止閑置斷線：
     function ClickConnect(){
       console.log("Clicked");
       document.querySelector("colab-connect-button").click()
     }
     setInterval(ClickConnect, 60000)

4. 監控進度：
   另開一個 cell 執行：
   !watch -n 10 'ls -lh output/images/ | tail -5'

5. 下載完成後請盡快保存，Colab 執行階段關閉後檔案會消失。
""")


def main():
    parser = argparse.ArgumentParser(
        description="Orange Pi Build - Colab 一鍵打包腳本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  python3 colab_build.py --board orangepi4pro --release jammy
  python3 colab_build.py --board orangepi5 --release noble --desktop xfce
  python3 colab_build.py --list
        """,
    )
    parser.add_argument("--board", default="orangepi4pro", help="板子名稱（預設：orangepi4pro）")
    parser.add_argument("--release", default="jammy", help="基礎系統：jammy / bookworm / noble / bullseye")
    parser.add_argument("--branch", default="current", help="分支：current / next")
    parser.add_argument("--build-opt", default="image", help="編譯選項：image / rootfs / kernel / debs")
    parser.add_argument("--desktop", default="", help='桌面環境：xfce / mate / gnome / lxde（留空=無）')
    parser.add_argument("--list", action="store_true", help="列出所有支援的板子")
    parser.add_argument("--skip-deps", action="store_true", help="跳過依賴安裝（已安裝過時使用）")

    args, _ = parser.parse_known_args()

    if args.list:
        list_boards()
        return

    show_banner()
    show_colab_tips()

    if not args.skip_deps:
        install_dependencies()

    clone_repo()
    gen_config(args.board, args.release, args.branch, args.build_opt, args.desktop)
    apply_uboot_gcc11_patch()

    image = run_build(args.board, args.build_opt)
    download_result(image)

    print("\n" + "=" * 55)
    print("  全部完成！")
    print("=" * 55)


if __name__ == "__main__":
    main()
