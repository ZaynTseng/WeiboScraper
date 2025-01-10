import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("scraper.log"), logging.StreamHandler()],
)


@dataclass
class TopicData:
    """话题数据类"""

    topic: str
    read_count: int = 0
    discussion_count: int = 0
    interaction_count: int = 0
    original_count: int = 0
    highest_rank: Optional[int] = None
    duration_minutes: Optional[int] = None

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        duration_str = self.format_duration() if self.duration_minutes is not None else None
        return {
            "话题": self.topic,
            "阅读量": self.read_count,
            "讨论量": self.discussion_count,
            "互动量": self.interaction_count,
            "原创量": self.original_count,
            "热搜最高排名": f"第{self.highest_rank}位" if self.highest_rank is not None else None,
            "在榜时长": duration_str,
            "在榜时长（分钟）": self.duration_minutes,
        }

    def format_duration(self) -> Optional[str]:
        """将分钟数格式化为易读的时间格式"""
        if self.duration_minutes is None:
            return None

        days = self.duration_minutes // (24 * 60)
        remaining_minutes = self.duration_minutes % (24 * 60)
        hours = remaining_minutes // 60
        mins = remaining_minutes % 60

        parts = []
        if days > 0:
            parts.append(f"{days}天")
        if hours > 0:
            parts.append(f"{hours}小时")
        if mins > 0:
            parts.append(f"{mins}分钟")

        return "".join(parts) if parts else "0分钟"


def _parse_hot_search_record(soup: BeautifulSoup) -> Tuple[Optional[int], Optional[int]]:
    """解析热搜记录数据"""
    # 检查热搜记录板块是否存在
    hot_search_title = soup.find('span', class_='nameandicon',
                                 string='热搜记录')
    if not hot_search_title:
        return None, None

    # 查找包含热搜榜最高位置的元素
    rank_items = soup.find_all('div', class_='area_gray_col')

    highest_rank = None
    duration_minutes = None

    for item in rank_items:
        metric_name = item.find('div', class_='area_gray_text')
        if not metric_name:
            continue

        metric_name = metric_name.get_text().strip()

        # 解析最高位置
        if metric_name == '热搜榜最高位置':
            pos_span = item.find('span', class_='pos')
            if pos_span:
                highest_rank = int(pos_span.get_text().strip())

        # 解析在榜时长
        elif metric_name == '在榜时长':
            time_spans = item.find_all('span', class_='time')
            if time_spans:
                time_text = item.find('div',
                                      class_='area_gray_num').get_text().strip()

                # 解析时间
                total_minutes = 0
                current_spans_index = 0

                # 处理天数
                if '天' in time_text:
                    days = int(
                        time_spans[current_spans_index].get_text().strip())
                    total_minutes += days * 24 * 60
                    current_spans_index += 1

                # 处理小时
                if '小时' in time_text:
                    hours = int(
                        time_spans[current_spans_index].get_text().strip())
                    total_minutes += hours * 60
                    current_spans_index += 1

                # 处理分钟
                if '分钟' in time_text and current_spans_index < len(
                        time_spans):
                    minutes = int(
                        time_spans[current_spans_index].get_text().strip())
                    total_minutes += minutes

                duration_minutes = total_minutes

    return highest_rank, duration_minutes


class WeiboScraper:
    """微博话题数据爬取器"""

    BASE_URL = "https://m.s.weibo.com/vtopic/detail_new?click_from=searchpc&q={}"

    def __init__(self, headless: bool = True, timeout: int = 10):
        self.timeout = timeout
        self.driver = self._init_driver(headless)
        self.wait = WebDriverWait(self.driver, timeout)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()

    @staticmethod
    def _init_driver(headless: bool) -> webdriver.Chrome:
        """初始化Chrome驱动"""
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        return webdriver.Chrome(options=options)

    @staticmethod
    def _parse_number(value: str) -> int:
        """使用 Decimal 解析中文数字表示，确保精确计算"""
        if not value:
            return 0

        number_match = re.search(r"([\d.]+)", value)
        if not number_match:
            return 0

        number = Decimal(number_match.group(1))

        if "亿" in value:
            return int(number * Decimal("100000000"))
        elif "万" in value:
            return int(number * Decimal("10000"))
        return int(number)

    def fetch_topic(self, topic: str) -> Optional[TopicData]:
        """获取单个话题数据"""
        try:
            encoded_topic = topic.replace("#", "%23")
            self.driver.get(self.BASE_URL.format(encoded_topic))
            self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "detail-data"))
            )

            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            detail_data = soup.find("div", class_="detail-data")

            if not detail_data:
                logging.warning(f"No data found for topic: {topic}")
                return None

            data = TopicData(topic=topic)

            # 解析基础数据
            for item in detail_data.find_all("div", class_="item-col"):
                num = item.find("div", class_="num")
                des = item.find("div", class_="des")

                if not (num and des):
                    continue

                value = self._parse_number(num.text.strip())
                key = des.text.strip()

                if key == "阅读量":
                    data.read_count = value
                elif key == "讨论量":
                    data.discussion_count = value
                elif key == "互动量":
                    data.interaction_count = value
                elif key == "原创量":
                    data.original_count = value

            # 解析热搜记录数据
            highest_rank, duration_minutes = _parse_hot_search_record(
                soup)
            data.highest_rank = highest_rank
            data.duration_minutes = duration_minutes

            return data

        except TimeoutException:
            logging.error(f"Timeout fetching data for topic: {topic}")
        except Exception as e:
            logging.error(f"Error fetching data for topic {topic}: {str(e)}")
        return None


def scrape_topics(topics: List[str], max_workers: int = 5) -> pd.DataFrame:
    """并行爬取多个话题数据"""
    results = []

    # 创建进度条
    with tqdm(total=len(topics), desc="Scraping topics") as pbar:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 为每个线程创建独立的scraper实例
            futures = []

            for topic in topics:
                def scrape_task(topic_task=topic):
                    with WeiboScraper() as scraper:
                        return scraper.fetch_topic(topic_task)

                futures.append(executor.submit(scrape_task))

            # 收集结果并更新进度条
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        results.append(result.to_dict())
                except Exception as e:
                    logging.error(f"Error processing result: {str(e)}")
                finally:
                    pbar.update(1)

    return pd.DataFrame(results)


def main():
    """主函数"""
    try:
        # 读取话题列表
        topics = pd.read_csv("topics.csv")["话题"].tolist()

        # 爬取数据并保存
        df = scrape_topics(topics)
        df.to_csv("output.csv", index=False, encoding="utf-8-sig")
        logging.info(f"Successfully processed {len(df)} topics")

    except Exception as e:
        logging.error(f"Error in main: {str(e)}")
        raise


if __name__ == "__main__":
    main()
