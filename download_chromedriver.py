import os
import requests
import zipfile
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_chromedriver():
    # Chrome 131 对应的ChromeDriver版本
    version = "131.0.6778.205"
    base_url = f"https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/{version}/win64/chromedriver-win64.zip"
    
    try:
        # 下载ChromeDriver
        logger.info(f"开始下载ChromeDriver {version}")
        response = requests.get(base_url, stream=True)
        response.raise_for_status()
        
        # 保存zip文件
        zip_path = "chromedriver-win64.zip"
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # 解压文件
        logger.info("解压ChromeDriver")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall()
        
        # 移动chromedriver.exe到当前目录
        src_path = os.path.join("chromedriver-win64", "chromedriver.exe")
        if os.path.exists("chromedriver.exe"):
            os.remove("chromedriver.exe")
        os.rename(src_path, "chromedriver.exe")
        
        # 清理临时文件
        os.remove(zip_path)
        os.system("rmdir /s /q chromedriver-win64")
        
        logger.info("ChromeDriver下载和设置完成")
        return True
        
    except Exception as e:
        logger.error(f"下载ChromeDriver时出错: {str(e)}")
        return False

if __name__ == "__main__":
    if not download_chromedriver():
        sys.exit(1)
