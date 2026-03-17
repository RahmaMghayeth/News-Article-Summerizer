import tkinter as tk
from tkinter import ttk, font
import threading
import requests
from newspaper import Article
import nltk

nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)


BG       = "#F7F5F2"
PANEL    = "#FFFFFF"
CARD     = "#FFFFFF"
BORDER   = "#E0DBD5"
ACCENT   = "#2563EB"
ACCENT_H = "#1D4ED8"
TEXT     = "#1C1917"
TEXT_DIM = "#78716C"
TEXT_MUT = "#A8A29E"
SUCCESS  = "#16A34A"
WARN     = "#DC2626"
TAG_BG   = "#EFF6FF"
TAG_FG   = "#2563EB"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}


class NewsSummarizer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("News Article Summarizer")
        self.geometry("920x700")
        self.minsize(760, 580)
        self.configure(bg=BG)
        self.resizable(True, True)

        self._anim_id   = None
        self._dot_count = 0
        self._pulse_val = 0

        self._build_fonts()
        self._build_ui()

    def _build_fonts(self):
        self.f_title   = font.Font(family="Segoe UI", size=16, weight="bold")
        self.f_sub     = font.Font(family="Segoe UI", size=9)
        self.f_label   = font.Font(family="Segoe UI", size=8,  weight="bold")
        self.f_input   = font.Font(family="Segoe UI", size=10)
        self.f_body    = font.Font(family="Segoe UI", size=10)
        self.f_section = font.Font(family="Segoe UI", size=9,  weight="bold")
        self.f_tag     = font.Font(family="Segoe UI", size=8)
        self.f_status  = font.Font(family="Segoe UI", size=8)
        self.f_btn     = font.Font(family="Segoe UI", size=9,  weight="bold")

    def _build_ui(self):
        hdr = tk.Frame(self, bg=PANEL,
                       highlightthickness=1, highlightbackground=BORDER)
        hdr.pack(fill="x")

        inner_hdr = tk.Frame(hdr, bg=PANEL)
        inner_hdr.pack(fill="x", padx=24, pady=14)

        left = tk.Frame(inner_hdr, bg=PANEL)
        left.pack(side="left")

        tk.Label(left, text="📰", font=font.Font(size=20),
                 bg=PANEL).pack(side="left", padx=(0, 10))

        title_block = tk.Frame(left, bg=PANEL)
        title_block.pack(side="left")
        tk.Label(title_block, text="News Article Summarizer",
                 font=self.f_title, fg=TEXT, bg=PANEL).pack(anchor="w")
        tk.Label(title_block, text="Paste any article URL to extract a summary and keywords",
                 font=self.f_sub, fg=TEXT_DIM, bg=PANEL).pack(anchor="w")

        right = tk.Frame(inner_hdr, bg=PANEL)
        right.pack(side="right")
        self.status_dot = tk.Label(right, text="●", font=self.f_status,
                                   fg=SUCCESS, bg=PANEL)
        self.status_dot.pack(side="left")
        self.status_lbl = tk.Label(right, text=" Ready",
                                   font=self.f_status, fg=TEXT_DIM, bg=PANEL)
        self.status_lbl.pack(side="left")


        inp_outer = tk.Frame(self, bg=BG)
        inp_outer.pack(fill="x", padx=24, pady=16)

        tk.Label(inp_outer, text="Article URL", font=self.f_label,
                 fg=TEXT_DIM, bg=BG).pack(anchor="w", pady=(0, 4))

        row = tk.Frame(inp_outer, bg=BG)
        row.pack(fill="x")

        self.url_var = tk.StringVar(
            value="")

        entry_frame = tk.Frame(row, bg=PANEL,
                               highlightthickness=1,
                               highlightbackground=BORDER)
        entry_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.url_entry = tk.Entry(entry_frame, textvariable=self.url_var,
                                  font=self.f_input, bg=PANEL, fg=TEXT,
                                  insertbackground=ACCENT, relief="flat",
                                  highlightthickness=0)
        self.url_entry.pack(fill="x", ipady=9, padx=10)
        self.url_entry.bind("<FocusIn>",
            lambda e: entry_frame.config(highlightbackground=ACCENT))
        self.url_entry.bind("<FocusOut>",
            lambda e: entry_frame.config(highlightbackground=BORDER))

        self.btn = tk.Button(row, text="Summarize",
                             font=self.f_btn, fg="#FFFFFF", bg=ACCENT,
                             activebackground=ACCENT_H, activeforeground="#FFFFFF",
                             relief="flat", cursor="hand2", padx=18,
                             command=self._on_analyze)
        self.btn.pack(side="right", ipady=9)
        self.btn.bind("<Enter>", lambda e: self.btn.config(bg=ACCENT_H))
        self.btn.bind("<Leave>", lambda e: self.btn.config(bg=ACCENT))


        self.progress_var = tk.DoubleVar(value=0)
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Clean.Horizontal.TProgressbar",
                        troughcolor=BORDER, background=ACCENT,
                        bordercolor=BG, lightcolor=ACCENT,
                        darkcolor=ACCENT, thickness=3)
        self.progress = ttk.Progressbar(self,
                                        variable=self.progress_var,
                                        style="Clean.Horizontal.TProgressbar",
                                        mode="determinate", maximum=100)
        self.progress.pack(fill="x", padx=24, pady=(0, 4))


        meta_outer = tk.Frame(self, bg=BG)
        meta_outer.pack(fill="x", padx=24, pady=(0, 10))

        meta_card = tk.Frame(meta_outer, bg=PANEL,
                             highlightthickness=1, highlightbackground=BORDER)
        meta_card.pack(fill="x")

        meta_inner = tk.Frame(meta_card, bg=PANEL)
        meta_inner.pack(fill="x", padx=16, pady=10)
        meta_inner.columnconfigure(0, weight=3)
        meta_inner.columnconfigure(1, weight=2)
        meta_inner.columnconfigure(2, weight=1)

        self.lbl_title  = self._meta_field(meta_inner, "Title",   col=0)
        self.lbl_author = self._meta_field(meta_inner, "Authors", col=1)
        self.lbl_date   = self._meta_field(meta_inner, "Date",    col=2)


        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=(0, 12))
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        self.left_card = self._card(body, "Summary")
        self.left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.summary_text = self._scrolled_text(self.left_card._inner)

        self.right_card = self._card(body, "Keywords")
        self.right_card.grid(row=0, column=1, sticky="nsew")
        self.kw_frame = tk.Frame(self.right_card._inner, bg=PANEL)
        self.kw_frame.pack(fill="both", expand=True)



        bar = tk.Frame(self, bg=PANEL,
                       highlightthickness=1, highlightbackground=BORDER,
                       height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self.bar_lbl = tk.Label(bar,
                                text="Ready — paste a URL above and click Summarize",
                                font=self.f_status, fg=TEXT_DIM, bg=PANEL)
        self.bar_lbl.pack(side="left", padx=14)

        tk.Label(bar, text="News Article Summarizer",
                 font=self.f_status, fg=TEXT_MUT, bg=PANEL).pack(
            side="right", padx=14)


    def _card(self, parent, title):
        outer = tk.Frame(parent, bg=PANEL,
                         highlightthickness=1, highlightbackground=BORDER)
        hdr = tk.Frame(outer, bg=BG)
        hdr.pack(fill="x")
        tk.Label(hdr, text=title, font=self.f_section,
                 fg=TEXT, bg=BG).pack(anchor="w", padx=12, pady=6)
        tk.Frame(outer, bg=BORDER, height=1).pack(fill="x")

        inner = tk.Frame(outer, bg=PANEL)
        inner.pack(fill="both", expand=True, padx=10, pady=8)
        outer._inner = inner
        return outer

    def _meta_field(self, parent, label, col):
        frame = tk.Frame(parent, bg=PANEL)
        frame.grid(row=0, column=col, sticky="ew", padx=(0, 12), pady=2)
        tk.Label(frame, text=label.upper(), font=self.f_label,
                 fg=TEXT_DIM, bg=PANEL).pack(anchor="w")
        val = tk.Label(frame, text="—", font=self.f_tag,
                       fg=TEXT, bg=PANEL, wraplength=220, justify="left")
        val.pack(anchor="w")
        return val

    def _scrolled_text(self, parent, height=10):
        frame = tk.Frame(parent, bg=PANEL)
        frame.pack(fill="both", expand=True)

        sb = tk.Scrollbar(frame, bg=BG, troughcolor=BG,
                          activebackground=TEXT_DIM, relief="flat", width=6)
        sb.pack(side="right", fill="y")

        t = tk.Text(frame, font=self.f_body, bg=PANEL, fg=TEXT,
                    relief="flat", wrap="word", height=height,
                    insertbackground=ACCENT,
                    selectbackground="#DBEAFE",
                    yscrollcommand=sb.set, padx=6, pady=6,
                    highlightthickness=0, state="disabled",
                    spacing1=2, spacing3=2)
        t.pack(side="left", fill="both", expand=True)
        sb.config(command=t.yview)
        return t

    def _pulse_status(self):
        if not self._anim_id:
            return
        dots = "." * (self._dot_count % 4)
        self.bar_lbl.config(text=f"Fetching and analyzing article{dots}")
        colors = [ACCENT, ACCENT_H, TEXT_DIM, ACCENT_H, ACCENT]
        self.status_dot.config(fg=colors[int(self._pulse_val) % len(colors)])
        self._pulse_val += 0.4
        self._dot_count += 1
        self._anim_id = self.after(250, self._pulse_status)

    def _stop_pulse(self):
        if self._anim_id:
            self.after_cancel(self._anim_id)
            self._anim_id = None
        self.status_dot.config(fg=SUCCESS)


    def _on_analyze(self):
        url = self.url_var.get().strip()
        if not url:
            self._set_status("Please enter a URL first.", WARN)
            return
        self.btn.config(state="disabled", text="Summarizing…", bg=TEXT_MUT)
        self._clear_results()
        self._set_status("Connecting…", ACCENT)
        self.progress_var.set(10)
        self._dot_count = 0
        self._anim_id = self.after(0, self._pulse_status)
        threading.Thread(target=self._fetch, args=(url,), daemon=True).start()

    def _fetch(self, url):
        try:
            self.after(0, lambda: self.progress_var.set(30))
            resp = requests.get(url, headers=HEADERS, timeout=30)
            self.after(0, lambda: self.progress_var.set(55))

            art = Article(url)
            art.html = resp.text
            art.is_downloaded = True
            art.parse()
            self.after(0, lambda: self.progress_var.set(75))
            art.nlp()
            self.after(0, lambda: self.progress_var.set(95))
            self.after(0, lambda: self._display(art))
        except Exception as exc:
            self.after(0, lambda: self._show_error(str(exc)))

    def _display(self, art):
        self._stop_pulse()
        self.progress_var.set(100)

        title   = art.title   or "Unknown"
        authors = ", ".join(art.authors) if art.authors else "Unknown"
        date    = str(art.publish_date)[:10] if art.publish_date else "Unknown"
        summary = art.summary or "No summary available."
        kws     = art.keywords or []

        self.lbl_title.config(text=title[:65] + ("…" if len(title) > 65 else ""))
        self.lbl_author.config(text=authors[:45])
        self.lbl_date.config(text=date)

        self.summary_text.config(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("end", summary)
        self.summary_text.config(state="disabled")

        for w in self.kw_frame.winfo_children():
            w.destroy()

        for i, kw in enumerate(kws):
            tag = tk.Label(self.kw_frame, text=f"  {kw}  ",
                           font=self.f_tag, fg=TAG_FG, bg=TAG_BG,
                           relief="flat", padx=4, pady=3)
            tag.grid(row=i // 2, column=i % 2,
                     padx=4, pady=3, sticky="ew")
        self.kw_frame.columnconfigure(0, weight=1)
        self.kw_frame.columnconfigure(1, weight=1)

        self._set_status(f"Done — {len(kws)} keywords extracted.", SUCCESS)
        self.btn.config(state="normal", text="Summarize", bg=ACCENT)
        self.after(3000, lambda: self.progress_var.set(0))

    def _show_error(self, msg):
        self._stop_pulse()
        self.progress_var.set(0)
        self.summary_text.config(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("end", f"Error: {msg}")
        self.summary_text.config(state="disabled", fg=WARN)
        self._set_status("Failed to fetch article. Check the URL or your connection.", WARN)
        self.btn.config(state="normal", text="Summarize", bg=ACCENT)

    def _clear_results(self):
        self.lbl_title.config(text="—")
        self.lbl_author.config(text="—")
        self.lbl_date.config(text="—")
        self.summary_text.config(state="normal", fg=TEXT)
        self.summary_text.delete("1.0", "end")
        self.summary_text.config(state="disabled")
        for w in self.kw_frame.winfo_children():
            w.destroy()

    def _set_status(self, msg, color=TEXT_DIM):
        self.status_lbl.config(text=f" {msg}", fg=color)
        self.bar_lbl.config(text=msg, fg=color)


if __name__ == "__main__":
    app = NewsSummarizer()
    app.mainloop()