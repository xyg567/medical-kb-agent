# -*- coding: utf-8 -*-
"""生成《第一周作业 · 模块零：医学科研背景与 Agent 基础》Word 文档。"""

import os

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

NAVY = RGBColor(0x1F, 0x38, 0x64)
BLUE = RGBColor(0x2E, 0x5C, 0x8A)
GREY = RGBColor(0x59, 0x59, 0x59)
DARK = RGBColor(0x26, 0x26, 0x26)
ACCENT = "1F3864"
LIGHT = "EDF1F7"
CODEBG = "F4F5F7"

doc = Document()

# ---------------------------------------------------------------- 页面
sec = doc.sections[0]
sec.page_height = Cm(29.7)
sec.page_width = Cm(21.0)
sec.top_margin = Cm(2.3)
sec.bottom_margin = Cm(2.2)
sec.left_margin = Cm(2.4)
sec.right_margin = Cm(2.4)

# ---------------------------------------------------------------- 默认样式
normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(10.5)
normal.font.color.rgb = DARK
normal._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
normal.paragraph_format.line_spacing = 1.5
normal.paragraph_format.space_after = Pt(3)


def _font(run, size=10.5, bold=False, color=DARK, ascii_font="Times New Roman", ea="宋体"):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = ascii_font
    run._element.rPr.rFonts.set(qn("w:eastAsia"), ea)


def _shade(element, fill):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    element.append(shd)


def _bottom_border(paragraph, color=ACCENT, size=8):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(size))
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), color)
    pBdr.append(bottom)
    pPr.append(pBdr)


def h1(text, page_break=False):
    if page_break:
        doc.add_page_break()
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after = Pt(7)
    p.paragraph_format.line_spacing = 1.25
    p.paragraph_format.keep_with_next = True
    _font(p.add_run(text), 15, True, NAVY, "微软雅黑", "微软雅黑")
    _bottom_border(p)
    return p


def h2(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(11)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.keep_with_next = True
    _font(p.add_run(text), 12, True, BLUE, "微软雅黑", "微软雅黑")
    return p


def h3(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.keep_with_next = True
    _font(p.add_run(text), 10.5, True, DARK, "微软雅黑", "微软雅黑")
    return p


def body(text, indent=0.0, space_after=3, first_line=0.0):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.left_indent = Cm(indent)
    if first_line:
        p.paragraph_format.first_line_indent = Cm(first_line)
    # 支持 **加粗** 片段
    parts = text.split("**")
    for i, seg in enumerate(parts):
        if not seg:
            continue
        r = p.add_run(seg)
        _font(r, 10.5, bold=(i % 2 == 1))
    return p


def bullet(text, level=0):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.75 + 0.65 * level)
    p.paragraph_format.first_line_indent = Cm(-0.35)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.45
    mark = "▪ " if level == 0 else "– "
    _font(p.add_run(mark), 10, False, BLUE)
    parts = text.split("**")
    for i, seg in enumerate(parts):
        if not seg:
            continue
        _font(p.add_run(seg), 10.5, bold=(i % 2 == 1))
    return p


def code(text, size=8.6):
    for line in text.strip("\n").split("\n"):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.left_indent = Cm(0.35)
        pPr = p._p.get_or_add_pPr()
        _shade(pPr, CODEBG)
        r = p.add_run(line if line else " ")
        _font(r, size, False, RGBColor(0x1B, 0x1B, 0x1B), "Consolas", "Consolas")


def caption(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(6)
    _font(p.add_run(text), 8.8, False, GREY, "微软雅黑", "微软雅黑")


def table(headers, rows, widths=None, font_size=9.2, header_fill=ACCENT, zebra=True):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    tblPr = t._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)

    hdr = t.rows[0].cells
    for i, text in enumerate(headers):
        cell = hdr[i]
        _shade(cell._tc.get_or_add_tcPr(), header_fill)
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        _font(p.add_run(text), font_size, True, RGBColor(0xFF, 0xFF, 0xFF), "微软雅黑", "微软雅黑")

    for ridx, row in enumerate(rows):
        cells = t.add_row().cells
        for i, text in enumerate(row):
            cell = cells[i]
            cell.text = ""
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2.5)
            p.paragraph_format.space_after = Pt(2.5)
            p.paragraph_format.line_spacing = 1.2
            if i == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            txt = str(text)
            parts = txt.split("**")
            for k, seg in enumerate(parts):
                if not seg:
                    continue
                _font(p.add_run(seg), font_size, bold=(k % 2 == 1), color=DARK)
            if zebra and ridx % 2 == 1:
                _shade(cell._tc.get_or_add_tcPr(), LIGHT)

    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return t


