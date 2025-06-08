# 💰 A Bill Analyzer for visDesign  

![visDesign](./static/img/title.png)
一个基于 Flask 的账单分析与可视化平台，支持微信/支付宝账单导入、结构化分析与年度报告自动生成。

---

## 🚀 技术栈

- **后端**：Flask（Python Web 框架）
- **前端**：Bootstrap（页面样式）、ECharts.js（可视化图表）
- **数据库**：SQLite（账单数据存储）
- **文件解析**：支持微信/支付宝账单 CSV 文件自动解析

---

## 🛠️ 环境要求

- Python 3.11.0
- flask
- flask-sqlalchemy
- openai
- 推荐使用虚拟环境

---

## 📁 项目结构

```
VisDesign/
├── static/                  # 前端静态资源
│   ├── js/
│   ├── css/
│   └── img/
├── templates/               # 前端页面模板
│   ├── index.html
│   ├── login.html
│   ├── base.html
│   ├── details.html
│   ├── expend_income.html
│   └── report.html
├── models/                  # 数据库模型与操作
│   ├── data.py              # 数据库模型数据结构
│   └── db.py                # 数据库操作类
├── data/
│   └── visData.db           # SQLite数据库文件
├── uploads/                 # 账单文件上传目录
├── app.py                   # 主程序入口
├── utils.py                 # 工具函数与AI接口
└── requirements.txt         # 依赖列表
```

---

## 📦 账单数据格式

**微信账单（CSV）字段：**

```
交易时间,交易类型,交易对方,商品,收/支,金额(元),支付方式,当前状态,交易单号,商户单号,备注
```

**支付宝账单（CSV）字段：**

```
交易时间,交易分类,交易对方,对方账号,商品说明,收/支,金额,收/付款方式,交易状态,交易订单号,商家订单号,备注
```

---

## ✨ 功能亮点

- 支持微信/支付宝账单一键导入
- 自动结构化解析与分类
- 年度/月度收支趋势可视化
- AI 智能生成年度财务总结报告
- 多维度消费分析与理财建议

---

## 📖 快速开始

1. 安装依赖  
   ```bash
   pip install -r requirements.txt
   ```

2. 启动项目  
   ```bash
   python app.py
   ```

3. 浏览器访问  
   ```
   http://localhost:5000
   ```

---

> 如有问题或建议，欢迎 issue 或 PR！