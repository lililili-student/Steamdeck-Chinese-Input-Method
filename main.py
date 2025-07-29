import tkinter as tk
from tkinter import ttk, font
import re
from collections import defaultdict
import json
import os

class ChineseInputMethod:
    def load_word_dict(self):


        with open('dictionary.json', 'r', encoding='utf-8') as file:
            dictionary = json.load(file)

        return dictionary


    def __init__(self, root):

        self.root = root
        root.title("中文输入法")
        root.geometry("500x400")
        self.root.configure(bg="#f0f0f0")
        self.load_user_dict()
        # 加载词库和用户词典
        self.word_dict = self.load_word_dict()
        self.user_dict = defaultdict(list)
        self.load_word_dict()

        # 创建样式
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TButton", padding=3, font=("微软雅黑", 10))
        self.style.configure("Candidate.TButton", background="#e6f3ff", borderwidth=1)
        self.style.map("Candidate.TButton",
                      background=[('active', '#cce5ff')])

        # 创建输出框（显示最终结果）
        output_frame = ttk.Frame(root, padding=(10, 10, 10, 5))
        output_frame.pack(fill=tk.X)

        self.output_var = tk.StringVar()
        self.output_entry = ttk.Entry(
            output_frame,
            textvariable=self.output_var,
            width=50,
            font=("微软雅黑", 12),
            state='readonly'
        )
        self.output_entry.pack(fill=tk.X)

        # 创建输入框
        input_frame = ttk.Frame(root, padding=(10, 5, 10, 10))
        input_frame.pack(fill=tk.X)

        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(
            input_frame,
            textvariable=self.input_var,
            width=30,
            font=("微软雅黑", 12)
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input_entry.bind("<KeyRelease>", self.on_input_change)
        self.input_entry.focus_set()

        # 添加功能按钮
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="←", width=3, command=self.backspace).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="加载字典", width=3, command=self.clear_input).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="清空", width=3, command=self.commit_space).pack(side=tk.LEFT)


        # 创建候选词区域
        self.candidate_frame = ttk.LabelFrame(
            root,
            text="候选词",
            padding=10
        )
        self.candidate_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        self.candidate_buttons = []
        self.candidates = []
        self.current_page = 0
        self.pages = 0

        # 状态栏
        self.status_var = tk.StringVar(value="就绪 | 拼音输入")
        status_bar = ttk.Label(
            root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(5, 2)
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 绑定键盘事件
        self.root.bind("<Escape>", lambda e: self.clear_input())
        self.root.bind("<Return>", lambda e: self.commit_input())
        self.root.bind("<space>", lambda e: self.select_first_candidate())

        # 绑定数字键选择候选词
        for i in range(1, 10):
            self.root.bind(str(i), lambda e, i=i: self.select_candidate_by_index(i-1))



    def load_user_dict(self):
        # 在实际应用中可以从文件加载用户词典
        self.user_dict = defaultdict(list)
        # 添加一些常用词
        self.add_to_user_dict("中国", "zhong guo")
        self.add_to_user_dict("人民", "ren min")
        self.add_to_user_dict("工作", "gong zuo")
        self.add_to_user_dict("今天", "jin tian")
        self.add_to_user_dict("明天", "ming tian")
        self.add_to_user_dict("输入法", "shu ru fa")

    def add_to_user_dict(self, word, pinyin):
        """添加词语到用户词典"""
        self.user_dict[pinyin].append(word)
        # 在实际应用中，这里应该保存到文件

    def on_input_change(self, event):
        # 忽略功能键
        if event.keysym in ["BackSpace", "Return", "Escape", "space"]:
            return

        input_text = self.input_var.get().lower()

        # 清除旧候选词按钮
        for btn in self.candidate_buttons:
            btn.destroy()
        self.candidate_buttons = []
        self.candidates = []

        if input_text:
            # 获取候选词
            self.candidates = self.get_candidates(input_text)
            self.current_page = 0
            self.pages = (len(self.candidates) + 8) // 9  # 每页9个候选词
            self.update_candidate_display()
        else:
            # 显示历史输入或常用词
            self.show_history_or_common()

    def show_history_or_common(self):
        """显示历史输入或常用词"""
        # 在实际应用中可以从文件加载历史记录
        history = ["中国", "人民", "工作", "今天", "输入法", "计算机", "学习", "开发", "程序"]

        for i, word in enumerate(history[:9]):
            btn = ttk.Button(
                self.candidate_frame,
                text=f"{i+1}.{word}",
                style="Candidate.TButton",
                command=lambda w=word: self.select_word(w)
            )
            btn.grid(row=i//3, column=i%3, padx=5, pady=5, sticky="nsew")
            self.candidate_buttons.append(btn)

        # 添加提示
        self.status_var.set(f"就绪 | 输入拼音或选择历史词")

    def get_candidates(self, pinyin_str):
        """获取候选词列表"""
        candidates = []

        # 1. 首先检查用户词典（优先级最高）
        if pinyin_str in self.user_dict:
            candidates.extend(self.user_dict[pinyin_str])

        # 2. 检查完整拼音匹配
        if pinyin_str in self.word_dict:
            candidates.extend(self.word_dict[pinyin_str])

        # 3. 智能分词匹配
        word_combinations = self.smart_pinyin_split(pinyin_str)
        for combination in word_combinations:
            candidates.append(combination)

        # 4. 添加拼音本身作为备选
        candidates.append(pinyin_str)

        # 去重并限制数量
        unique_candidates = []
        for c in candidates:
            if c not in unique_candidates:
                unique_candidates.append(c)

        return unique_candidates[:50]  # 最多50个候选词

    def smart_pinyin_split(self, pinyin):
        """智能拼音分词算法"""
        results = []

        # 简单分词：尝试常见分割点
        common_splits = self.find_common_splits(pinyin)
        for words in common_splits:
            results.append("".join(words))

        # 最大匹配算法
        max_match = self.maximum_matching(pinyin)
        if max_match:
            results.append("".join(max_match))

        # 按音节分割
        syllable_split = self.split_by_syllables(pinyin)
        if syllable_split:
            results.append("".join(syllable_split))

        return results

    def find_common_splits(self, pinyin):
        """查找常见的分割点"""
        results = []

        # 常见双音节词分割
        for i in range(1, min(6, len(pinyin))):
            part1 = pinyin[:i]
            part2 = pinyin[i:]

            if part1 in self.word_dict and part2 in self.word_dict:
                for w1 in self.word_dict[part1]:
                    for w2 in self.word_dict[part2]:
                        results.append([w1, w2])

        # 常见三音节词分割
        if len(pinyin) > 4:
            for i in range(1, len(pinyin)-2):
                for j in range(i+1, len(pinyin)):
                    part1 = pinyin[:i]
                    part2 = pinyin[i:j]
                    part3 = pinyin[j:]

                    if (part1 in self.word_dict and
                        part2 in self.word_dict and
                        part3 in self.word_dict):
                        for w1 in self.word_dict[part1]:
                            for w2 in self.word_dict[part2]:
                                for w3 in self.word_dict[part3]:
                                    results.append([w1, w2, w3])

        return results

    def maximum_matching(self, pinyin):
        """最大匹配算法"""
        words = []
        start = 0
        n = len(pinyin)

        while start < n:
            found = False
            # 从最长可能匹配开始（最多6个字母）
            for end in range(min(start+6, n), start, -1):
                syllable = pinyin[start:end]
                if syllable in self.word_dict:
                    words.append(self.word_dict[syllable][0])  # 取第一个候选词
                    start = end
                    found = True
                    break

            if not found:
                # 没有匹配，按单个字符处理
                words.append(pinyin[start])
                start += 1

        return words

    def split_by_syllables(self, pinyin):
        """按音节分割"""
        # 简单实现：按常见韵母分割
        vowels = ["a", "o", "e", "i", "u", "v", "ai", "ei", "ui", "ao", "ou", "iu",
                 "ie", "ve", "er", "an", "en", "in", "un", "ang", "eng", "ing", "ong"]

        words = []
        start = 0
        n = len(pinyin)

        while start < n:
            found = False
            # 尝试匹配韵母
            for v in sorted(vowels, key=len, reverse=True):
                if pinyin.startswith(v, start):
                    # 检查前面是否有声母
                    if start > 0 and pinyin[start-1] in "bpmfdtnlgkhjqxzhchshrzcsyw":
                        words.append(pinyin[start-1:start+len(v)])
                        start += len(v) + 1
                    else:
                        words.append(pinyin[start:start+len(v)])
                        start += len(v)
                    found = True
                    break

            if not found:
                words.append(pinyin[start])
                start += 1

        # 查找每个音节对应的汉字
        result = []
        for syllable in words:
            if syllable in self.word_dict:
                result.append(self.word_dict[syllable][0])
            else:
                result.append(syllable)

        return result

    def update_candidate_display(self):
        """更新候选词显示"""
        for btn in self.candidate_buttons:
            btn.destroy()
        self.candidate_buttons = []

        if not self.candidates:
            label = ttk.Label(
                self.candidate_frame,
                text="无匹配结果",
                foreground="gray"
            )
            label.grid(row=0, column=0, columnspan=3, padx=5, pady=20)
            self.candidate_buttons.append(label)
            return

        # 显示当前页的候选词
        start_idx = self.current_page * 9
        end_idx = min(start_idx + 9, len(self.candidates))
        page_candidates = self.candidates[start_idx:end_idx]

        for i, word in enumerate(page_candidates):
            btn = ttk.Button(
                self.candidate_frame,
                text=f"{i+1}.{word}",
                style="Candidate.TButton",
                command=lambda w=word: self.select_word(w)
            )
            btn.grid(row=i//3, column=i%3, padx=5, pady=5, sticky="nsew")
            self.candidate_buttons.append(btn)

        # 添加翻页按钮
        if self.pages > 1:
            page_frame = ttk.Frame(self.candidate_frame)
            page_frame.grid(row=3, column=0, columnspan=3, pady=(10, 0))

            if self.current_page > 0:
                prev_btn = ttk.Button(
                    page_frame,
                    text="< 上一页",
                    command=self.prev_page
                )
                prev_btn.pack(side=tk.LEFT, padx=5)

            page_label = ttk.Label(
                page_frame,
                text=f"{self.current_page+1}/{self.pages}",
                foreground="gray"
            )
            page_label.pack(side=tk.LEFT, padx=5)

            if self.current_page < self.pages - 1:
                next_btn = ttk.Button(
                    page_frame,
                    text="下一页 >",
                    command=self.next_page
                )
                next_btn.pack(side=tk.LEFT, padx=5)

        # 更新状态栏
        self.status_var.set(f"找到 {len(self.candidates)} 个候选词 | 第 {self.current_page+1}/{self.pages} 页")

    def next_page(self):
        """显示下一页候选词"""
        if self.current_page < self.pages - 1:
            self.current_page += 1
            self.update_candidate_display()

    def prev_page(self):
        """显示上一页候选词"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_candidate_display()

    def select_candidate_by_index(self, index):
        """通过数字键选择候选词"""
        start_idx = self.current_page * 9
        actual_index = start_idx + index

        if actual_index < len(self.candidates):
            self.select_word(self.candidates[actual_index])

    def select_first_candidate(self):
        """选择第一个候选词（空格键）"""
        if self.candidates:
            self.select_word(self.candidates[0])

    def select_word(self, word):
        """选择候选词"""
        current_output = self.output_var.get()
        self.output_var.set(current_output + word)

        # 添加到用户词典（实际应用中需要更智能的方式）
        if len(word) > 1 and self.input_var.get():
            self.add_to_user_dict(word, self.input_var.get())

        self.input_var.set("")
        self.input_entry.focus()

        # 清除候选词
        for btn in self.candidate_buttons:
            btn.destroy()
        self.candidate_buttons = []
        self.candidates = []

        # 更新状态栏
        self.status_var.set(f"已选择: {word} | 继续输入拼音")

    def backspace(self):
        """删除输入或输出内容"""
        if self.input_var.get():
            # 删除输入框内容
            current = self.input_var.get()
            self.input_var.set(current[:-1])
            self.on_input_change(None)
        elif self.output_var.get():
            # 删除输出框内容
            current_output = self.output_var.get()
            self.output_var.set(current_output[:-1])

    def clear_input(self):
        self.load_word_dict()

    def commit_space(self):
        # 删除输出框内容
        current_output = self.output_var.get()
        self.output_var.set(current_output[:-10000])

    def commit_input(self):
        """提交当前输入（回车键）"""
        if self.input_var.get():
            self.select_word(self.input_var.get())
        else:
            # 换行
            current_output = self.output_var.get()
            self.output_var.set(current_output + "\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = ChineseInputMethod(root)
    root.mainloop()