def callout(title, text, fill="F2F6FC", bar=ACCENT):
    t = doc.add_table(rows=1, cols=1)
    t.autofit = False
    cell = t.cell(0, 0)
    cell.width = Cm(16.2)
    tcPr = cell._tc.get_or_add_tcPr()
    _shade(tcPr, fill)
    borders = OxmlElement("w:tcBorders")
    for edge, sz, col in (("left", 24, bar), ("top", 4, fill), ("bottom", 4, fill), ("right", 4, fill)):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(sz))
        el.set(qn("w:color"), col)
        borders.append(el)
    tcPr.append(borders)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(5)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.3
    _font(p.add_run(title), 9.8, True, NAVY, "微软雅黑", "微软雅黑")

    p2 = cell.add_paragraph()
    p2.paragraph_format.space_before = Pt(0)
    p2.paragraph_format.space_after = Pt(5)
    p2.paragraph_format.line_spacing = 1.4
    parts = text.split("**")
    for k, seg in enumerate(parts):
        if not seg:
            continue
        _font(p2.add_run(seg), 9.8, bold=(k % 2 == 1))
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def footer_with_page_number():
    footer = sec.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _font(p.add_run("医学科研智能体培养计划 · 第一周作业（模块零）　　"), 8.5, False, GREY)
    run = p.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)
    _font(run, 8.5, False, GREY)


footer_with_page_number()

# ================================================================ 标题区
p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(6)
p.paragraph_format.space_after = Pt(2)
_font(p.add_run("医学科研智能体 · 培养计划"), 9, True, BLUE, "微软雅黑", "微软雅黑")

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(0)
p.paragraph_format.space_after = Pt(2)
p.paragraph_format.line_spacing = 1.1
_font(p.add_run("第一周作业：模块零"), 26, True, NAVY, "微软雅黑", "微软雅黑")

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(0)
p.paragraph_format.space_after = Pt(10)
p.paragraph_format.line_spacing = 1.25
_font(p.add_run("医学科研背景与 Agent 基础 · 共享基础阶段（全员必修）"), 12, False, BLUE, "微软雅黑", "微软雅黑")

table(
    ["项目", "内容"],
    [
        ["作业周期", "2026-11-05 至 2026-11-11（第 1 周）"],
        ["对应阶段", "第一阶段 / 共享基础 / 模块零（全员必修，与个人模块无关）"],
        ["本周交付", "① 一份学习与方案说明（本文档）　② 一个可运行的最小 Agent demo（代码 + 运行轨迹）"],
        ["验收标准", "能说清四个模块在科研流程中的位置与关系；能调用大模型 API 完成带工具调用的最小 Agent demo"],
        ["对应文件", "week1_module0/（代码工程）　schema/trace.schema.json（统一中间结果格式）"],
    ],
    widths=[3.0, 13.2],
)
caption("表 0　作业基本信息（姓名 / 组别请自行补充在提交版首页）")

# ================================================================ 一
h1("一、第一周到底要做什么")

body("把《学习路线》和《项目规划》两份材料对起来看，结论很明确：**第一周不是写业务模块，而是打通“大模型 + 工具”这条链路**。")
body("培养计划分三个阶段：第一阶段“共享基础”、第二阶段“各模块专项”、第三阶段“联调与交付”。第一阶段里唯一的模块就是**模块零**，标注为“全员必修”，四个模块的同学做的是同一份作业。它只要求两件事：")
bullet("**认知对齐**：说清楚文献检索、统计分析、医疗知识库、科研绘图这四个模块，在真实科研流程里各站在哪一步、彼此怎么衔接；")
bullet("**动手跑通**：调用一个大模型 API，完成一个带工具调用（Function Calling）的最小 Agent demo。")
body("换句话说，本周的产出不是“功能”，而是“能力证明 + 工程地基”。项目规划里写的四个子方向（B-01 文献检索、B-02 科研绘图、B-04 统计分析、B-05 知识库）属于第二阶段，本周不展开，但要知道它们将来长什么样——这正是模块零存在的意义：先看清地图，再挖自己那口井。")

