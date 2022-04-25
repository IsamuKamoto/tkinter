import os
import glob
import cv2
from PIL import Image, ImageTk, ImageOps
import datetime
import tkinter as tk
from tkinter import filedialog
from tkinter.font import Font
from tkinter import ttk
from tqdm import tqdm
import pyautogui as pgui
import numpy as np
import subprocess

class Tkinter():
    def __init__(self):
        self.baseGround = tk.Tk()
        # ウィンドウのサイズを設定
        self.ww, self.hh = 1920, 1080
        self.baseGround.geometry('{}x{}'.format(self.ww + 500, self.hh))
        # 画面タイトル
        self.baseGround.title('メインウィンドウ')
        # メインウィンドウの色を設定
        self.baseGround.configure(bg = 'gray15')

        self.canvas = tk.Canvas(master = self.baseGround, bg = 'black', width = self.ww, height = self.hh)
        self.canvas.place(x = 0, y = 0)

        self.canvas.bind('<Button-1>', self.canvas_left_click)
        self.canvas.bind('<Button-2>', self.finish_and_next)
        self.canvas.bind('<Button-3>', self.canvas_right_click)
        self.canvas.bind("<Escape>", self.canvas_right_click)
        self.canvas.bind("<Control-Key-z>", self.back_one_step)
        self.canvas.bind("<Control-Key-y>", self.forward_one_step)
        self.canvas.bind("<BackSpace>", self.back_one_step)
        self.canvas.pack(fill = tk.BOTH)#, expand = True)

        self.output_list = []
        self.backup_list = []
        self.output_list_world = []

        self.world_list = [[0, 9.56], [0, 0], [10.5, 0], [10.5, 9.56]]

        self.output_list_label_1 = ['左上', '左下', '右下', '右上']
        self.output_list_label_1_Eng = ['LU', 'LD', 'RD', 'RU']
        self.output_list_label_2 = ['内橋', '河田', '丸山', '大鎌', '高瀬', '福井', '萩原', '齊藤', '白石', '向井', '八木', '中村', '和田']
        self.output_list_label_2_Num = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13']
        self.color = ['red', 'red', 'red', 'red', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow']

        self.sub_window = tk.Toplevel()
        self.sub_window.title('サブウィンドウ')
        self.sub_window.geometry('1000x600')
        self.sub_frame = tk.Frame(self.sub_window)
        self.sub_frame.pack(fill = tk.BOTH, expand = True)

        reset_button = tk.Button(self.sub_frame, text = 'リセット', fg = 'red', activeforeground = 'pink', width = '5', height = '2', bg = 'khaki', activebackground = 'light goldenrod', relief = 'raised', command = self.reset_all_window)
        reset_button.place(x = 75, y = 450)
        finish_button = tk.Button(self.sub_frame, text = '終了', fg = 'black', activeforeground = 'red', width = '5', height = '2', bg = 'gray', activebackground = 'gray40', relief = 'raised', command = self.finish_and_next)
        finish_button.place(x = 175, y = 450)
        back_button = tk.Button(self.sub_frame, text = '1つ戻る', fg = 'maroon', activeforeground = 'purple', width = '5', height = '2', bg = 'gray70', activebackground = 'gray50', relief = 'raised', command = self.back_one_step)
        back_button.place(x = 275, y = 450)
        forward_button = tk.Button(self.sub_frame, text = '1つ進む', fg = 'maroon', activeforeground = 'purple', width = '5', height = '2', bg = 'gray70', activebackground = 'gray50', relief = 'raised', command = self.forward_one_step)
        forward_button.place(x = 375, y = 450)

    def chanege_img_format(self, img):
        image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # imreadはBGRなのでRGBに変換
        image_pil = Image.fromarray(image_rgb)  # RGBからPILフォーマットへ変換
        image_tk = ImageTk.PhotoImage(image_pil)  # ImageTkフォーマットへ変換
        return image_tk

    def reset_all_window(self):
        self.baseGround.destroy()
        self.__init__()
        self.main(self.img_path, self.ff_world)

    def quit(self):
        self.baseGround.destroy()

    def canvas_left_click(self, event):
        x_event, y_event = event.x, event.y
        self.output_list.append([x_event, y_event])
        if len(self.output_list) == 4:
            self.get_matrix()
        self.reload_main_window(), self.reload_sub_window()

    def get_matrix(self):
        list_screen = np.float32(self.output_list)
        list_world = np.float32(self.world_list)
        self.homography_matrix = cv2.getPerspectiveTransform(list_screen, list_world)

    def finish_and_next(self):
        self.data_output()
        self.quit()

    def back_one_step(self, event = None):
        try:
            self.backup_list.append(self.output_list)
            self.output_list = self.output_list[:-1]
        except:
            pass

    def forward_one_step(self, event = None):
        try:
            self.output_list = self.backup_list[-1]
            del self.backup_list[-1]
        except:
            pass

    def canvas_right_click(self, event):
        self.emergency_window = tk.Toplevel()
        self.emergency_window.title('作業を中止しますか？')
        self.emergency_window.geometry('500x200')
        self.emergency_frame = tk.Frame(self.emergency_window)
        self.emergency_frame.pack(fill = tk.BOTH, expand = True)
        label = tk.Label(self.emergency_frame, text = '本当にやめちゃうの…？', width = '50', anchor = tk.NW, height = '20')
        label.place(x = 130, y = 50)

        yes_button = tk.Button(self.emergency_frame, text = 'No(Yes)', fg = 'blue', activeforeground = 'purple', width = '6', height = '2', bg = 'burlywood2', activebackground = 'burlywood3', relief = 'raised', command = self.process_break)
        yes_button.place(x = 100, y = 120)
        no_button = tk.Button(self.emergency_frame, text = 'No', fg = 'red', activeforeground = 'DeepPink4', width = '6', height = '2', bg = 'burlywood2', activebackground = 'burlywood3', relief = 'raised', command = self.close_emergency)
        no_button.place(x = 300, y = 120)

    def process_break(self):
        self.baseGround.destroy()
        self.answer = False

    def close_emergency(self):
        self.emergency_window.destroy()

    def data_output(self): #CSVに書き出し
        for ii in range(4):
            output_data = [str(self.img_path), str(self.Time), str(self.output_list_label_1_Eng[ii]), str(self.output_list[ii][0]), str(self.output_list[ii][1])]
            output_data = ','.join(output_data)
            self.ff_screen.write(output_data + '\n')
        output_wold = self.output_list[4:]
        for ii in range(13):
            output_data_screen = [str(self.img_path), str(self.Time), str(self.output_list_label_2_Num[ii]), str(self.output_list[ii + 4][0]), str(self.output_list[ii + 4][1])]
            output_data_screen = ','.join(output_data_screen)
            XY = np.array([[output_wold[ii][0]], [output_wold[ii][1]], [1]])
            XYW = np.dot(self.homography_matrix, XY)
            output_XY = XYW[0] / XYW[2], XYW[1] / XYW[2]
            output_data = [str(self.img_path), str(self.Time), str(self.output_list_label_2_Num[ii]), str(output_XY[0][0]), str(output_XY[1][0])]
            output_data = ','.join(output_data)
            self.ff_world.write(output_data + '\n')
            self.ff_screen.write(output_data_screen + '\n')

    def reload_sub_window(self):
        x1, y1, dx, dy = 100, 40, 20, 40
        for ii in range(4):
            label = tk.Label(self.sub_frame, text = self.output_list_label_1[ii], width = '100', anchor = tk.W, fg = 'green')
            label.place(x = x1, y = y1 + dy * ii)
            try:
                xx, yy = self.output_list[ii][0], self.output_list[ii][1]
                value_x = tk.Label(self.sub_frame, text = str(xx), width = '120', anchor = tk.W)
                value_x.place(x = x1 + 100 + dx, y = y1 + dy * ii)
                value_y = tk.Label(self.sub_frame, text = str(yy), width = '120', anchor = tk.W)
                value_y.place(x = x1 + 220 + dx * 2, y = y1 + dy * ii)
            except:
                pass

        for ii in range(13):
            label = tk.Label(self.sub_frame, text = self.output_list_label_2[ii], width = '100', anchor = tk.W, fg = 'green')
            label.place(x = x1 + 340 + dx * 4, y = y1 + dy * ii)
            try:
                xx, yy = self.output_list[ii + 4][0], self.output_list[ii + 4][1]
                value_x = tk.Label(self.sub_frame, text = str(xx), width = '120', anchor = tk.W)
                value_x.place(x = x1 + 440 + dx * 5, y = y1 + dy * ii)
                value_y = tk.Label(self.sub_frame, text = str(yy), width = '120', anchor = tk.W)
                value_y.place(x = x1 + 560 + dx * 6, y = y1 + dy * ii)
            except:
                pass

    def reload_main_window(self):
        self.canvas.create_image(0, 0, image = self.image_tk, anchor = tk.NW)
        pgui.typewrite(['tab'])
        try:
            for ii in range(len(self.output_list)):
                color = self.color[ii]
                xx, yy = self.output_list[ii][0], self.output_list[ii][1]
                self.canvas.create_oval(xx - 2, yy - 2, xx + 2, yy + 2, fill = color)
        except:
            pass

    def main(self, IMAGE, ff_world, ff_screen):
        self.answer = True
        self.img_path = IMAGE
        self.ff_world = ff_world
        self.ff_screen = ff_screen
        self.Time = os.path.splitext(os.path.basename(IMAGE))[0]
        img = cv2.imread(IMAGE)
        img = cv2.resize(img, dsize = (self.ww, self.hh))
        self.image_tk = self.chanege_img_format(img)
        self.canvas.create_image(0, 0, image = self.image_tk, anchor = tk.NW)
        pgui.typewrite(['tab'])
        self.reload_main_window(), self.reload_sub_window()

        self.baseGround.mainloop()
        # self.sub_window.mainloop()
        return self.answer

dt_start = datetime.datetime.now()
print('開始時刻：' + dt_start.strftime('%Y年%m月%d日 %H:%M:%S'))
image_folder_path = '/Data_Drive/Time_Arrange_Data/Driving_School/20211104/Drone/Scene1/'
START = [700, 2100, 3300, 4650, 5950, 7300, 8900, 10150, 11450, 12750, 14150, 16050, 17500, 18900, 20200, 21600, 24050, 25750]
END = [1150, 2550, 3750, 5100, 6400, 7750, 9350, 10600, 11900, 13200, 14600, 16500, 17950, 19350, 20650, 22050, 24500, 26200]
phase = 'Training'
# phase = 'Main'
No = 0
start = START[No]
end = END[No]
step = 10
number = 0
images = sorted(glob.glob(image_folder_path + '*.bmp'))[start : end]
check_csv_folder_path = 'Drone_CSV/{}'.format(phase)
output_csv_path_world = check_csv_folder_path + '/World_{}_{}__{}.csv'.format(start, end, step)
output_csv_path_screen = check_csv_folder_path + '/Screen_{}_{}__{}.csv'.format(start, end, step)
with open(output_csv_path_world, 'w') as ff_world, open(output_csv_path_screen, 'w') as ff_screen:
    for ii in tqdm(range(len(images))):
        if ii % step == 0:
            answer = Tkinter().main(images[ii], ff_world, ff_screen)
            number += 1
            if answer is False:
                break
subprocess.run(['xdg-open', check_csv_folder_path])
dt_end = datetime.datetime.now()
print('終了時刻：' + dt_end.strftime('%Y年%m月%d日 %H:%M:%S'))
time = dt_end - dt_start
print('所要時間：' + str(time))
time_per_img = time / number
print('１枚毎の所要時間：' + str(time_per_img))
