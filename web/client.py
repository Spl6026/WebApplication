import time
import tkinter as tk
import numpy as np
from tkHyperlinkManager import HyperlinkManager
from tkinter import messagebox
from tkinter import filedialog
from PIL import Image, ImageTk
from functools import partial
import webbrowser
import pyautogui
import threading
import datetime
import imghdr
import socket
import pyaudio
import wave
import cv2
import os

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
name = str()
file_exist = False
photo = []
is_running = True
is_watching = True
streaming = b''
is_recording = True


def internet(HOST, PORT):
    s.connect((HOST, PORT))


def on_closing():
    if tk.messagebox.askokcancel("Quit", "Do you want to quit?"):
        try:
            s.sendall(b'|EXIT|')
            s.close()
        except:
            pass

        root.destroy()


def send():
    s.setblocking(True)
    global file_exist
    message = entry_message.get()
    if file_exist:
        s.sendall(name.encode())
        s.sendall(b'|END|')
        label_filepath.config(text="Finish!")
        file_exist = False

    else:
        s.sendall(name.encode() + b'|NAME|' + message.encode())
        s.sendall(b'|END|')
        display.insert(tk.END, 'You: ' + message + '\n')
    entry_message.delete(0, tk.END)
    s.setblocking(False)


def send_file():
    s.setblocking(True)
    global file_exist
    file_path = filedialog.askopenfilename()
    file_name = os.path.basename(file_path)
    file_extension = os.path.splitext(file_name)[1]
    file = open(file_path, "rb")
    data = file.read()
    header = b'FILE:'
    s.sendall(header)
    s.sendall(file_extension.encode() + b'|EXTENSION|')
    s.sendall(str(len(data)).encode())
    s.sendall(b'|SIZE|')
    s.sendall(data)
    s.sendall(b'|SPLIT|')
    file_exist = True
    label_filepath.config(text=file_name)
    s.setblocking(False)


def send_audio(file_path, file_name):
    s.setblocking(True)
    global file_exist
    file = open(file_path + file_name, "rb")
    data = file.read()
    header = b'FILE:'
    s.sendall(header)
    s.sendall('.wav'.encode() + b'|EXTENSION|')
    s.sendall(str(len(data)).encode())
    s.sendall(b'|SIZE|')
    s.sendall(data)
    s.sendall(b'|SPLIT|')
    file_exist = True
    label_filepath.config(text=file_name)
    s.setblocking(False)


def receive():
    global streaming
    while True:
        data = b''
        # length = 0
        try:
            while True:
                temp = s.recv(1024)
                # length += len(temp)
                # print(len(temp), length)
                if temp == b'|END|':
                    break

                data += temp

        except:
            pass

        if data:
            """
            if data.startswith(b'|STREAMING|'):
                file_data = data[11:]
                frame = cv2.cvtColor(np.array(file_data), cv2.COLOR_RGB2BGR)
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                streaming = ImageTk.PhotoImage(image=Image.fromarray(image))
            """

            if data.startswith(b'FILE:'):
                file_extension, file_data = data.split(b'|EXTENSION|')
                file_size, file_data = file_data.split(b'|SIZE|')
                file_data, file_N = file_data.split(b'|SPLIT|')
                file_extension = file_extension[5:]
                datetime_str = datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
                file_path = os.getcwd() + '\\temp\\'
                if not os.path.exists(file_path):
                    os.mkdir(file_path)

                file_name = datetime_str + file_extension.decode()
                file_path += file_name
                with open(file_path, 'wb+') as file:
                    file.write(file_data)

                file_N = file_N.split(b'|END|')

                if imghdr.what(file_path) is not None:
                    global photo
                    image = Image.open(file_path)
                    width, height = image.size
                    target_width = 200
                    target_height = int(target_width / (width / height))
                    resized_image = image.resize((target_width, target_height))
                    photo.append(ImageTk.PhotoImage(resized_image))
                    display.insert(tk.END, '{}: '.format(file_N[0].decode()) + '\n')
                    display.image_create(tk.END, image=photo[-1])
                    display.insert(tk.END, '\n')

                else:
                    display.insert(tk.END, '{}: '.format(file_N[0].decode()))
                    hyperlink = HyperlinkManager(display)
                    display.insert(tk.END,
                                   file_name,
                                   hyperlink.add(partial(webbrowser.open, f"file://{file_path}")))
                    display.insert(tk.END, '\n')

            else:
                N, message = data.split(b'|NAME|')
                message = message.split(b'|END|')
                display.insert(tk.END, '{}: '.format(N.decode()) + message[0].decode() + '\n')


def record_audio():
    global is_recording
    is_recording = True
    threading.Thread(target=recording).start()


def recording():
    chunk = 1024
    sample_format = pyaudio.paInt16
    channels = 1
    sample_rate = 44100

    audio = pyaudio.PyAudio()

    stream = audio.open(format=sample_format,
                        channels=channels,
                        rate=sample_rate,
                        frames_per_buffer=chunk,
                        input=True)

    print("Recording started...")
    frames = []

    while is_recording:
        data = stream.read(chunk)
        frames.append(data)

    print("Recording finished.")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    datetime_str = datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    audio_name = datetime_str + ".wav"
    file_path = os.getcwd() + '\\wav\\'
    if not os.path.exists(file_path):
        os.mkdir(file_path)
    # 將錄製的音訊寫入WAV檔案
    wave_file = wave.open(file_path + audio_name, 'wb')
    wave_file.setnchannels(channels)
    wave_file.setsampwidth(audio.get_sample_size(sample_format))
    wave_file.setframerate(sample_rate)
    wave_file.writeframes(b''.join(frames))
    wave_file.close()
    send_audio(file_path, audio_name)


