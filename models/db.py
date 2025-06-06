import csv
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask import Flask
from models.data import User, Bill

class BillDataBase:
    def __init__(self, app: Flask, db: SQLAlchemy):
        self.app = app
        self.db = db
        with self.app.app_context():
            self.db.create_all()
            
    # 获取用户
    def get_user(self, userinfo):
        if isinstance(userinfo, int):
            # 如果传入的是用户ID
            user = User.query.get(userinfo)
        elif isinstance(userinfo, str):
            user = User.query.filter_by(username=userinfo).first()
        return user
        
    # 添加用户
    def add_user(self, username: str, password: str):
        existing = User.query.filter_by(username=username).first()
        # 如果用户已存在
        if existing:
            return None
        user = User(username=username, password=password)
        self.db.session.add(user)
        self.db.session.commit()
        return user
        
    # 保存账单数据
    def save_bill(self, bill_path, user_id):
        user = User.query.get(user_id)
        encoding = 'utf-8'
        try:
            with open(bill_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if '微信支付账单明细' in first_line:
                    platform = 'wechat'
                else:
                    platform = 'alipay'
        except Exception as e:
            encoding = 'gbk'
            with open(bill_path, 'r', encoding='gbk') as f:
                first_line = f.readline().strip()
                if '微信支付账单明细' in first_line:
                    platform = 'wechat'
                else:
                    platform = 'alipay'
                
        if platform == 'wechat':
            self.import_wechat_csv(bill_path, user,encoding)
        elif platform == 'alipay':
            self.import_alipay_csv(bill_path, user,encoding)
    
    # 按照日期获取用户的账单
    def get_bills(self, user_id, start_date=None, end_date=None):
        query = Bill.query.filter_by(user_id=user_id)
        if start_date:
            query = query.filter(Bill.transaction_time >= start_date)
        if end_date:
            query = query.filter(Bill.transaction_time <= end_date)
        return query.all()
    
    # 获取用户最新的账单日期
    def get_latest_billdate(self, user_id):
        latest_bill = Bill.query.filter_by(user_id=user_id).order_by(Bill.transaction_time.desc()).first()
        if latest_bill:
            return latest_bill.transaction_time
        else:
            return datetime.now()
        
    # 获取用户最早的账单日期
    def get_earliest_billdate(self, user_id):
        earliest_bill = Bill.query.filter_by(user_id=user_id).order_by(Bill.transaction_time.asc()).first()
        if earliest_bill:
            return earliest_bill.transaction_time
        else:
            return datetime.now()
    
    def import_wechat_csv(self, bill_path, user: User,encoding):
        with open(bill_path, 'r', encoding=encoding) as f:
            reader = csv.reader(f)
            # 跳过头部说明行
            while True:
                line = next(reader)
                if line and line[0].startswith('交易时间'):
                    header = line
                    break

            for row in reader:
                if len(row) < 11:  # 跳过空行或分隔行
                    continue
                transaction_time = row[0]
                category = row[1]
                counterparty = row[2]
                product = row[3]
                income_or_expense = row[4]
                amount = row[5].replace('¥', '').replace(',', '').strip()
                payment_method = row[6]
                current_status = row[7]
                transaction_id = row[8]
                merchant_id = row[9]
                remarks = row[10]

                # 跳过中性交易
                if income_or_expense == '/':
                    continue
                
                # 跳过已经存在的交易
                existing = Bill.query.filter_by(transaction_id=transaction_id, user_id=user.id).first()
                if existing:
                    continue
                
                bill = Bill(
                    user_id=user.id,
                    platform='微信',
                    transaction_time=datetime.strptime(transaction_time, "%Y-%m-%d %H:%M:%S"),
                    category=category,
                    counterparty=counterparty,
                    product=product,
                    income_or_expense=income_or_expense,
                    amount=float(amount),
                    payment_method=payment_method,
                    current_status=current_status,
                    transaction_id=transaction_id,
                    merchant_id=merchant_id,
                    remarks=remarks
                )

                self.db.session.add(bill)
            self.db.session.commit()
            
    def import_alipay_csv(self, bill_path, user: User,encoding):
        with open(bill_path, 'r', encoding=encoding) as f:
            reader = csv.reader(f)
            # 跳过头部说明行
            while True:
                line = next(reader)
                if line and line[0].startswith('交易时间'):
                    header = line
                    break            

            for row in reader:
                if len(row) < 12:
                    continue
                transaction_time = row[0]
                category = row[1]
                counterparty = row[2]
                # row[3]：对方账号
                product = row[4]
                income_or_expense = row[5]
                amount_str = row[6].replace(',', '').strip()
                payment_method = row[7]
                current_status = row[8]
                transaction_id = row[9]
                merchant_id = row[10]
                remarks = row[11]

                # 跳过中性交易
                if income_or_expense == '/':
                    continue
                
                # 跳过已经存在的交易
                existing = Bill.query.filter_by(transaction_id=transaction_id, user_id=user.id).first()
                if existing:
                    continue
                
                bill = Bill(
                    user_id=user.id,
                    platform='支付宝',
                    transaction_time=datetime.strptime(transaction_time, "%Y-%m-%d %H:%M:%S"),
                    category=category,
                    counterparty=counterparty,
                    product=product,
                    income_or_expense=income_or_expense,
                    amount=float(amount_str),
                    payment_method=payment_method,
                    current_status=current_status,
                    transaction_id=transaction_id,
                    merchant_id=merchant_id,
                    remarks=remarks
                )
                self.db.session.add(bill)
            self.db.session.commit()
            
    def show_tables(self):
        with self.app.app_context():
            users = User.query.all()
            bills = Bill.query.all()
            print("Users:")
            for user in users:
                print(user)
            print("\nBills:")
            for bill in bills:
                print(bill)

    def get_bill_table_data(self, user_id, start_date=None, end_date=None):
        """
        查询账单明细，返回适合表格渲染的 data 字典
        """
        query = Bill.query.filter_by(user_id=user_id)
        if start_date:
            query = query.filter(Bill.transaction_time >= start_date)
        if end_date:
            query = query.filter(Bill.transaction_time <= end_date)
        bills = query.order_by(Bill.transaction_time.desc()).all()

        data = {}
        for idx, bill in enumerate(bills, 1):
            data[idx] = [
                idx,  # 序号
                bill.platform,
                bill.transaction_time.strftime("%Y-%m-%d %H:%M:%S") if bill.transaction_time else "",
                bill.category or "",
                bill.product or "",
                bill.counterparty or "",
                bill.income_or_expense or "",
                bill.amount,
                bill.payment_method or "",
                bill.current_status or ""
            ]
        return data
    
    def get_expend_classification_pie_data(self, user_id, start_date=None, end_date=None):
        """
        获取支出分类饼图数据
        """
        query = Bill.query.filter_by(user_id=user_id, income_or_expense='支出')
        if start_date:
            query = query.filter(Bill.transaction_time >= start_date)
        if end_date:
            query = query.filter(Bill.transaction_time <= end_date)
        
        results = query.with_entities(
            Bill.category,
            func.sum(Bill.amount).label('total_amount')
        ).group_by(Bill.category).all()
        
        dict = {category: total_amount for category, total_amount in results}
        data = [{"value": round(v, 2), "name": k} for k, v in dict.items()]
        return data
    
    def get_last_week_expend_bar_data(self, user_id):
        today = datetime.now()
        last_week_start = today - timedelta(days=6)
        bills = self.get_bills(user_id, start_date=last_week_start, end_date=today)
        # 只统计支出
        expend_bills = [bill for bill in bills if hasattr(bill, "income_or_expense") and bill.income_or_expense == "支出"]
        # 初始化每天的金额为0，key为"MM-DD"
        date_list = [(last_week_start + timedelta(days=i)).strftime("%m-%d") for i in range(7)]
        date_amount = {d: 0.0 for d in date_list}
        for bill in expend_bills:
            day = bill.transaction_time.strftime("%m-%d")
            if day in date_amount:
                date_amount[day] += bill.amount
        dates = list(date_amount.keys())
        counts = [round(v, 2) for v in date_amount.values()]
        return {"date": dates, "counts": counts}

    def get_highest_expend(self, user_id, start_date=None, end_date=None):
        """
        获取最高支出数值（保留2位小数，字符串类型）
        """
        query = Bill.query.filter_by(user_id=user_id, income_or_expense='支出')
        if start_date:
            query = query.filter(Bill.transaction_time >= start_date)
        if end_date:
            query = query.filter(Bill.transaction_time <= end_date)
        
        result = query.order_by(Bill.amount.desc()).first()
        if result:
            return f"{result.amount:.2f}"
        else:
            return "0.00"
        
    def get_highest_expend_bill(self, user_id):
        """
        获取最高支出账单
        """
        bill = Bill.query.filter_by(user_id=user_id, income_or_expense='支出').order_by(Bill.amount.desc()).first()
        if bill:
            return {
                "商品名称": bill.product or "",
                "交易金额": f"{bill.amount:.2f}",
                "对方名称": bill.counterparty or "",
            }
        else:
            return {
                "商品名称": "",
                "交易金额": "0.00",
                "对方名称": "",
            }
            
    def get_highest_income_bill(self, user_id):
        """
        获取最高收入账单
        """
        bill = Bill.query.filter_by(user_id=user_id, income_or_expense='收入').order_by(Bill.amount.desc()).first()
        if bill:
            return {
                "商品名称": bill.product or "",
                "交易金额": f"{bill.amount:.2f}",
                "对方名称": bill.counterparty or "",
            }
        else:
            return {
                "商品名称": "",
                "交易金额": "0.00",
                "对方名称": "",
            }
            
    def get_highest_income(self, user_id, start_date=None, end_date=None):
        """
        获取最高收入数值（保留2位小数，字符串类型）
        """
        query = Bill.query.filter_by(user_id=user_id, income_or_expense='收入')
        if start_date:
            query = query.filter(Bill.transaction_time >= start_date)
        if end_date:
            query = query.filter(Bill.transaction_time <= end_date)
        
        result = query.order_by(Bill.amount.desc()).first()
        if result:
            return f"{result.amount:.2f}"
        else:
            return "0.00"
        
    def get_total_expend(self, user_id, start_date=None, end_date=None):
        """
        获取总支出，保留2位小数，返回字符串
        """
        query = Bill.query.filter_by(user_id=user_id, income_or_expense='支出')
        if start_date:
            query = query.filter(Bill.transaction_time >= start_date)
        if end_date:
            query = query.filter(Bill.transaction_time <= end_date)
        
        total = query.with_entities(func.sum(Bill.amount)).scalar() or 0
        return f"{total:.2f}"
    
    def get_total_income(self, user_id, start_date=None, end_date=None):
        """
        获取总收入
        """
        query = Bill.query.filter_by(user_id=user_id, income_or_expense='收入')
        if start_date:
            query = query.filter(Bill.transaction_time >= start_date)
        if end_date:
            query = query.filter(Bill.transaction_time <= end_date)
        
        total = query.with_entities(func.sum(Bill.amount)).scalar() or 0
        return f"{total:.2f}"
    
    def get_highest_lowest_week_expend_income(self, user_id):
        """
        获取周支出综合最高的一周和最低的一周，所有金额保留两位小数
        """     
        # 查询所有支出账单
        bills = self.get_bills(user_id)
        expend_bills = [bill for bill in bills if hasattr(bill, "income_or_expense") and bill.income_or_expense == "支出"]
        week_days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        if not expend_bills:
            empty = {d: 0.0 for d in week_days}
            return {
                "highest": {"week_start": "", "days": empty.copy()},
                "lowest": {"week_start": "", "days": empty.copy()}
            }

        # 按自然周分组
        week_map = {}
        for bill in expend_bills:
            dt = bill.transaction_time
            # 找到该账单所在周的周一日期
            monday = dt - timedelta(days=dt.weekday())
            week_start_str = monday.strftime("%Y-%m-%d")
            if week_start_str not in week_map:
                week_map[week_start_str] = {d: 0.0 for d in week_days}
            week_map[week_start_str][week_days[dt.weekday()]] += bill.amount

        # 计算每周总额
        week_sums = {k: sum(v.values()) for k, v in week_map.items()}
        if not week_sums:
            empty = {d: 0.0 for d in week_days}
            return {
                "highest": {"week_start": "", "days": empty.copy()},
                "lowest": {"week_start": "", "days": empty.copy()}
            }
        # 找到最大和最小周
        highest_week = max(week_sums, key=week_sums.get)
        lowest_week = min(week_sums, key=week_sums.get)

        # 金额保留两位小数
        def round_dict(d):
            return {k: round(v, 2) for k, v in d.items()}

        return {
            "highest": {"week_start": highest_week, "days": round_dict(week_map[highest_week])},
            "lowest": {"week_start": lowest_week, "days": round_dict(week_map[lowest_week])}
        }  
        
    def get_top10_expend_bill(self, user_id):
        """
        获取支出金额前10的账单
        """
        bills = Bill.query.filter_by(user_id=user_id, income_or_expense='支出').order_by(Bill.amount.desc()).limit(10).all()
        top10 = []
        for bill in bills:
            top10.append({
                "序号": len(top10) + 1,
                "商品名称": bill.product or "",
                "交易金额": f"{bill.amount:.2f}",
                "交易时间": bill.transaction_time.strftime("%Y-%m-%d %H:%M:%S") if bill.transaction_time else "",
                "交易状态": bill.current_status or "",
                "支付方式": bill.payment_method or "",              
            })
        return top10
        
    def get_last_two_week_expend(self, user_id):
        """
        获取最近两周的支出数据，返回账单金额和对应日期
        """
        today = datetime.now()
        two_weeks_ago_start = today - timedelta(days=13)
        
        bills = self.get_bills(user_id, start_date=two_weeks_ago_start, end_date=today)
        expend_bills = [bill for bill in bills if hasattr(bill, "income_or_expense") and bill.income_or_expense == "支出"]
        
        if not expend_bills:
            return []
        expend_bills.sort(key=lambda bill: bill.transaction_time)

        result = []
        for bill in expend_bills:
            result.append({
                "消费时间": bill.transaction_time.strftime("%Y-%m-%d %H:%M:%S"),
                "商品名称": bill.product or "",
                "消费金额": float(bill.amount)
            })
        return result
    
    def get_last_half_year_expend(self, user_id):
        """
        获取最近半年每月前五类支出数据，每类每月的消费金额
        """
        today = datetime.now()
        six_months_ago = today - timedelta(days=180)
        
        bills = self.get_bills(user_id, start_date=six_months_ago, end_date=today)
        expend_bills = [bill for bill in bills if hasattr(bill, "income_or_expense") and bill.income_or_expense == "支出"]
        
        if not expend_bills:
            return []
        
        # 统计半年内所有分类总金额，取前五类
        category_sum = {}
        for bill in expend_bills:
            cat = bill.category or "其他"
            category_sum[cat] = category_sum.get(cat, 0) + bill.amount
        top5_cats = [k for k, v in sorted(category_sum.items(), key=lambda x: x[1], reverse=True)[:5]]

        # 统计每月每类金额
        month_cat_sum = {}
        for bill in expend_bills:
            month = bill.transaction_time.strftime("%Y-%m")
            cat = bill.category or "其他"
            if cat not in top5_cats:
                continue
            key = (month, cat)
            month_cat_sum[key] = month_cat_sum.get(key, 0) + bill.amount

        # 补全每个月每类（无则为0）
        months = set(bill.transaction_time.strftime("%Y-%m") for bill in expend_bills)
        result = []
        for month in sorted(months):
            for cat in top5_cats:
                amount = round(month_cat_sum.get((month, cat), 0), 2)
                result.append({
                    "月份": month,
                    "分类": cat,
                    "金额": amount
                })
        return result
    
    def get_last20_weeks_expend_income(self, user_id):
        """
        获取最近10周（从上周开始，不含本周）的每日净收入数据（收入-支出）
        """
        today = datetime.now()
        # 找到本周一
        this_monday = today - timedelta(days=today.weekday())
        # 上周一
        last_monday = this_monday - timedelta(weeks=1)
        # 20周前的周一（不含本周，含上周）
        start_monday = last_monday - timedelta(weeks=19)
        # 查询所有账单
        bills = self.get_bills(user_id, start_date=start_monday, end_date=last_monday + timedelta(days=6))
        week_days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        # 初始化数据结构
        week_data = []
        for week in range(20):
            monday = last_monday - timedelta(weeks=week)
            for i, day_name in enumerate(week_days):
                date = monday + timedelta(days=i)
                week_data.append({
                    "周序": week + 1,
                    "日期": date.strftime("%Y-%m-%d"),
                    "星期": day_name,
                    "收入": 0.0,
                    "支出": 0.0
                })

        # 构建日期到记录的映射
        date_map = {item["日期"]: item for item in week_data}

        # 累加账单
        for bill in bills:
            date_str = bill.transaction_time.strftime("%Y-%m-%d")
            if date_str in date_map:
                if hasattr(bill, "income_or_expense"):
                    if bill.income_or_expense == "支出":
                        date_map[date_str]["支出"] += float(bill.amount)
                    elif bill.income_or_expense == "收入":
                        date_map[date_str]["收入"] += float(bill.amount)

        # 计算净收入并保留两位小数
        result = []
        for item in week_data:
            net = round(item["收入"] - item["支出"], 2)
            result.append({
                "周序": item["周序"],
                "星期": item["星期"],
                "日期": item["日期"],
                "收支": net
            })

        # 按周序从1到20、周一到周日排序
        result.sort(key=lambda x: (x["周序"], week_days.index(x["星期"])))
        return result
    
    def get_all_year_monthly_expend_income(self, user_id):
        """
        获取最近一年的每月收支数据：
        从上个月往前推11个月，共12个月
        """
        today = datetime.now()
        # 获取上个月的最后一天
        first_day_this_month = today.replace(day=1)
        last_month_end = first_day_this_month - timedelta(days=1)

        # 获取12个月的起始时间
        start_date = (last_month_end.replace(day=1) - relativedelta(months=11))
        end_date = last_month_end.replace(hour=23, minute=59, second=59)

        # 获取账单
        bills = self.get_bills(user_id, start_date=start_date, end_date=end_date)

        # 初始化12个月份
        month_data = {}
        for i in range(12):
            month = (start_date + relativedelta(months=i)).strftime("%Y-%m")
            month_data[month] = {"收入": 0.0, "支出": 0.0}

        # 填充账单数据
        for bill in bills:
            month = bill.transaction_time.strftime("%Y-%m")
            if month in month_data:
                if hasattr(bill, "income_or_expense"):
                    if bill.income_or_expense == "支出":
                        month_data[month]["支出"] += float(bill.amount)
                    elif bill.income_or_expense == "收入":
                        month_data[month]["收入"] += float(bill.amount)

        # 整理结果
        result = []
        for month in sorted(month_data.keys()):
            data = month_data[month]
            result.append({
                "月份": month,
                "收入": round(data["收入"], 2),
                "支出": round(data["支出"], 2),
            })

        return result
    
    def get_sankey_data(self, user_id):
        """
        获取桑基图数据
        """
        bills = self.get_bills(user_id)
        if not bills:
            return {"nodes": [], "links": []}
        links = []

        for bill in bills:
            if not hasattr(bill, "income_or_expense"):
                continue
            # 来源节点
            if bill.income_or_expense == "收入":
                if bill.counterparty == "/":
                    source = "其他收入"
                else:
                    source = bill.counterparty or "其他收入"
                target = "账户"
                type = "income"
            elif bill.income_or_expense == "支出":
                source = "账户"
                if bill.counterparty == "/":
                    target = "其他支出"
                else:
                    target = (bill.category or "其他支出")
                type = "expense"
            else:
                continue

            links.append({
                "source": source,
                "target": target,
                "value": round(bill.amount, 2),
                "type": type
            })
                
        # 累加相同的 source、target、type 的 links
        links = merge_links(links)
        # 处理小额交易
        for link in links:
            if link["type"] == "expense" and link["value"] < 100:
                link["target"] = "其他"
            elif link["type"] == "income" and link["value"] < 50:
                link["source"] = "其他收入"
        links = merge_links(links)
        
        # 构建节点列表
        node_set = set()
        for link in links:
            node_set.add(link["source"])
            node_set.add(link["target"])
        node_list = [{"name": name} for name in node_set]
        
        return {
            "nodes": node_list,
            "links": links
        }


    def get_year_report_data(self, user_id):
        """
        获取指定年份的年度报告数据，适合AI生成总结
        """
        year = datetime.now().year
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)

        # 总收入、总支出
        total_income = self.get_total_income(user_id, start_date, end_date)
        total_expend = self.get_total_expend(user_id, start_date, end_date)

        # 月度收支
        bills = self.get_bills(user_id, start_date, end_date)
        month_data = {}
        for bill in bills:
            month = bill.transaction_time.strftime("%Y-%m")
            if month not in month_data:
                month_data[month] = {"收入": 0.0, "支出": 0.0}
            if hasattr(bill, "income_or_expense"):
                if bill.income_or_expense == "支出":
                    month_data[month]["支出"] += float(bill.amount)
                elif bill.income_or_expense == "收入":
                    month_data[month]["收入"] += float(bill.amount)
        monthly = []
        for month, data in sorted(month_data.items()):
            monthly.append({
                "月份": month,
                "收入": round(data["收入"], 2),
                "支出": round(data["支出"], 2),
            })

        # 分类支出
        expend_class = self.get_expend_classification_pie_data(user_id, start_date, end_date)

        # 最大支出/收入账单
        max_expend = self.get_highest_expend_bill(user_id)
        max_income = self.get_highest_income_bill(user_id)

        # 最高/最低消费周
        week_stat = self.get_highest_lowest_week_expend_income(user_id)
        highest_week = week_stat.get("highest", {})
        lowest_week = week_stat.get("lowest", {})

        # 支出前10账单
        top10_expend = self.get_top10_expend_bill(user_id)

        return {
            "总收入": total_income,
            "总支出": total_expend,
            "月度收支": monthly,
            "分类支出": expend_class,
            "最大支出账单": max_expend,
            "最大收入账单": max_income,
            "最高消费周": highest_week,
            "最低消费周": lowest_week,
            "支出前10账单": top10_expend
        }
    
def merge_links(links):
    """
    合并相同 source 、 target、type 的 links
    """
    merged = {}
    for link in links:
        key = (link['source'], link['target'],link['type'])
        if key not in merged:
            merged[key] = link.copy()
        else:
            merged[key]['value'] += link['value']
    return list(merged.values())