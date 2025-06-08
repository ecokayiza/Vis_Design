from openai import OpenAI

SYSTEM_COMMAND = ("你是一个专业的财务分析师，擅长从年度账单数据中提取关键信息并生成总结.所有换行请使用`<br>`\n"
                    )
PROMPT = (
    "请根据以下年度账单数据，生成一段结构化且细致的年度总结，要求如下：\n"
    # "1. 先用一段话简要概述整体收支、结余及同比变化。\n"
    # "2. 用分点或小标题详细分析：\n"
    # "   - 主要收入来源及占比，按月趋势变化。\n"
    # "   - 主要支出类别及占比，按月趋势变化。\n"
    # "   - 最大/最小单笔收入与支出及其时间、类别。\n"
    # "   - 月度收支波动、异常月份及可能原因。\n"
    # "   - 现金流状况、储蓄率、投资与消费比例。\n"
    # "3. 结尾给出针对性理财建议。\n"
    # "请根据以下年度账单数据，生成一段简洁有洞察力的年度总结，要求：\n"
    "1. 先简要概述整体收支情况。\n"
    "2. 用分点或小标题详细说明主要消费类别、月度趋势、最大/最小收支等亮点。\n"
    "3. 结尾给出理财建议。\n"
    "输出请使用Markdown格式，请严格遵守Markdown格式，开头不要输出```和markdown等多余内容。\n"
    "所有标题、段落、列表项都要单独一行，且标题、段落、列表之间用空行分隔，禁止将多个标题或内容写在同一行。\n"
    "所有有序列表如（"
    "`<br>`1. 内容`<br>`"
    "`<br>`2. 内容`<br>`"
    "`<br>`3. 内容`<br>` ）"
    "每一项都要单独一行，并且前后用空行分隔，禁止将多个序号内容写在同一行。\n"
    "所有标题的#后面都要有空格，前面都要有换行，标题结束后必须有换行,如`<br>`# 一级标题`<br>`,`<br>`## 二级标题`<br>`，`<br>`### 三级标题`<br>`\n"
    "说有数字不要使用逗号分隔符，直接使用数字，如[1000]，不要使用[1,000]。\n"
    "请注意，输出的内容需要有逻辑性和条理性，不能只是简单的数字罗列。\n"
    "账单数据如下：\n"
)
    # "请根据以下年度账单数据，生成一段简洁有洞察力的年度总结，要求：\n"
    # "1. 先简要概述整体收支情况。\n"
    # "2. 用分点或小标题详细说明主要消费类别、月度趋势、最大/最小收支等亮点。\n"
    # "3. 结尾给出理财建议。\n"
class AIClient:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key,base_url="https://api.deepseek.com")

    def generate_summary_stream(self, user_id, year_report_data):
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": f"{SYSTEM_COMMAND}"},
                {"role": "user", "content": f"{PROMPT}\n{year_report_data}"}
            ],
            max_tokens=2000,
            stream=True,
            
        )
        
        for chunk in response:
            if hasattr(chunk, "choices"):
                delta = chunk.choices[0].delta
                if hasattr(delta, "content") and delta.content:
                    yield delta.content