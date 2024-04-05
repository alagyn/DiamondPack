import tkinter as tk
from argparse import ArgumentParser


def main():
    parser = ArgumentParser()
    parser.add_argument("--noRun", action="store_true")
    args = parser.parse_args()

    root = tk.Tk()
    tk.Button(root, text="Hello", command=root.destroy).grid(row=0, column=0, padx=20, pady=20)
    if args.noRun:
        print("GUI No-Run")
        root.update()
        root.destroy()
    else:
        print("GUI Mainloop")
        root.mainloop()


if __name__ == '__main__':
    main()
