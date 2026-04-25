import os
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import ImageGrab, Image

class ScreenCropper:
    def __init__(self, root):
        self.root = root
        self.root.title("Recorta y Redimensiona")
        self.root.geometry("360x290")
        self.root.resizable(False, False)

        self.start_x = None
        self.start_y = None
        self.rect = None

        tk.Label(root, text="Ancho de salida:").pack(pady=(15, 0))
        self.width_entry = tk.Entry(root)
        self.width_entry.insert(0, "800")
        self.width_entry.pack()

        tk.Label(root, text="Alto de salida:").pack(pady=(10, 0))
        self.height_entry = tk.Entry(root)
        self.height_entry.insert(0, "400")
        self.height_entry.pack()

        self.compress_var = tk.BooleanVar(value=True)
        self.compress_check = tk.Checkbutton(
            root,
            text="Comprimir imagen al guardar",
            variable=self.compress_var,
            command=self.toggle_quality_widgets
        )
        self.compress_check.pack(pady=(12, 5))

        self.quality_label = tk.Label(root, text="Nivel de calidad: 80")
        self.quality_label.pack()

        self.quality_var = tk.IntVar(value=80)
        self.quality_scale = tk.Scale(
            root,
            from_=1,
            to=100,
            orient="horizontal",
            variable=self.quality_var,
            command=self.update_quality_label,
            length=250
        )
        self.quality_scale.pack()

        tk.Label(
            root,
            text="Menor calidad = más compresión",
            fg="gray"
        ).pack(pady=(0, 10))

        tk.Button(root, text="Capturar área", command=self.start_capture).pack(pady=10)

        self.toggle_quality_widgets()

    def update_quality_label(self, value=None):
        self.quality_label.config(text=f"Nivel de calidad: {self.quality_var.get()}")

    def toggle_quality_widgets(self):
        state = "normal" if self.compress_var.get() else "disabled"
        self.quality_scale.config(state=state)
        self.quality_label.config(
            fg="black" if self.compress_var.get() else "gray"
        )

    def start_capture(self):
        try:
            self.target_width = int(self.width_entry.get())
            self.target_height = int(self.height_entry.get())

            if self.target_width <= 0 or self.target_height <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Ingresa un ancho y alto válidos.")
            return

        self.root.withdraw()
        self.root.after(200, self.create_overlay)

    def create_overlay(self):
        self.overlay = tk.Toplevel()
        self.overlay.attributes("-fullscreen", True)
        self.overlay.attributes("-alpha", 0.25)
        self.overlay.attributes("-topmost", True)
        self.overlay.configure(bg="black")

        self.canvas = tk.Canvas(self.overlay, bg="black", highlightthickness=0, cursor="cross")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.overlay.bind("<Escape>", self.cancel_capture)

    def on_button_press(self, event):
        self.start_x = event.x_root
        self.start_y = event.y_root

        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="red", width=2
        )

    def on_mouse_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x_root, event.y_root)

    def on_button_release(self, event):
        end_x = event.x_root
        end_y = event.y_root

        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)

        self.overlay.destroy()
        self.root.deiconify()
        self.root.update()

        if x2 - x1 < 2 or y2 - y1 < 2:
            messagebox.showwarning("Aviso", "Selección demasiado pequeña.")
            return

        img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        img = img.resize((self.target_width, self.target_height), Image.LANCZOS)

        file_path = filedialog.asksaveasfilename(
            defaultextension=".webp",
            filetypes=[
                ("WEBP", "*.webp"),
                ("PNG", "*.png"),
                ("JPEG", "*.jpg")
            ]
        )

        if not file_path:
            return

        self.save_optimized_image(img, file_path)

    def save_optimized_image(self, img, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        compress_enabled = self.compress_var.get()
        quality = self.quality_var.get()

        try:
            if ext in (".jpg", ".jpeg"):
                if img.mode in ("RGBA", "LA"):
                    img = img.convert("RGB")

                if compress_enabled:
                    jpeg_quality = min(max(quality, 5), 95)
                    img.save(
                        file_path,
                        "JPEG",
                        quality=jpeg_quality,
                        optimize=True,
                        progressive=True
                    )
                else:
                    img.save(file_path, "JPEG", quality=95)

            elif ext == ".png":
                if compress_enabled:
                    img_to_save = img

                    if quality < 80:
                        if quality >= 60:
                            colors = 256
                        elif quality >= 40:
                            colors = 128
                        elif quality >= 20:
                            colors = 64
                        else:
                            colors = 32

                        img_to_save = img.convert("RGB").quantize(colors=colors)

                    img_to_save.save(
                        file_path,
                        "PNG",
                        optimize=True,
                        compress_level=9
                    )
                else:
                    img.save(file_path, "PNG", compress_level=0)

            elif ext == ".webp":
                if compress_enabled:
                    webp_quality = min(max(quality, 1), 100)
                    if img.mode in ("RGBA", "LA"):
                        img_to_save = img
                    else:
                        img_to_save = img.convert("RGB")

                    img_to_save.save(
                        file_path,
                        "WEBP",
                        quality=webp_quality,
                        method=6
                    )
                else:
                    if img.mode in ("RGBA", "LA"):
                        img_to_save = img
                    else:
                        img_to_save = img.convert("RGB")

                    img_to_save.save(file_path, "WEBP", quality=100, method=0)

            else:
                img.save(file_path)

            final_size = os.path.getsize(file_path)
            final_size_kb = final_size / 1024

            messagebox.showinfo(
                "Imagen guardada",
                f"Archivo guardado correctamente.\n\n"
                f"Peso final: {final_size_kb:.2f} KB\n"
                f"Calidad usada: {quality if compress_enabled else 'sin compresión'}"
            )

        except Exception as e:
            messagebox.showerror("Error al guardar", str(e))

    def cancel_capture(self, event=None):
        self.overlay.destroy()
        self.root.deiconify()

if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenCropper(root)
    root.mainloop()