h2("1.1 五项学习内容与本周的对应动作")
table(
    ["学习内容（原文）", "本周实际动作", "本文档中的证据"],
    [
        ["医学科研流程：选题、文献调研、研究设计、数据收集、统计分析、图表呈现、论文写作", "画出七阶段流程图，标出四个模块的落点与依赖关系", "第二章 表 2-1、图 2-1"],
        ["科研智能体定位：LLM + 工具调用的编排；Agent = 规划 + 工具 + 记忆 + 反思", "把四个部件逐一落到代码位置，写出一次完整调用时序", "第三章 表 3-1、3-2"],
        ["LLM 基础：Prompt 工程、结构化输出 JSON、Function Calling、RAG、上下文管理", "用 tools 的 JSON Schema 做结构化输出；用 messages 回灌实现上下文", "第五章 5.5、第六章 6.2"],
        ["Agent 框架选型：LangChain / LlamaIndex / Dify / Coze 或轻量自研", "五方案对比，说明本周为何选自研、什么时候该换框架", "第四章 表 4-1"],
        ["工程基础：Python 环境、Git 协作、API Key 管理、目录规范、统一 JSON 格式", "落地目录树、.gitignore、Key 脱敏、trace schema", "第五章 全部"],
    ],
    widths=[6.6, 6.4, 3.2],
)
caption("表 1　模块零学习内容与本周动作的对应关系")

callout(
    "一句话结论",
    "本周的验收物是两件：一张能讲明白的“科研流程 × 四模块”图，和一个 `python main.py \"…\"` 就能跑出“模型自己决定调工具、拿到结果再回答”的 demo。"
    "没有这两样，后面做模块一会一直卡在“我到底在给谁做工具”这个问题上。",
)

# ================================================================ 二
h1("二、医学科研流程与四个模块的定位", page_break=True)

h2("2.1 七阶段流程：每个阶段的真实动作和常见失败点")
body("教材上的流程图通常只画“选题→文献→设计→数据→统计→成图→写作”，但真正决定一个科研智能体好不好用的，是每个阶段的**失败点**——工具要解决的正是这些失败点，而不是把流程再念一遍。")
table(
    ["阶段", "典型动作", "最常见的失败点", "对应模块"],
    [
        ["① 选题", "从临床痛点/既往文献里找 gap，形成 PICO", "凭印象选题，没查重，做完发现别人已发表", "文献检索（前置）"],
        ["② 文献调研", "检索式构建、去重、纳排筛选、精读、做笔记", "检索式太窄漏文献；去重靠手工；读完就忘", "**模块一 文献检索**"],
        ["③ 研究设计", "确定设计类型、样本量、终点指标、统计方案", "先收数据再想统计，导致无法补救", "模块二 统计（前置介入）"],
        ["④ 数据收集", "问卷/量表、临床数据导出、数据清洗", "量表信效度没验；缺失值随意删除", "模块一 问卷分析"],
        ["⑤ 统计分析", "描述统计、假设检验、回归/生存分析", "正态性不查、多重比较不校正、P 值误读", "**模块二 智能统计分析**"],
        ["⑥ 图表呈现", "主图设计、配色、分辨率、图注", "图是 Excel 默认样式；300dpi 不达标被拒", "**模块四 科研绘图**"],
        ["⑦ 论文写作", "结构化写作、参考文献格式、投稿返修", "引文对不上；图表与正文数字不一致", "模块一（综述）+ 全模块"],
    ],
    widths=[2.0, 4.6, 6.6, 3.4],
)
caption("表 2-1　科研七阶段与失败点（加粗为第一轮优先模块）")

h2("2.2 四个模块不是四个并列的 App")
body("这是模块零最容易被误解的一点。四个模块在流程里是**一条主干 + 一个支撑**的关系，不是四个互相独立的工具：")
bullet("**主干（串联）**：文献检索 → 智能统计 → 科研绘图。前者产出“证据”，中间产出“结论”，后者产出“可发表的表达”。任何一个环节断掉，整条链就不成立。")
bullet("**支撑（旁挂）**：医疗知识库不占流程中的某一步，它给主干上的每一步提供“领域事实校验”——统计时确认指标定义、绘图时确认临床分组含义、写综述时提供指南依据。")
bullet("**所以**：知识库是“被调用者”，不是“第三步”。如果把它当成流程的一步，就会做出一个“什么都能问但什么都答不深”的问答框。")
body("这也解释了项目规划里那句“建议第一轮优先：文献检索 + 医学绘图”——这两个模块分别站在主干的**入口**和**出口**，最容易独立做出可演示的价值，也最容易和别人对接：检索的输出（文献列表 JSON）正好是绘图的输入（CSV/表格），中间不需要等统计模块完工。")

