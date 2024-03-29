from dataclasses import field
from enum import Flag
from multiprocessing.dummy import Array
from re import sub
import tkinter
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import os
from tokenize import String
import glob
import subprocess
import log_adjust6

def quit():
    global window
    window.destroy()

def make_app():
    global frame1, frame2, frame3, frame4
    frame3.destroy()
    frame4.destroy()
    frame1 = ttk.Frame(window, padding=10)
    frame1.grid()
    frame2 = ttk.Frame(window, padding=10)
    frame2.grid()
    btn = ttk.Button(frame2, text="開始", command=click_start_button)
    btn.grid(row=0, column=0)
    lbl = ttk.Label(frame1, text="実行したいファイルを選択してください", font=("meiryo", 12))
    lbl.grid(row=0, column=0)
    refer_button = ttk.Button(frame1, text=u'参照', command=click_refer_button)
    refer_button.grid(row=1, column=1)
    file_path=StringVar()
    flfld = ttk.Entry(frame1, textvariable=file_path, width=70)
    flfld.grid(row=1, column=0)

def change_result(state):
    global frame3, frame4, flag
    frame1.destroy()
    frame2.destroy()
    frame3 = ttk.Frame(window, padding=10)
    frame4 = ttk.Frame(window, padding=10)
    frame3.grid(row=0, column=0)
    frame4.grid(row=1, column=1)
    if flag is True:
        lbl1 = ttk.Label(frame3, text="いずれかの処理に失敗しました。", font=("meiryo", 12))
        lbl2 = ttk.Label(frame3, text="作成者にお問い合わせください。 エラーコード" + str(state), font=("meiryo", 12))
        btn1 = ttk.Button(frame4, text=u'戻る', command = make_app)
        btn2 = ttk.Button(frame4, text=u'終了', command = quit)
        lbl1.pack()
        lbl2.pack()
        btn1.grid(row=0, column=0)
        btn2.grid(row=0, column=1)
        flag = False
    else:
        lbl = ttk.Label(frame3, text="すべての処理を正常に終了しました。", font=("meiryo", 12))
        btn1 = ttk.Button(frame4, text=u'戻る', command = make_app)
        btn2 = ttk.Button(frame4, text=u'終了', command = quit)
        lbl.pack()
        btn1.grid(row=0, column=0)
        btn2.grid(row=0, column=1)

def click_refer_button():
    global filepath
    fType = [("","*")]
    iDir = os.path.abspath(os.path.dirname(__file__))
    filepath = filedialog.askopenfilenames(filetypes = fType, initialdir = iDir)
    file_path.set(filepath)

def change_flag():
    global flag
    flag = True

def click_start_button():
    #print(file_path.get())
    for f in (filepath):
        state = log_adjust6.main(f)
        if state !=0:
            change_flag()
            continue
    change_result(state)

    

if __name__ == '__main__':
    flag = False
    window = Tk()
    window.title('ログ整理')
    window.geometry("540x300+10+20")
    frame1 = ttk.Frame(window, padding=10)
    frame1.grid()
    frame2 = ttk.Frame(window, padding=10)
    frame2.grid()
    btn = ttk.Button(frame2, text="開始", command=click_start_button)
    btn.grid(row=0, column=0)
    lbl = ttk.Label(frame1, text="実行したいファイルを選択してください", font=("meiryo", 12), )
    lbl.grid(row=0, column=0)
    refer_button = ttk.Button(frame1, text=u'参照', command=click_refer_button)
    refer_button.grid(row=1, column=1)
    file_path=StringVar()
    flfld = ttk.Entry(frame1, textvariable=file_path, width=70)
    flfld.grid(row=1, column=0)
    window.mainloop()
