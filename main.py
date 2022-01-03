from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageTk
import numpy as np
from pathlib import Path
import cv2
from utils import verify_image, load_images_recursively, resize_with_padding
from functools import partial

root_dir = Path("./images")
sample_image = root_dir / "beard before after 1" / "0.jpg"

save_state_dir = Path("./save_state")
labels_file = save_state_dir / "labels.npy"
marked_for_deletion_file = save_state_dir / "marked_for_deletion.npy"
marked_for_manual_file = save_state_dir / "marked_for_manual.npy"

image_paths, label2image = load_images_recursively(root_dir)
total_num_of_images = len(image_paths)

options = ["No label", "Before", "After"]
values = [-1, 0, 1]
values2options = {k: v for k, v in zip(values, options)}
options2values = {k: v for k, v in zip(options, values)}

def get_first_element_that_was_not_set(labels, marked_for_deletion, marked_for_manual):
    for i, (l, d, m) in enumerate(zip(labels, marked_for_deletion, marked_for_manual)):
        if 0 in l or 1 in l or d == 1 or m == 1:
            continue
        else:
            return i
    
    return -1

class Window(Frame):
    left_value: int = None
    right_value: int = None
    left_button = None
    right_button = None

    # tuples with [label_of_first, label_of_second]
    # label can be -1 = unlabeled, 0 = before, 1 = after
    labels = np.full((total_num_of_images, 2), -1)
    marked_for_deletion = np.zeros((total_num_of_images))
    marked_for_manual = np.zeros((total_num_of_images))

    if labels_file.exists():
        labels = np.load(labels_file)

    if marked_for_deletion_file.exists():
        marked_for_deletion = np.load(marked_for_deletion_file)
    
    if marked_for_manual_file.exists():
        marked_for_manual = np.load(marked_for_manual_file)  

    prev_btn = None
    next_btn = None
    mark_for_deletion_button = None
    mark_for_manual_button = None
    save_button = None

    def __init__(self, master, image_paths, initial_index=0):
        Frame.__init__(self, master)
        self.master = master
        self.pack(fill=BOTH, expand=1)
        self.index = initial_index

        self.image_paths = image_paths
        
        first_index = get_first_element_that_was_not_set(self.labels, self.marked_for_deletion, self.marked_for_manual)      

        if first_index > -1:
            self.index = first_index
            self.load_image(first_index)
        
        self.load_buttons()
        self.load_label_pickers()

        self.prev_btn = Button(self, text="Previous")
        self.next_btn = Button(self, text="Next")
        self.mark_for_deletion_button = Button(self, text="Mark for Deletion")
        self.mark_for_manual_button = Button(self, text="Mark for Manual")

          

    def save(self):
        np.save(labels_file, self.labels)
        np.save(marked_for_deletion_file, self.marked_for_deletion)
        np.save(marked_for_manual_file, self.marked_for_manual)

        print("Successfully saved")
        

    def load_image(self, index):
        img_path = self.image_paths[index]

        if verify_image(img_path):
            load = Image.open(img_path)
            resized = resize_with_padding(load)
            render = ImageTk.PhotoImage(resized)
            
            file_label = Label(self, text=f'Viewing: {img_path} ({index + 1}/{total_num_of_images})')

            file_label.grid_forget()
            file_label.grid(row=0, column=0, columnspan=4)

            img = Label(self, image=render)
            img.image = render

            img.grid_forget()
            img.grid(row=1, column=0, columnspan=4)
        else:
            error = Label(self, text=f'Image: {img_path} could not be opened')

            error.grid_forget()
            error.grid(row=1, column=0, columnspan=4)

            self.mark_for_deletion_handler()

    def next_handler(self):
        self.index += 1

        self.load_image(self.index)
        self.load_buttons()
        self.load_label_pickers()

    def prev_handler(self):
        self.index -= 1

        self.load_image(self.index)
        self.load_buttons()
        self.load_label_pickers()

    def set_label(self, left_or_right, value):
        index_of_image = self.index

        if left_or_right == "left":
            self.labels[index_of_image, 0] = value
        elif left_or_right == "right":
            self.labels[index_of_image, 1] = value


    def left_label_change_handler(self, *args):
        index_of_image = self.index
        current_labels = self.labels[index_of_image]

        if current_labels[0] == 1:
            self.labels[index_of_image, 0] = 0
            self.labels[index_of_image, 1] = 1
        else:
            self.labels[index_of_image, 0] = 1
            self.labels[index_of_image, 1] = 0

        self.load_label_pickers()

    def right_label_change_handler(self, *args):
        index_of_image = self.index
        current_labels = self.labels[index_of_image]

        if current_labels[1] == 1:
            self.labels[index_of_image, 0] = 1
            self.labels[index_of_image, 1] = 0
        else:
            self.labels[index_of_image, 0] = 0
            self.labels[index_of_image, 1] = 1

        self.load_label_pickers()

    def load_label_pickers(self):
        current_index = self.index
        labels = self.labels[current_index]

        if labels[0] == -1 and labels[1] == -1:
            left_value = 0       
            right_value = 1
            self.set_label("left", left_value)
            self.set_label("right", right_value)
        else:
            left_value = labels[0]        
            right_value = labels[1]

        if self.left_button == None:
            self.left_button = Button(self, command=self.left_label_change_handler, text=values2options[left_value])

        if self.right_button == None:
            self.right_button = Button(self, command=self.right_label_change_handler, text=values2options[right_value])
        
        if left_value == 0 and right_value == 1:
            self.left_button.config(bg="white", fg="black", text=values2options[0])
            self.right_button.config(bg="#525252", fg="white", text=values2options[1])
        elif left_value == 1 and right_value == 0:
            self.left_button.config(bg="#525252", fg="white", text=values2options[1])            
            self.right_button.config(bg="white", fg="black", text=values2options[0])

        self.left_button.grid_forget()
        self.left_button.grid(row=2, column=1, sticky=W)
        
        self.right_button.grid_forget()
        self.right_button.grid(row=2, column=2)

    def mark_for_deletion_handler(self):
        current_index = self.index
        value = self.marked_for_deletion[current_index]
        self.marked_for_deletion[current_index] = 1 if value == 0 else 0
        self.load_buttons()

    def mark_for_manual_handler(self):
        current_index = self.index
        value = self.marked_for_manual[current_index]
        self.marked_for_manual[current_index] = 1 if value == 0 else 0
        self.load_buttons()

    def load_buttons(self):
        if self.prev_btn == None:
            self.prev_btn = Button(self, text="Previous")
        if self.next_btn == None:
            self.next_btn = Button(self, text="Next")
        if self.mark_for_deletion_button == None:
            self.mark_for_deletion_button = Button(self, text="Mark for Deletion")
        if self.mark_for_manual_button == None:
            self.mark_for_manual_button = Button(self, text="Mark for Manual")
        if self.save_button == None:
            self.save_button = Button(self, text="Save")


        prev_status = DISABLED if self.index <= 0 else ACTIVE
        next_status = DISABLED if self.index > total_num_of_images - 1 else ACTIVE

        prev_btn = self.prev_btn
        next_btn = self.next_btn
        mark_for_deletion_button = self.mark_for_deletion_button
        mark_for_manual_button = self.mark_for_manual_button

        self.prev_btn.config(text="Previous", state=prev_status, command=self.prev_handler)
        self.next_btn.config(text="Next", state=next_status, command=self.next_handler)

        current_index = self.index
        is_marked_for_deletion = self.marked_for_deletion[current_index]
        is_marked_for_manual = self.marked_for_manual[current_index]

        self.mark_for_deletion_button.config(command=self.mark_for_deletion_handler)

        if is_marked_for_deletion:
            self.mark_for_deletion_button.config(text="Marked for Deletion", bg="#525252", fg="white", activebackground="white", activeforeground="#525252")
        else:
            self.mark_for_deletion_button.config(text="Mark for Deletion", bg="white", fg="black", activebackground="white", activeforeground="black")

        
        self.mark_for_manual_button.config(command=self.mark_for_manual_handler)
        
        if is_marked_for_manual:
            self.mark_for_manual_button.config(text="Marked for Manual", bg="#525252", fg="white", activebackground="white", activeforeground="#525252")
        else:
            self.mark_for_manual_button.config(text="Mark for Manual", bg="white", fg="black", activebackground="white", activeforeground="black")

        self.prev_btn.grid_forget()
        self.prev_btn.grid(row=2, column=0,  sticky=E)

        self.next_btn.grid_forget()
        self.next_btn.grid(row=2, column=3)

        self.mark_for_deletion_button.grid_forget()
        self.mark_for_deletion_button.grid(row=3, column=0)

        self.mark_for_manual_button.grid_forget()
        self.mark_for_manual_button.grid(row=3, column=1)

        self.save_button.config(command=self.save)
        self.save_button.grid_forget()
        self.save_button.grid(row=3, column=3)




root = Tk()
root.wm_title("Label Images")

app = Window(root, image_paths)

def on_closing():
    try:
        if messagebox.askyesno("Quit", "Do you want to save before closing?"):
            app.save()
            root.destroy()
        else:
            root.destroy()
    except Exception as e:
        print(e)
        root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()