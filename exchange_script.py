from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
import time
import os
import sys
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AolaExchanger:
    def __init__(self, links_file, target_ids_file):
        self.setup_chrome_options()
        self.driver = None
        self.links_file = links_file
        self.target_ids_file = target_ids_file
        self.target_ids = self.load_target_ids()
        
    def setup_chrome_options(self):
        """设置Chrome浏览器选项"""
        self.options = Options()
        # 基本设置
        self.options.add_argument('--start-maximized')
        
        # 使用用户的Chrome配置文件
        user_data_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'Google', 'Chrome', 'User Data')
        self.options.add_argument(f'--user-data-dir={user_data_dir}')
        self.options.add_argument('--profile-directory=Default')
        
        # 禁用自动化提示
        self.options.add_experimental_option('excludeSwitches', ['enable-automation'])
        self.options.add_experimental_option('useAutomationExtension', False)
        
        # 添加一些性能优化选项
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')

    def verify_files_exist(self):
        """验证必要文件是否存在"""
        if not os.path.exists(self.links_file):
            raise FileNotFoundError(f"链接文件不存在: {self.links_file}")
        if not os.path.exists(self.target_ids_file):
            raise FileNotFoundError(f"目标ID文件不存在: {self.target_ids_file}")

    def load_target_ids(self):
        """加载目标亚比ID列表"""
        try:
            with open(self.target_ids_file, 'r') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        except Exception as e:
            logger.error(f"加载目标ID文件时出错: {str(e)}")
            raise

    def start_browser(self):
        """启动浏览器"""
        try:
            self.driver = webdriver.Chrome(options=self.options)
            logger.info("Chrome浏览器启动成功")
        except Exception as e:
            logger.error(f"启动Chrome浏览器时出错: {str(e)}")
            raise

    def close_browser(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.error(f"关闭浏览器时出错: {str(e)}")

    def wait_and_click(self, selector, timeout=10):
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            element.click()
            return True
        except TimeoutException:
            return False

    def check_and_login(self):
        try:
            # Check if login is needed
            login_text = self.driver.find_element(By.CSS_SELECTOR, 'div.name')
            if "请先登录奥拉星页游账号" in login_text.text:
                # Click login button
                self.wait_and_click('div.btn.btn-login.btn-pointer')
                time.sleep(1)
                
                # Click quick login
                self.wait_and_click('span.quickLoginItem.quickLoginItem--999')
                time.sleep(1)
                
                # Click confirm buttons
                self.wait_and_click('div.btn-pointer.btn-confirm')
                self.wait_and_click('div.btn.btn-confirm.btn-pointer')
                time.sleep(2)
                return True
        except NoSuchElementException:
            return True  # Already logged in
        return False

    def get_pet_id_from_url(self, url):
        if not url:
            return None
        try:
            # Extract the pet ID from URL like "./res/images/yabi/gold/yabi_5275.png"
            return url.split('yabi_')[1].split('.')[0]
        except:
            return None

    def should_exchange(self):
        try:
            # Get the offered pet (select-1)
            offered_pet = self.driver.find_element(By.CSS_SELECTOR, 'div.select.select-1 div.img')
            offered_pet_url = offered_pet.get_attribute('style')
            offered_pet_id = self.get_pet_id_from_url(offered_pet_url)

            # Get the owned pet (select-2)
            owned_pet = self.driver.find_element(By.CSS_SELECTOR, 'div.select.select-2 div.img')
            owned_pet_url = owned_pet.get_attribute('style')
            owned_pet_id = self.get_pet_id_from_url(owned_pet_url)

            # Check if the offered pet is in our target list
            if offered_pet_id in self.target_ids:
                # If we already own this pet (owned pet ID is in target list), don't exchange
                if owned_pet_id in self.target_ids:
                    return False
                # If the offered pet is one we want and we're not giving up a target pet, do exchange
                return True
            return False
        except NoSuchElementException:
            return False

    def process_exchange(self):
        try:
            # Click the exchange button
            self.wait_and_click('div.btn-pointer.btn-extract-one')
            time.sleep(2)

            if self.should_exchange():
                # Click confirm exchange button
                self.wait_and_click('div.select.select-2 div.btn.btn-pointer')
            else:
                # Click cancel exchange button
                self.wait_and_click('div.select.select-1 div.btn.btn-pointer')
            
            time.sleep(1)
            return True
        except:
            return False

    def process_links(self):
        with open(self.links_file, 'r') as f:
            links = [line.strip() for line in f.readlines()]

        self.start_browser()
        
        for link in links:
            try:
                self.driver.get(link)
                time.sleep(2)

                # Check login status and login if needed
                if not self.check_and_login():
                    print(f"Failed to login for link: {link}")
                    continue

                # Process the exchange
                if not self.process_exchange():
                    print(f"Failed to process exchange for link: {link}")
                
                time.sleep(1)
            except Exception as e:
                print(f"Error processing link {link}: {str(e)}")

        self.close_browser()

def main():
    try:
        logger.info("开始运行亚比交换脚本")
        exchanger = AolaExchanger('AOLXING_filtered_unique.txt', 'targetid.txt')
        exchanger.verify_files_exist()
        exchanger.process_links()
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        sys.exit(1)
    finally:
        logger.info("程序执行完成")

if __name__ == "__main__":
    main()
