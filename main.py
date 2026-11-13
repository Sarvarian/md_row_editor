import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, font as tkfont


class Row:
    def __init__(self, row_id, text):
        self.id = row_id
        self.text = text


class MarkdownRowEditor:
    def __init__(self, root, md_path):
        self.root = root
        self.md_path = os.path.abspath(md_path)

        self.rows = []
        self.next_id = 1
        self.selected_index = None

        self.drag_row = None
        self.drag_label = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.moved = False

        self.font = tkfont.nametofont("TkDefaultFont")

        root.title(f"Markdown rows - {self.md_path}")
        root.geometry("660x500")
        root.minsize(420, 280)

        # Top row: new row text + Add/Delete
        top = ttk.Frame(root)
        top.pack(fill=tk.X, padx=10, pady=(10, 4))

        self.entry = ttk.Entry(top)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind("<Return>", self.add_row)

        ttk.Button(top, text="Add", command=self.add_row).pack(side=tk.LEFT, padx=(4, 0))
        ttk.Button(top, text="Delete", command=self.delete_selected).pack(side=tk.LEFT, padx=(4, 0))

        # Controls
        controls = ttk.Frame(root)
        controls.pack(fill=tk.X, padx=10, pady=(0, 6))
        ttk.Button(controls, text="Open…", command=self.open_file).pack(side=tk.LEFT)
        ttk.Button(controls, text="Save", command=self.save).pack(side=tk.LEFT, padx=(4, 0))
        ttk.Label(
            controls,
            text="Double-click a row to edit it. Drag rows to reorder."
        ).pack(side=tk.LEFT, padx=(12, 0))

        # Main list area
        body = ttk.Frame(root)
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.listbox = tk.Listbox(body, font=self.font, borderwidth=1, relief="solid")
        self.scrollbar = ttk.Scrollbar(body, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=self.scrollbar.set)

        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox.bind("<Button-1>", self.on_press)
        self.listbox.bind("<B1-Motion>", self.on_motion)
        self.listbox.bind("<ButtonRelease-1>", self.on_release)
        self.listbox.bind("<Double-Button-1>", self.on_double_click)

        self.load()
        self.refresh()
        self.entry.focus_set()

        root.protocol("WM_DELETE_WINDOW", self.on_close)

    def refresh(self):
        """Redraw the listbox from self.rows."""
        self.listbox.delete(0, tk.END)
        for row in self.rows:
            self.listbox.insert(tk.END, row.text)

        self.listbox.selection_clear(0, tk.END)
        if self.selected_index is not None and 0 <= self.selected_index < len(self.rows):
            self.listbox.selection_set(self.selected_index)
            self.listbox.see(self.selected_index)

    def index_at(self, event):
        """Return the row index under the mouse event."""
        if not self.rows:
            return None

        try:
            idx = int(self.listbox.nearest(event.y))
        except Exception:
            return None

        return max(0, min(len(self.rows) - 1, idx))

    def load(self):
        """Load rows from the .md file."""
        self.rows.clear()
        self.selected_index = None

        if not os.path.exists(self.md_path):
            return

        with open(self.md_path, "r", encoding="utf-8-sig") as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue

                if line.startswith("- "):
                    item = line[2:].rstrip()
                elif line.startswith("-"):
                    item = line[1:].strip()
                else:
                    # Non-list lines are also kept so text is not lost.
                    # If you want strict Markdown-list-only behavior,
                    # replace the next line with:
                    # continue
                    item = line

                if not item:
                    continue

                self.rows.append(Row(self.next_id, item))
                self.next_id += 1

    def save(self):
        """Save rows to the .md file as Markdown list items."""
        try:
            content = "\n".join("- " + row.text for row in self.rows)

            with open(self.md_path, "w", encoding="utf-8") as f:
                f.write(content)
                if content:
                    f.write("\n")

            self.root.title(f"Markdown rows - {self.md_path}")
        except Exception as exc:
            messagebox.showerror("Could not save Markdown file", str(exc), parent=self.root)

    def add_row(self, event=None):
        """Add a new row from the text entry."""
        text = self.entry.get().strip()
        if not text:
            messagebox.showinfo("Add row", "Please type a row first.", parent=self.root)
            return

        row = Row(self.next_id, text)
        self.next_id += 1

        insert_at = len(self.rows)
        if self.selected_index is not None and 0 <= self.selected_index < len(self.rows):
            insert_at = self.selected_index + 1

        self.rows.insert(insert_at, row)
        self.entry.delete(0, tk.END)
        self.selected_index = insert_at

        self.save()
        self.refresh()
        self.entry.focus_set()

    def delete_selected(self):
        """Delete the currently selected row."""
        if self.selected_index is None or not self.rows:
            messagebox.showinfo("Delete", "Click a row first.", parent=self.root)
            return

        idx = self.selected_index
        del self.rows[idx]

        if self.rows:
            self.selected_index = min(idx, len(self.rows) - 1)
        else:
            self.selected_index = None

        self.save()
        self.refresh()

    def open_file(self):
        """Open another .md file."""
        path = filedialog.askopenfilename(
            parent=self.root,
            title="Open Markdown file",
            filetypes=[
                ("Markdown files", "*.md"),
                ("Text files", "*.txt"),
                ("All files", "*.*"),
            ],
        )

        if path:
            self.md_path = os.path.abspath(path)
            self.load()
            self.root.title(f"Markdown rows - {self.md_path}")
            self.refresh()

    def on_close(self):
        """Save on close."""
        self.save()
        self.root.destroy()

    def on_press(self, event):
        """Mouse button 1 pressed."""
        idx = self.index_at(event)
        if idx is None:
            return

        self.selected_index = idx
        self.drag_row = self.rows[idx]

        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root
        self.moved = False

        if self.drag_label is not None:
            self.drag_label.destroy()
            self.drag_label = None

        self.refresh()
        self.listbox.grab_set()

    def on_motion(self, event):
        """Mouse moved while button 1 is pressed."""
        if self.drag_row is None:
            return

        # Do not start dragging until the mouse has moved a little.
        if not self.moved:
            dx = abs(event.x_root - self.drag_start_x)
            dy = abs(event.y_root - self.drag_start_y)
            if dx + dy < 5:
                return
            self.moved = True

        # Create the floating drag label only once.
        if self.drag_label is None:
            self.drag_label = tk.Label(
                self.root,
                text=self.drag_row.text,
                bg="#cfe8ff",
                fg="black",
                bd=1,
                relief="solid",
                font=self.font,
            )

        # Convert screen coordinates to root-window coordinates.
        x = event.x_root - self.root.winfo_rootx()
        y = event.y_root - self.root.winfo_rooty()

        self.drag_label.place(x=x + 12, y=y + 12)
        self.drag_label.lift()

        idx = self.index_at(event)
        if idx is None:
            return

        current = self.rows.index(self.drag_row)
        if idx == current:
            return

        self.rows.remove(self.drag_row)
        self.rows.insert(idx, self.drag_row)

        self.selected_index = idx
        self.refresh()

    def on_release(self, event):
        """Mouse button 1 released."""
        try:
            self.listbox.grab_release()
        except Exception:
            pass

        if self.drag_label is not None:
            self.drag_label.destroy()
            self.drag_label = None

        if self.drag_row is not None and self.moved:
            self.save()

        self.drag_row = None
        self.moved = False

    def on_double_click(self, event):
        """Double-click a row to edit it."""
        idx = self.index_at(event)
        if idx is None:
            return

        row = self.rows[idx]
        new_text = simpledialog.askstring(
            "Edit row",
            "Row text:",
            initialtext=row.text,
            parent=self.root,
        )

        if new_text is None:
            return

        new_text = new_text.strip()
        if not new_text:
            messagebox.showwarning("Edit row", "A row cannot be empty.", parent=self.root)
            return

        row.text = new_text
        self.selected_index = idx

        self.save()
        self.refresh()


def main():
    md_path = sys.argv[1] if len(sys.argv) > 1 else "rows.md"
    root = tk.Tk()
    MarkdownRowEditor(root, md_path)
    root.mainloop()


if __name__ == "__main__":
    main()