callout(
    "自测题（本周应能脱口而出）",
    "问：为什么先做文献检索和绘图，而不是先做知识库？\n"
    "答：因为入口和出口可以各自独立闭环、且能直接对接；知识库是横向支撑，缺少主干的真实数据时，它的检索质量根本无法评测。",
    fill="FFF7E8",
    bar="C08A2E",
)

h2("2.3 模块之间靠什么对接")
body("第二阶段各做各的，第三阶段要联调，那么接口必须现在就定下来。本周给出的答案是**统一中间结果格式**（见 5.5）：每个模块对外只暴露“输入 JSON → 输出 JSON”，内部用什么框架、什么模型、几个 Agent 都不管。这样四个人的东西拼起来时，编排层只需要认一种结构。")

# ================================================================ 三
h1("三、把 Agent 拆成四个部件")

h2("3.1 四个部件分别是什么")
body("“Agent = 规划 + 工具 + 记忆 + 反思”这句话背下来只要十秒，但每个词都容易被想错。下面这张表左边是常见误解，右边是本周 demo 里的真实落点。")
table(
    ["部件", "常见误解", "实际含义", "本 demo 落点"],
    [
        ["规划 Planning", "以为要写一套复杂的任务分解树", "让模型在每一步决定“下一步做什么、调哪个工具、传什么参数”，本质是一次结构化输出", "llm.py 输出 tool_calls"],
        ["工具 Tools", "以为工具越多越智能", "确定性函数：输入固定则输出固定，可单独测试、可单独失败", "tools.py 的 3 个函数"],
        ["记忆 Memory", "以为必须上向量数据库", "短期记忆就是 messages 列表；长期记忆才是向量库/知识库", "core.py 的 messages"],
        ["反思 Reflection", "以为要模型自我批评三轮", "最低成本的做法：把工具报错原文回灌给模型，让它有机会改参数重试；再加最大步数兜底", "core.py 的 MAX_STEPS + 错误回灌"],
    ],
    widths=[3.0, 4.6, 6.4, 3.4],
)
caption("表 3-1　Agent 四部件的误解与真实落点")

h2("3.2 普通对话和 Agent 的差别")
table(
    ["维度", "普通 LLM 对话", "带工具的 Agent"],
    [
        ["信息来源", "训练语料里的统计规律", "训练语料 + 实时工具返回"],
        ["能不能给事实", "会给，但可能是编的", "关键事实由工具返回，可追溯到接口/文件"],
        ["失败模式", "一本正经地胡说", "工具报错、超时、返回空——可观测、可重试"],
        ["成本", "一次请求一次回答", "一次任务 N 次模型调用 + N 次工具调用"],
        ["调试方式", "改 prompt 看输出", "看 trace：哪一步调了什么、返回了什么、耗时多少"],
        ["适用场景", "写作、改写、头脑风暴", "检索、计算、查库、出图——一切需要“事实”的活"],
    ],
    widths=[2.6, 6.4, 7.2],
)
caption("表 3-2　对话式使用与 Agent 式使用的差别")

h2("3.3 一次 Function Calling 的完整时序")
body("这是模块零必须亲手跑一遍的东西。以本 demo 的一次真实请求为例：")
code(
    """① 用户："检索 PD-1 抑制剂与肠道菌群相关的文献，并算一下 (120-15)/120*100"
② 请求：POST /chat/completions  { messages:[system,user], tools:[3个工具JSON Schema] }
③ 模型返回：content 为空，tool_calls = [pubmed_search{...}, calculator{...}]   ← 规划
④ 本地执行：两个工具各跑一次，得到 {ok, source, records[]} / {ok, value}
⑤ 回灌：把 assistant(tool_calls) 和两条 role=tool 的消息 append 进 messages    ← 记忆
⑥ 再次请求：模型看到工具结果，输出自然语言回答 + 引用编号                    ← 收尾
⑦ 落盘：runs/<run_id>.json 记录 6 个 step 与耗时                            ← 可复盘"""
)
body("注意第③步：模型返回的是**结构化 JSON**，不是“我准备去查一下”这种话。这也是判断一个 demo 到底是不是真 Agent 的最快方法——看它有没有 tool_calls 结构，而不是看它回答得像不像。")