def stop_audio():
    global is_recording
    is_recording = False


def screenshare(share, img_canvas):
    global is_running
    while is_running:
        screenshot = pyautogui.screenshot()
        width, height = screenshot.size
        target_width = 600
        target_height = int(target_width / (width / height))
        resized_screenshot = screenshot.resize((target_width, target_height))
        frame = cv2.cvtColor(np.array(resized_screenshot), cv2.COLOR_RGB2BGR)
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        tk_img = ImageTk.PhotoImage(image=Image.fromarray(image))
        data = resized_screenshot.tobytes()

        img_canvas.create_image(0, 0, image=tk_img, anchor=tk.NW)

        share.update()

    share.destroy()


def screenshare_close(share):
    global is_running
    is_running = False
    share.destroy()


def screenshare_window():
    global is_running
    is_running = True
    share = tk.Toplevel(root)
    share.geometry('600x500+200+100')
    img_canvas = tk.Canvas(share, height=400, width=600)
    record_button = tk.Button(share, text='R', command=lambda: screenshare(share, img_canvas))
    watch_button = tk.Button(share, text='W', command=lambda: watch_window(share))
    img_canvas.grid(row=0, column=0, columnspan=2)
    record_button.grid(row=1, column=0)
    watch_button.grid(row=1, column=1)
    share.protocol("WM_DELETE_WINDOW", lambda: screenshare_close(share))


def watch_close():
    global is_watching
    is_watching = False


def watch_window(share):
    global streaming
    global is_watching
    is_watching = True
    watch = tk.Toplevel(share)
    watch.geometry('600x500+200+100')
    img_canvas = tk.Canvas(watch, height=400, width=600)
    img_canvas.grid(row=0, column=0)
    watch.protocol("WM_DELETE_WINDOW", watch_close)
    while is_watching:
        """
        temp, addr = s_UDP.recvfrom(1024)
        data = b''
        while True:
            data += temp
            """
        img_canvas.create_image(0, 0, image=streaming, anchor=tk.NW)
        watch.update()

    watch.destroy()


def create():
    global name
    name = entry_name_input.get()
    IP = entry_IP_input.get()
    PORT = entry_PORT_input.get()
    internet(str(IP), int(PORT))
    root.title("Chat Room")
    label_name_input.destroy()
    entry_name_input.destroy()
    label_IP_input.destroy()
    entry_IP_input.destroy()
    label_PORT_input.destroy()
    entry_PORT_input.destroy()
    button_info.destroy()

    label_name.config(text=name)
    label_name.grid(row=0, column=0, columnspan=5, padx=0, pady=(5, 5), sticky='W')

    display.grid(row=1, column=0, rowspan=3, columnspan=5)

    label_TEXT.grid(row=4, column=0, columnspan=3, padx=0, pady=(5, 5))
    entry_message.grid(row=4, column=3, padx=0, pady=(5, 5), sticky='W')
    button_send.grid(row=4, column=4, padx=0, pady=(5, 5))

    button_file.grid(row=5, column=0, padx=0, pady=(5, 5))
    button_audio.grid(row=5, column=1, padx=0, pady=(5, 5))
    button_audio_stop.grid(row=5, column=2, padx=0, pady=(5, 5))
    label_filepath.grid(row=5, column=3)
    button_share.grid(row=5, column=4)


root = tk.Tk()

root.title('Name')

label_name_input = tk.Label(root, text="NAME: ")
label_name_input.grid(row=0, column=0, padx=(45, 3), pady=0, sticky='E')
entry_name_input = tk.Entry(root, width=25)
entry_name_input.grid(row=0, column=1, padx=(0, 70), pady=0)

label_IP_input = tk.Label(root, text="IP: ")
label_IP_input.grid(row=1, column=0, padx=(45, 3), pady=0, sticky='E')
entry_IP_input = tk.Entry(root, width=25)
entry_IP_input.grid(row=1, column=1, padx=(0, 70), pady=0)

label_PORT_input = tk.Label(root, text="PORT: ")
label_PORT_input.grid(row=2, column=0, padx=(45, 3), pady=0, sticky='E')
entry_PORT_input = tk.Entry(root, width=25)
entry_PORT_input.grid(row=2, column=1, padx=(0, 70), pady=0)

button_info = tk.Button(root, text='Send', command=create)
button_info.grid(row=3, column=0, columnspan=2)

label_name = tk.Label(root, text="")

display = tk.Text(root, height=20, width=50)

label_TEXT = tk.Label(root, text="TEXT: ")
entry_message = tk.Entry(root, width=30)
button_send = tk.Button(root, text='Send', command=send, width=5)

button_file = tk.Button(root, text='+', command=send_file)
button_audio = tk.Button(root, text='🔴', command=record_audio)
button_audio_stop = tk.Button(root, text='🟥', command=stop_audio)
label_filepath = tk.Label(root, text="")
button_share = tk.Button(root, text='🖥', command=screenshare_window, width=5)

threading.Thread(target=receive).start()
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
