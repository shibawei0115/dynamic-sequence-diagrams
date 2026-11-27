import json
import os

class SequenceEngine:
    def __init__(self):
        self.lifelines = []
        self.messages = []
        self.fragments = []

    def auto_layout(self):
        """需求 1: 自動排版"""
        x_spacing = 160
        for i, lifeline in enumerate(self.lifelines):
            lifeline["x"] = 120 + (i * x_spacing)

        y_spacing = 65
        for i, message in enumerate(self.messages):
            message["y"] = 100 + (i * y_spacing)

        for frag in self.fragments:
            if self.lifelines:
                min_x = min(l["x"] for l in self.lifelines) - 40
                max_x = max(l["x"] for l in self.lifelines) + 40
                frag["x"] = min_x
                frag["width"] = max_x - min_x

    def drag_lifeline(self, lifeline_id, new_x):
        """需求 2: 左右拖曳改變 Lifeline 順序"""
        for l in self.lifelines:
            if l["id"] == lifeline_id:
                l["x"] = new_x
                self.lifelines.sort(key=lambda item: item["x"])
                break

    def drag_message(self, message_id, new_y):
        """需求 2: 上下拖曳調整訊息位置"""
        for m in self.messages:
            if m["id"] == message_id:
                m["y"] = new_y
                self.messages.sort(key=lambda item: item["y"])
                break

    def move_or_resize_fragment(self, frag_id, x, y, width, height):
        """需求 2: 移動或調整 Combined Fragment 大小"""
        for frag in self.fragments:
            if frag["id"] == frag_id:
                frag["x"] = x
                frag["y"] = y
                frag["width"] = max(40, width)
                frag["height"] = max(30, height)
                break

    def add_fragment(self, frag_id, frag_type, x, y, width, height):
        """需求 3: 建立 Ignore / Consider / Alt 等區塊"""
        self.fragments.append({
            "id": frag_id,
            "type": frag_type,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "interactions": []
        })

    def edit_fragment_interactions(self, frag_id, interactions_list):
        """需求 3: 編輯區塊內要忽略或考慮的 interaction 清單"""
        for frag in self.fragments:
            if frag["id"] == frag_id:
                frag["interactions"] = interactions_list
                break

    def save_to_file(self, filepath):
        """需求 4: 儲存所有修改後的內容至 JSON"""
        data = {
            "lifelines": self.lifelines,
            "messages": self.messages,
            "fragments": self.fragments
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_from_file(self, filepath):
        """需求 4: 讀取已保存的內容，避免被自動排版覆蓋"""
        if not os.path.exists(filepath):
            return False
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.lifelines = data.get("lifelines", [])
            self.messages = data.get("messages", [])
            self.fragments = data.get("fragments", [])
        return True