h2("3.4 RAG 和 Agent 是什么关系")
body("这两个词经常被混着用，实际是包含关系：**RAG（检索增强生成）是 Agent 可以调用的一个工具，不是 Agent 的同义词**。RAG 干的事是“先把相关文档捞出来，塞进上下文，再让模型回答”；而 Agent 干的事是“决定什么时候该捞、捞几篇、捞完不够要不要再捞”。")
body("本 demo 的 `pubmed_search` 就是一个最小 RAG 的检索端：它只负责“召回”，没有做向量化（PubMed 本身就是关键词检索）。等到模块一/模块三，把“关键词召回”换成“embedding + 向量库召回 + rerank”，链路结构不变，只是工具内部实现升级——这正是把工具做成独立函数的价值。")

h2("3.5 上下文管理：为什么工具结果一定要回灌")
body("模型没有记忆，它只能看见你这一次请求里发的 messages。所以工具结果必须显式 append 回去，否则模型下一步会“忘了自己刚查过什么”，转而开始编。这是新手最常踩的坑：代码里调了工具，也打印了结果，但没把结果放进 messages，模型回答照样是幻觉。")
body("同时要开始建立成本意识：工具返回的原文越长，后续每次调用都要重复付费。本周的做法是**工具只返回结构化摘要**（标题/期刊/年份/PMID，不含摘要全文），需要全文时再单独取。经验阈值：单次上下文控制在 8k token 以内，超过就摘要或分段。")

h2("3.6 三条可控性底线（写在 system prompt 里）")
bullet("**不许编文献**：需要文献必须调 `pubmed_search`，不许凭记忆写作者和 PMID；")
bullet("**事实与推断分开**：回答里标明哪句来自工具、哪句是模型推断；")
bullet("**失败要显式降级**：工具挂了就写“PubMed 不可用，以下为示例数据”，绝不静默换成假数据冒充真实结果。")

# ================================================================ 四
h1("四、Agent 框架选型：本周为什么选自研")

table(
    ["方案", "上手成本", "可控性", "部署形态", "适合谁", "本周结论"],
    [
        ["LangChain", "中", "中（抽象层厚，出问题要读源码）", "库，嵌入自有服务", "要做复杂链式编排、需要大量现成集成", "第二阶段模块一可考虑"],
        ["LlamaIndex", "中", "中", "库", "以 RAG/文档问答为主", "模块三（知识库）再上"],
        ["Dify", "低", "低（可视化编排，深度定制要改源码）", "独立服务，带 Web UI", "想快速出可演示产品、非纯代码团队", "第三阶段联调时可做统一入口"],
        ["Coze", "极低", "低（平台托管，数据出境需评估）", "SaaS", "做 Demo、验证想法", "不用于本项目的医学数据"],
        ["轻量自研（本周）", "低", "高（每一行都看得见）", "纯 Python 脚本", "要真正理解 Agent 内部机制的人", "**本周采用**"],
    ],
    widths=[3.4, 2.2, 3.6, 3.0, 3.2, 3.0],
)
caption("表 4-1　五类方案对比")

body("结论：第一周选自研，不是因为框架不好，而是因为**这一周的学习目标是“理解”，不是“产出”**。用 150 行写一遍主循环，你会永久记住 tool_calls 长什么样、messages 怎么拼、为什么模型会忘事；直接上 LangChain，这些都会被 `AgentExecutor` 一行包掉，出问题时你不知道该改哪里。")
body("换框架的时机也很清楚：当你要做**多工具路由 + 多轮对话 + 记忆持久化 + 可观测**时，自研的维护成本会超过框架的学习成本，那时候换。模块一实现“检索→筛选→综述生成”这种多步流程时，就是切换点。")

# ================================================================ 五
h1("五、工程基础：可检查的五件事", page_break=True)

h2("5.1 环境：一个模块一个 conda 环境")
code(
    """conda create -n medagent python=3.11 -y
conda activate medagent
pip install -r requirements.txt      # 本周 demo 只用标准库，此文件为后续预留
python -c "import sys; print(sys.version)\""""
)
body("为什么锁 3.11 而不是最新版：医学影像/算法生态（nnUNet、部分 CUDA 轮子）对 3.13 支持滞后，团队统一 3.11 可以少踩一半环境坑。")

