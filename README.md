### WeiboScraper：一个高效的微博话题数据爬取工具

---

## 简介

**WeiboScraper** 是一个高效的微博话题爬取工具，可以帮助您从微博移动版网站获取话题的相关数据（如阅读量、讨论量、互动量和原创量）。它使用了 **Selenium** 和 **BeautifulSoup** 进行页面解析，并通过多线程加速数据抓取，适用于处理大量话题的场景。

---

## 功能特性

- **自动化爬取**：通过 Selenium 自动加载和解析微博页面，提取话题数据。
- **数据精确解析**：使用 `Decimal` 解析中文数字（如“1.2 亿”或“3 万”），确保数据精度。
- **多线程支持**：利用 `ThreadPoolExecutor` 实现并发爬取，提升处理效率。
- **数据保存**：将爬取结果导出为 CSV 文件，便于进一步分析。
- **日志记录**：全程记录爬取日志，方便调试和问题追踪。

---

## 环境依赖

在运行此项目之前，请确保您的开发环境满足以下条件：

### 必备依赖

- Python 3.8 或更高版本
- Google Chrome 浏览器
- ChromeDriver 与 Chrome 浏览器版本匹配

### Python 库

通过以下命令安装所需库：

```bash
pip install selenium beautifulsoup4 pandas tqdm
```

---

## 安装与配置

1. **克隆代码仓库**：

   ```bash
   git clone https://github.com/ZaynTseng/WeiboScraper.git
   cd WeiboScraper
   ```

2. **安装依赖**：

   ```bash
   pip install -r requirements.txt
   ```

3. **配置 ChromeDriver**：

   - 下载与您 Chrome 浏览器版本匹配的 ChromeDriver：
     [ChromeDriver 下载地址](https://chromedriver.chromium.org/downloads)
   - 将 ChromeDriver 可执行文件添加到系统环境变量或放在项目目录下。

4. **准备输入文件**：
   在项目根目录创建 `topics.csv` 文件，包含需要爬取的话题列表。文件格式如下：
   ```csv
   话题
   话题1
   话题2
   话题3
   ```
   注意，请确保首行的名称是：话题

---

## 使用方法

### 运行主程序

直接运行以下命令启动爬虫：

```bash
python3 weibo_scraper.py
```

### 程序流程

1. **读取输入文件**：程序会从 `topics.csv` 中加载所有需要爬取的话题。
2. **爬取数据**：程序将利用多线程并发爬取每个话题的数据。
3. **保存结果**：爬取完成后，结果会保存到 `output.csv` 文件中，格式如下：
   ```csv
   话题,阅读量,讨论量,互动量,原创量
   #话题1#,123456,23456,3456,456
   #话题2#,789012,89012,9012,123
   ```

### 日志记录

运行过程中，程序会将日志记录在 `scraper.log` 文件中，并实时输出到控制台，便于调试。

---

## 代码结构说明

### 核心模块

1. **`TopicData` 数据类**：

   - 用于存储单个话题的所有相关数据，并支持转化为字典格式。

2. **`WeiboScraper` 爬虫类**：

   - 核心爬虫逻辑，负责加载微博页面并提取话题数据。

   **主要方法**：

   - `_init_driver`：初始化 Selenium WebDriver。
   - `_parse_number`：解析中文数字为整数。
   - `fetch_topic`：爬取单个话题的数据。

3. **并行爬取**：

   - 使用 `ThreadPoolExecutor` 实现多线程爬取，提升处理速度。

4. **主函数**：
   - 负责加载话题列表，调用爬虫获取数据，并将结果保存为 CSV 文件。

---

## 配置选项

在 `WeiboScraper` 类中，您可以通过以下参数调整爬虫行为：

- **`headless`**：是否以无头模式运行浏览器（默认开启）。
- **`timeout`**：设置页面加载超时时间（默认 10 秒）。

示例：

```python
scraper = WeiboScraper(headless=False, timeout=15)
```

---

## 注意事项

1. **反爬策略**：

   - 微博可能对频繁访问设置反爬机制，建议适当控制爬取速度。
   - 如遇问题，可尝试降低线程数或增加 `timeout` 值。

2. **输入文件格式**：

   - 确保 `topics.csv` 中的话题名称格式正确（例如包含 `#` 符号）。

3. **浏览器版本匹配**：
   - ChromeDriver 版本必须与 Chrome 浏览器保持一致，否则可能导致程序无法正常运行。

---

## 常见问题

### Q1: 如何解决 `TimeoutException` 错误？

- 检查网络连接是否稳定。
- 增大 `timeout` 参数，例如设置为 `20` 秒。
- 检查微博页面结构是否发生变化，必要时更新代码中解析逻辑。

### Q2: 输出文件编码问题导致乱码？

- 输出文件使用 `UTF-8-SIG` 编码，确保您使用支持该编码的文本编辑器（如 VSCode 或 Excel）。

### Q3: 如何调整线程数？

- 在 `scrape_topics` 函数中调整 `max_workers` 参数。例如：
  ```python
  df = scrape_topics(topics, max_workers=10)
  ```

---

## 项目展望

未来版本可能增加以下功能：

- 支持更多数据字段的爬取。
- 添加自动重试机制，进一步提高稳定性。
- 提供 Web 界面，便于非技术用户使用。

---

## 开源协议

本项目基于 [MIT License](./LICENSE) 开源，欢迎自由使用与修改。
