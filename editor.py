import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
import uuid
from sequence_engine import SequenceEngine

class SequenceEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dynamic Sequence Diagram Editor")
        self.engine = SequenceEngine()
        self.save_path = "diagram_state.json"

        # 載入既有檔案，若無則初始化範例並執行自動排版
        if not self.engine.load_from_file(self.save_path):
            self.engine.lifelines = [
                {"id": "User", "x": 0},
                {"id": "Frontend", "x": 0},
                {"id": "Backend", "x": 0}
            ]
            self.engine.messages = [
                {"id": "m1", "from": "User", "to": "Frontend", "y": 0, "text": "clickLogin()"},
                {"id": "m2", "from": "Frontend", "to": "Backend", "y": 0, "text": "authRequest()"},
                {"id": "m3", "from": "Backend", "to": "Frontend", "y": 0, "text": "tokenOK()"}
            ]
            self.engine.add_fragment("f_init", "alt", 0, 140, 300, 140)
            self.engine.auto_layout()

        # 頂部工具列
        toolbar = tk.Frame(root)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        tk.Button(toolbar, text="儲存 (Save)", command=self.save_diagram).pack(side=tk.LEFT, padx=4, pady=4)
        tk.Button(toolbar, text="讀取 (Load)", command=self.load_diagram).pack(side=tk.LEFT, padx=4, pady=4)
        tk.Button(toolbar, text="重新自動排版", command=self.reset_layout).pack(side=tk.LEFT, padx=4, pady=4)
        tk.Label(toolbar, text="操作提示：拖曳方塊改順序 / 拖曳箭頭調高度 / 右鍵畫 Ignore/Consider 區塊 / 點擊區塊編輯清單").pack(side=tk.LEFT, padx=10)

        self.canvas = tk.Canvas(root, width=850, height=550, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 互動狀態變數
        self.drag_data = {"type": None, "id": None, "mode": None, "start_x": 0, "start_y": 0}
        self.draw_mode = None
        self.temp_rect = None

        # 右鍵選單
        self.context_menu = tk.Menu(root, tearoff=0)
        self.context_menu.add_command(label="建立 Ignore 區塊 (拖曳繪製)", command=lambda: self.start_draw_fragment("ignore"))
        self.context_menu.add_command(label="建立 Consider 區塊 (拖曳繪製)", command=lambda: self.start_draw_fragment("consider"))

        # 事件綁定
        self.canvas.bind("<Button-1>", self.on_left_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_up)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)

        self.render()

    def render(self):
        self.canvas.delete("all")
        lifeline_x_map = {l["id"]: l["x"] for l in self.engine.lifelines}

        # 1. 繪製 Combined Fragments (底層)
        for frag in self.engine.fragments:
            x, y, w, h = frag["x"], frag["y"], frag["width"], frag["height"]
            color = "#fff3cd" if frag["type"] == "ignore" else ("#d1ecf1" if frag["type"] == "consider" else "#f8f9fa")
            self.canvas.create_rectangle(x, y, x + w, y + h, outline="#333", fill=color, width=1.5)
            label = f"[{frag['type']}]"
            if frag["interactions"]:
                label += f" {{{', '.join(frag['interactions'])}}}"
            self.canvas.create_text(x + 8, y + 8, anchor="nw", text=label, font=("Arial", 9, "bold"))
            # 右下角調整大小控制點
            self.canvas.create_rectangle(x + w - 8, y + h - 8, x + w, y + h, fill="#555", outline="")

        # 2. 繪製 Lifelines
        for l in self.engine.lifelines:
            x = l["x"]
            self.canvas.create_rectangle(x - 45, 25, x + 45, 60, fill="#e2e8f0", outline="#1e293b", width=1.5)
            self.canvas.create_text(x, 42, text=l["id"], font=("Arial", 10, "bold"))
            self.canvas.create_line(x, 60, x, 500, dash=(4, 4), fill="#64748b")

        # 3. 繪製訊息箭頭
        for m in self.engine.messages:
            x1 = lifeline_x_map.get(m["from"], 100)
            x2 = lifeline_x_map.get(m["to"], 200)
            y = m["y"]
            self.canvas.create_line(x1, y, x2, y, arrow=tk.LAST, width=2, fill="#0f172a")
            self.canvas.create_text((x1 + x2) / 2, y - 10, text=m["text"], font=("Arial", 9))

    def start_draw_fragment(self, frag_type):
        self.draw_mode = frag_type
        self.canvas.config(cursor="crosshair")

    def on_right_click(self, event):
        self.context_menu.post(event.x_root, event.y_root)

    def on_left_down(self, event):
        if self.draw_mode:
            self.drag_data = {"type": "new_frag", "start_x": event.x, "start_y": event.y}
            return

        # 檢查是否點擊 Lifeline 標題方塊
        for l in self.engine.lifelines:
            if abs(event.x - l["x"]) <= 45 and 25 <= event.y <= 60:
                self.drag_data = {"type": "lifeline", "id": l["id"], "start_x": event.x}
                return

        # 檢查是否點擊訊息箭頭
        for m in self.engine.messages:
            if abs(event.y - m["y"]) <= 10:
                self.drag_data = {"type": "message", "id": m["id"], "start_y": event.y}
                return

        # 檢查是否點擊 Fragment (移動或右下角縮放)
        for frag in reversed(self.engine.fragments):
            x, y, w, h = frag["x"], frag["y"], frag["width"], frag["height"]
            if (x + w - 12) <= event.x <= (x + w + 4) and (y + h - 12) <= event.y <= (y + h + 4):
                self.drag_data = {"type": "frag_resize", "id": frag["id"], "orig": (x, y, w, h), "start_x": event.x, "start_y": event.y}
                return
            if x <= event.x <= (x + w) and y <= event.y <= (y + h):
                self.drag_data = {"type": "frag_move", "id": frag["id"], "orig": (x, y, w, h), "start_x": event.x, "start_y": event.y}
                return

    def on_mouse_move(self, event):
        dtype = self.drag_data.get("type")
        if not dtype:
            return

        if dtype == "new_frag":
            if self.temp_rect:
                self.canvas.delete(self.temp_rect)
            self.temp_rect = self.canvas.create_rectangle(
                self.drag_data["start_x"], self.drag_data["start_y"], event.x, event.y,
                outline="blue", dash=(3, 3)
            )
        elif dtype == "lifeline":
            self.engine.drag_lifeline(self.drag_data["id"], event.x)
            self.render()
        elif dtype == "message":
            self.engine.drag_message(self.drag_data["id"], event.y)
            self.render()
        elif dtype == "frag_move":
            ox, oy, ow, oh = self.drag_data["orig"]
            dx, dy = event.x - self.drag_data["start_x"], event.y - self.drag_data["start_y"]
            self.engine.move_or_resize_fragment(self.drag_data["id"], ox + dx, oy + dy, ow, oh)
            self.render()
        elif dtype == "frag_resize":
            ox, oy, ow, oh = self.drag_data["orig"]
            dx, dy = event.x - self.drag_data["start_x"], event.y - self.drag_data["start_y"]
            self.engine.move_or_resize_fragment(self.drag_data["id"], ox, oy, ow + dx, oh + dy)
            self.render()

    def on_left_up(self, event):
        if self.drag_data.get("type") == "new_frag":
            if self.temp_rect:
                self.canvas.delete(self.temp_rect)
                self.temp_rect = None
            x1, y1 = self.drag_data["start_x"], self.drag_data["start_y"]
            x, y = min(x1, event.x), min(y1, event.y)
            w, h = abs(event.x - x1), abs(event.y - y1)
            if w > 20 and h > 20:
                fid = f"frag_{uuid.uuid4().hex[:6]}"
                self.engine.add_fragment(fid, self.draw_mode, x, y, w, h)
            self.draw_mode = None
            self.canvas.config(cursor="")
            self.render()

        self.drag_data = {"type": None}

    def on_double_click(self, event):
        # 雙擊 Ignore / Consider 區塊編輯 interaction 清單
        for frag in reversed(self.engine.fragments):
            x, y, w, h = frag["x"], frag["y"], frag["width"], frag["height"]
            if x <= event.x <= (x + w) and y <= event.y <= (y + h):
                if frag["type"] in ("ignore", "consider"):
                    current = ", ".join(frag["interactions"])
                    res = simpledialog.askstring(
                        f"編輯 {frag['type']} 清單",
                        "請輸入要忽略/考慮的 interaction 名稱（以逗號分隔）：",
                        initialvalue=current
                    )
                    if res is not None:
                        items = [s.strip() for s in res.split(",") if s.strip()]
                        self.engine.edit_fragment_interactions(frag["id"], items)
                        self.render()
                break

    def save_diagram(self):
        self.engine.save_to_file(self.save_path)
        messagebox.showinfo("儲存成功", f"已將目前排版與修改儲存至 {self.save_path}")

    def load_diagram(self):
        if self.engine.load_from_file(self.save_path):
            self.render()
            messagebox.showinfo("讀取成功", "已還原上次儲存的修改狀態！")

    def reset_layout(self):
        self.engine.auto_layout()
        self.render()

if __name__ == "__main__":
    root = tk.Tk()
    app = SequenceEditorApp(root)
    root.mainloop()