h2("5.2 目录规范")
code(
    """week1_module0/
├── main.py                  # 入口：只做参数解析与装配
├── agent/
│   ├── config.py            # 配置与 Key 脱敏
│   ├── llm.py               # 模型接入层（唯一允许出现 API 调用的文件）
│   ├── tools.py             # 工具层（确定性函数，不依赖模型）
│   ├── core.py              # 编排层（Agent 主循环）
│   └── trace.py             # 观测层（运行留痕）
├── data/                    # 输入数据 / 断网 fixture
├── schema/                  # 对外 JSON 契约
├── runs/                    # 运行产物（gitignore）
└── .env.example             # 配置模板（真实 .env 不入库）"""
)
body("分层的判据只有一条：**改需求时你只需要动一层**。换模型只动 llm.py，加工具只动 tools.py，改流程只动 core.py。如果一次改动要横跨三个文件，说明分层错了。")

h2("5.3 Git：分支、提交与自检")
bullet("分支：`feat/module1-search`、`fix/trace-null`，一人一分支，主干保护，合入走 PR；")
bullet("提交信息：`feat: 增加 pubmed 检索工具` / `fix: 修正表达式解析越界` / `docs: 补 README`，一行说清“改了什么”，不要写“update”；")
bullet("提交前自检三问：`.env` 有没有被 `git add`？`runs/` 有没有进版本库？代码里有没有硬编码 Key？")
bullet("`.gitignore` 必须包含：`.env`、`runs/`、`__pycache__/`、`.venv/`。")

h2("5.4 API Key 管理：三种错误做法")
table(
    ["错误做法", "后果", "正确做法"],
    [
        ["写在代码里 `api_key = \"sk-...\"`", "一旦推到 GitHub，几分钟内被扫描盗刷", "只从环境变量/.env 读，代码里出现 Key 视为 bug"],
        ["把 `.env` 提交进仓库", "同上，且历史记录里删不干净", "`.env` 进 .gitignore，只提交 `.env.example`"],
        ["把 Key 发群里共用", "无法定位是谁超的额度，泄露后无法单独吊销", "一人一 Key，按项目建配额，泄露立即吊销重建"],
    ],
    widths=[5.4, 5.4, 5.4],
)
caption("表 5-1　Key 管理的错误与正确做法")
body("本 demo 的做法：`config.py` 只从环境变量读，并对日志输出做脱敏（`sk-1a2b***9f0e`），保证截图和 trace 里不会泄露完整 Key。")

h2("5.5 统一中间结果格式（对外契约）")
body("这是四个模块将来能拼在一起的前提。格式定义在 `schema/trace.schema.json`，一次运行落两个文件：`runs/<run_id>.json`（最终态）和 `.jsonl`（逐步追加，用于流式观察）。")
code(
    """{
  "run_id": "700c4193-...", "mode": "offline", "model": "rule-based-planner",
  "user_query": "检索 PD-1 与肠道菌群的文献，并算 (120-15)/120*100",
  "steps": [
    {"index":0, "type":"llm_call",   "latency_ms":0,    "result_summary":"tool_calls=2"},
    {"index":1, "type":"tool_call",  "name":"pubmed_search", "arguments":{"query":"...","retmax":5}},
    {"index":2, "type":"tool_result","name":"pubmed_search", "ok":true, "result_summary":"pubmed-live", "latency_ms":1603},
    {"index":3, "type":"tool_call",  "name":"calculator", "arguments":{"expression":"(120-15)/120*100"}},
    {"index":4, "type":"tool_result","name":"calculator", "ok":true, "result_summary":"ok", "latency_ms":0},
    {"index":5, "type":"llm_call",   "latency_ms":0,    "result_summary":"tool_calls=0"}
  ],
  "status": "success"
}"""
)
table(
    ["字段", "类型", "为什么要它"],
    [
        ["run_id / started_at / finished_at", "string", "一次运行一个 ID，联调时能对上日志"],
        ["mode / model", "enum / string", "区分在线与离线、区分模型版本，避免“结果不一致”扯皮"],
        ["steps[].type", "enum", "llm_call / tool_call / tool_result / final，前端按类型渲染"],
        ["steps[].name + arguments", "string / object", "复现的最小信息：知道调了什么、传了什么"],
        ["steps[].ok + result_summary", "bool / string", "不存全量结果，只存“成功/失败 + 一句话摘要”，控体积"],
        ["steps[].latency_ms", "integer", "定位慢在哪一步（模型还是工具）"],
        ["status", "enum", "success / max_steps_exceeded / error，失败也要留痕"],
    ],
    widths=[5.2, 2.6, 8.4],
)
caption("表 5-2　trace 字段设计理由")

h2("5.6 可复现：每次运行都留痕")
body("调试 Agent 和调试普通函数最大的区别是：同一个输入，两次运行结果可能不同。所以不能只靠 `print`，必须把每一次运行的完整决策链落盘。本 demo 的 trace 记录了 6 个步骤、每步耗时与工具返回摘要，出问题时可以回答“它到底在第几步走偏了”。")

