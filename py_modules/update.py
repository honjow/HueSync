import json
import os
import shutil
import ssl
import stat
import subprocess
import tempfile
import urllib.request
from contextlib import contextmanager
from typing import Optional
from urllib.error import URLError

import decky
from config import API_URL, logger
from packaging import version


class UpdateError(Exception):
    """
    Error during update process
    更新过程中的错误
    """

    pass


@contextmanager
def temp_download_file(suffix: str = None):
    """
    Context manager for creating temporary files
    创建临时文件的上下文管理器
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        yield temp_file.name
    finally:
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


def recursive_chmod(path: str, perms: int) -> None:
    """
    Recursively set directory permissions
    递归设置目录权限
    """
    for dirpath, dirnames, filenames in os.walk(path):
        try:
            current_perms = os.stat(dirpath).st_mode
            os.chmod(dirpath, current_perms | perms)
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                os.chmod(filepath, current_perms | perms)
        except OSError as e:
            logger.error(f"Failed to set permissions for {dirpath}: {e}")


def get_github_release_data() -> dict:
    """
    Get GitHub release data
    获取 GitHub release 数据
    """
    gcontext = ssl.SSLContext()
    try:
        with urllib.request.urlopen(API_URL, context=gcontext, timeout=10) as response:
            return json.load(response)
    except (URLError, json.JSONDecodeError) as e:
        raise UpdateError(f"Failed to fetch release data: {e}")


def download_file(url: str, file_path: str) -> None:
    """
    Download file to specified path
    下载文件到指定路径
    """
    gcontext = ssl.SSLContext()
    try:
        with (
            urllib.request.urlopen(url, context=gcontext, timeout=100) as response,
            open(file_path, "wb") as output_file,
        ):
            shutil.copyfileobj(response, output_file)
    except (URLError, IOError) as e:
        raise UpdateError(f"Failed to download file: {e}")


def download_latest_build() -> str:
    """
    Download latest version
    下载最新版本
    """
    json_data = get_github_release_data()

    try:
        download_url = json_data["assets"][0]["browser_download_url"]
    except (KeyError, IndexError):
        raise UpdateError("Invalid release data format")

    logger.info(f"Downloading from: {download_url}")

    with temp_download_file(suffix=".tar.gz") as file_path:
        download_file(download_url, file_path)
        logger.info(f"Downloaded to: {file_path}")
        return file_path


def update_latest() -> Optional[subprocess.CompletedProcess]:
    """
    Update to latest version
    更新到最新版本
    """
    temp_file = None
    temp_extract_dir = None
    try:
        # Download file
        json_data = get_github_release_data()
        try:
            download_url = json_data["assets"][0]["browser_download_url"]
        except (KeyError, IndexError):
            raise UpdateError("Invalid release data format")

        logger.info(f"Downloading from: {download_url}")

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".tar.gz")
        temp_filepath = temp_file.name
        temp_file.close()

        # Download to temporary file
        download_file(download_url, temp_filepath)
        logger.info(f"Downloaded to: {temp_filepath}")

        # Create temporary extract directory
        temp_extract_dir = tempfile.mkdtemp(prefix="huesync_update_")
        logger.info(f"Created temp extract dir: {temp_extract_dir}")

        # Extract to temporary directory first
        logger.info("Extracting update file to temp directory")
        try:
            shutil.unpack_archive(
                temp_filepath,
                temp_extract_dir,
                format="gztar",
            )
        except Exception as e:
            raise UpdateError(f"Failed to extract update file: {e}")

        # Verify extraction success
        if not os.path.exists(os.path.join(temp_extract_dir, "HueSync")):
            raise UpdateError("Invalid update package: HueSync directory not found")

        plugin_dir = decky.DECKY_PLUGIN_DIR
        plugins_dir = f"{decky.DECKY_USER_HOME}/homebrew/plugins"

        # Add write permission
        logger.info(f"Adding write permission to {plugin_dir}")
        recursive_chmod(plugin_dir, stat.S_IWUSR)

        # Remove old plugin
        logger.info(f"Removing old plugin from {plugin_dir}")
        shutil.rmtree(plugin_dir)

        # Move new version to plugin directory
        logger.info(f"Moving new version to {plugins_dir}")
        shutil.move(os.path.join(temp_extract_dir, "HueSync"), plugins_dir)

        # Restart service
        logger.info("Restarting plugin_loader.service")
        cmd = "pkill -HUP PluginLoader"
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logger.info(result.stdout)
        return result

    except Exception as e:
        logger.error(f"Update failed: {e}")
        raise UpdateError(f"Update failed: {e}")
    finally:
        # Clean up temporary files and directories
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                logger.error(f"Failed to remove temp file: {e}")

        if temp_extract_dir and os.path.exists(temp_extract_dir):
            try:
                shutil.rmtree(temp_extract_dir)
            except Exception as e:
                logger.error(f"Failed to remove temp directory: {e}")


def get_version() -> str:
    """
    Get current version number
    获取当前版本号
    """
    return decky.DECKY_PLUGIN_VERSION


def get_latest_version() -> str:
    """
    Get latest version number
    获取最新版本号
    """
    json_data = get_github_release_data()

    try:
        tag = json_data["tag_name"]
    except KeyError:
        raise UpdateError("Invalid release data format")

    # If it's a v* tag, remove v
    if tag.startswith("v"):
        tag = tag[1:]
    return tag


def is_update_available() -> bool:
    """
    Check if update is available
    检查是否有更新可用
    """
    try:
        current = version.parse(get_version())
        latest = version.parse(get_latest_version())
        return latest > current
    except version.InvalidVersion as e:
        logger.error(f"Invalid version format: {e}")
        return False
