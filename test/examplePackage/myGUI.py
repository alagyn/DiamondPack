import tkinter as tk


def main():
    root = tk.Tk()
    tk.Button(root, text="Hello", command=root.destroy).grid(row=0, column=0, padx=20, pady=20)
    root.mainloop()


if __name__ == '__main__':
    main()