# ================================================================ 六
h1("六、交付物：最小可运行 Agent demo", page_break=True)

body("工程位于 `week1_module0/`，约 670 行 Python，**零第三方依赖**（只用标准库），保证换台机器 `clone` 下来就能跑。")

h2("6.1 三个工具")
table(
    ["工具", "做什么", "关键设计（也是本周学到的点）"],
    [
        ["pubmed_search", "调 NCBI E-utilities（esearch + esummary）检索文献，返回标题/期刊/年份/作者/PMID", "超时 8 秒；网络失败自动回落本地 fixture，并在返回值标 `source`，防止模型把示例数据当真"],
        ["calculator", "算术求值，用于样本量、百分比等", "用 `ast` 白名单解析，不用 `eval`；已实测拦截 `__import__('os').system(...)` 注入"],
        ["export_csv", "把结构化结果导出 CSV 交给 Excel/R", "`utf-8-sig` 编码，Excel 打开中文不乱码——这是医学团队最常见的“小需求大坑”"],
    ],
    widths=[3.4, 6.6, 6.2],
)
caption("表 6-1　工具清单")

h2("6.2 主循环（核心 25 行）")
code(
    """for step in range(MAX_STEPS):
    reply = llm.complete(messages, TOOL_SPECS)        # ① 规划
    calls = reply["tool_calls"]
    if not calls:                                     # ② 没有工具意图 → 结束
        return reply["content"]
    messages.append({"role": "assistant", "content": reply["content"],
                     "tool_calls": [...]})            # ③ 记忆：把意图写回上下文
    for call in calls:                                # ④ 执行
        payload = tools.call_tool(call["name"], call["arguments"])
        messages.append({"role": "tool", "tool_call_id": call["id"],
                         "content": json.dumps(payload, ensure_ascii=False)})
    # ⑤ 回到循环开头，模型带着工具结果再决策（反思的机会在这里）"""
)
body("这 25 行就是所有 Agent 框架的心脏。LangChain 的 `AgentExecutor`、Dify 的编排引擎，拆开看都是这个循环加上重试、流式、记忆持久化、并发工具调用等外围能力。")

h2("6.3 实测记录")
body("以下为本机真实运行输出（2026-11-05，Windows / Python 3.13，网络可达 NCBI）：")
code(
    """> python main.py --selftest
calculator: {"ok": true, "expression": "(120-15)/120*100", "value": 87.5}
pubmed_search: {"ok": true, "source": "pubmed-live", "count": 3}
export_csv: {"ok": true, "path": "runs/selftest_hits.csv", "rows": 3}
calculator(注入用例): {"ok": false, "error": "ValueError: 不支持的表达式节点：Call"}   ← 注入被拦

> python main.py --offline "检索 PD-1 与肠道菌群的文献，并算一下 (120-15)/120*100"
[模式] offline / rule-based-planner（未调用大模型）
[1] Interaction between drugs and the gut microbiome. — Gut, 2020; PMID: 32409589
[2] Gut microbiome in HCC - Mechanisms, diagnosis and therapy. — J Hepatol, 2020; PMID: 31954488
[3] Exercise-induced microbiota metabolite enhances CD8 T cell antitumor immunity... — Cell, 2025
[4] Gut Microbiota in Cancer Immune Response and Immunotherapy. — Trends Cancer, 2021
[5] The gut microbiome and cancer response to immune checkpoint inhibitors. — J Clin Invest, 2025
计算结果：(120-15)/120*100 = 87.5
status=success"""
)
body("上面 5 条 PMID 是 PubMed 实时返回的真实记录，不是 fixture。这说明工具层是通的；`(120-15)/120*100 = 87.5` 说明计算工具正确；注入用例被拒绝说明安全边界有效。")

h2("6.4 必须说清楚的限制")
table(
    ["限制", "原因", "影响与下一步"],
    [
        ["在线（真实大模型）模式未实测", "本机没有可用 API Key，不能伪造结果", "代码按 OpenAI 规范实现，需填 Key 后自测一次并补截图"],
        ["离线 planner 没有语言能力", "它只是关键词→工具的规则映射", "仅用于证明链路，不代表模型效果；真实回答质量取决于在线模式"],
        ["PubMed 未做重试/限流", "第一周只验证主链路", "NCBI 要求 ≤3 req/s 且带 tool/email 参数，模块一必须补"],
        ["无向量库、无 PDF 解析、无多轮压缩", "属于模块一/模块三范围", "第二周起按模块逐步接入"],
        ["fixture 中 PMID 为 DEMO 编号", "防止把示例数据误当真实文献", "任何对外材料只能引用 live 结果"],
    ],
    widths=[4.8, 5.4, 6.0],
)
caption("表 6-2　已知限制（不掩盖）")

# ================================================================ 七
h1("七、自检：对照验收标准")

table(
    ["模块零验收标准", "我的证据", "自评"],
    [
        ["能说清四个模块在科研流程中的位置与关系", "第二章表 2-1 与 2.2 节“主干 + 支撑”论述；能回答“为什么知识库不是第三步”", "达成"],
        ["能调用大模型 API 完成带工具调用的最小 Agent demo", "第六章 demo：3 工具、6 步 trace、真实 PubMed 返回、注入拦截", "达成（在线模式待补测）"],
        ["掌握 Prompt / 结构化输出 / Function Calling / RAG / 上下文管理", "3.3 时序、3.4 RAG 定位、3.5 上下文回灌与 token 预算", "达成"],
        ["完成 Agent 框架选型判断", "第四章五方案对比与切换时机", "达成"],
        ["工程基础：环境 / Git / Key / 目录 / JSON 契约", "第五章全部，schema 文件已落盘", "达成"],
    ],
    widths=[7.0, 7.4, 2.2],
)
caption("表 7-1　验收自评表")

# ================================================================ 八
h1("八、第二周计划与风险")

body("按项目规划“第一轮优先：文献检索 + 医学绘图”，第二周进入模块一（或模块四）的专项。若我分到文献检索，计划如下：")
table(
    ["时间", "任务", "产出", "验收方式"],
    [
        ["周一–周二", "PubMed E-utilities 规范化封装：检索式构建（MeSH + 布尔）、重试、限流、tool/email 参数", "`search/pubmed.py` + 单元测试", "同一检索式两次运行结果一致"],
        ["周三", "去重与元数据清洗：DOI 归一化、标题相似度、作者/年份对齐", "`dedup.py`", "人工构造 20 条重复样本，去重准确率 100%"],
        ["周四–周五", "PDF 解析 + 分段 + embedding 入库（PyMuPDF + Chroma）", "`index.py` + 本地向量库", "给定 query 能召回正确段落 Top-3"],
        ["周末", "串成“输入研究问题 → 检索 → 筛选 → 带引用综述草稿”的 Agent，复用本周 trace 格式", "可演示 demo + 接口文档", "端到端跑通 3 个真实研究问题"],
    ],
    widths=[2.6, 8.2, 3.4, 3.4],
)
caption("表 8-1　第二周计划（以文献检索模块为例）")

h2("8.1 风险与应对")
table(
    ["风险", "可能性", "应对"],
    [
        ["NCBI 接口限流/封 IP", "中", "加 0.4s 间隔、失败指数退避、缓存已检索结果到本地"],
        ["PDF 全文解析质量差（双栏、公式、表格）", "高", "先用摘要做检索，全文解析作为增强；对解析失败样本单独记录"],
        ["embedding 模型选型纠结", "中", "先用开源 bge-small 跑通，指标（召回率）达标再换大模型"],
        ["四人接口对不齐", "中", "以 trace schema 为准，第二周先交换一次样例 JSON 再各自动手"],
    ],
    widths=[6.4, 2.4, 7.4],
)
caption("表 8-2　第二周风险清单")

# ================================================================ 参考
h1("参考资源")
bullet("PubMed E-utilities 文档：https://www.ncbi.nlm.nih.gov/books/NBK25501/（本周实际使用 esearch / esummary）")
bullet("OpenAI Function Calling 指南：https://platform.openai.com/docs/guides/function-calling（tool_calls 结构以此为准）")
bullet("LangChain / LlamaIndex 官方文档（框架选型的对照依据，第二阶段再深入）")
bullet("《医学科研智能体学习路线（11-12 月份）》内部文档；《医学智能技术研发团队培养与项目任务规划》内部 PPT")

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(14)
_font(p.add_run("附：代码工程 week1_module0/，运行 `python main.py --selftest` 可在无网络、无 Key 的情况下完成自检。"), 9, False, GREY, "微软雅黑", "微软雅黑")

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "第一周作业_模块零_医学科研背景与Agent基础.docx")
doc.save(out)
print("saved:", out)
