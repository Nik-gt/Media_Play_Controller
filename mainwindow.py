# This Python file uses the following encoding: utf-8
import sys
import os
import threading
from threading import Thread
import time

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread, Signal
import asyncio

from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionPlaybackStatus

import tkinter as tk
from pystray import Icon, MenuItem
from PIL import Image
from win32api import GetSystemMetrics

# Класс нужен для отдельного потока, который отслеживает другие сессии медиа
class Worker(QThread):
    global_var_Changed = Signal(list)

    def __init__(self):
        super().__init__()
        self.previous_properties = None
        self.previous_status = None

    async def run_async(self):
        while True:
            media_transport_manager = None
            media_session = None
            try:
                # Запрашиваем менеджер сессий медиа-транспорта. Новый экземпляр диспетчера сеансов.
                media_transport_manager = await GlobalSystemMediaTransportControlsSessionManager.request_async()
                # Возвращает текущий сеанс, который система считает, что пользователь, скорее всего, захочет контролировать
                media_session = media_transport_manager.get_current_session()

                # активные сессии
                main_sessions = []
                media_properties = None
                if media_session is not None:
                   main_sessions.append(media_session)
                   # Получаем свойства медиа
                   media_properties = await media_session.try_get_media_properties_async()

                   # Если свойства медиа доступны, извлекаем необходимые данные
                   #    'album_artist': str,
                   #    'album_title': str,
                   #    'album_track_count': int,
                   #    'artist': str,
                   #    'genres': list,
                   #    'playback_type': int,
                   #    'subtitle': str,
                   #    'thumbnail':
                   #        <_winrt_Windows_Storage_Streams.IRandomAccessStreamReference object at ?>,
                   #    'title': str,
                   #    'track_number': int,

                   if media_properties:
                    title = media_properties.title
                    artist = media_properties.artist
                    status = media_session.get_playback_info().playback_status

                    #Проверка, на нужную сессию
                    if self.previous_properties is None and self.previous_status is None or title != self.previous_properties.title or artist != self.previous_properties.artist or status != 0 and status != self.previous_status:
                            self.previous_properties = media_properties
                            self.previous_status = status
                            # Проверяем, что автор не пустой
                            if artist:
                                main_sessions.append(f"{artist} - {title}")
                            else:
                                main_sessions.append(f"{title}")
                            #print(f"{artist} - {title}. Состояние: {status}")
                            self.global_var_Changed.emit(main_sessions)
                    else: await asyncio.sleep(0.5)  # Задержка асинхронной работы
            except Exception as e: # Обработка ошибки при получении свойств медиа
                #print(f"Ошибка при получении свойств медиа: {e}")
                #await asyncio.sleep(0.5)  # Задержка перед повторной попыткой
                continue

        await asyncio.sleep(0.2)  # Задержка асинхронной работы

    def run(self): # Создаем event loop для фонового потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)  # Устанавливаем новый event loop в этом потоке
        loop.run_until_complete(self.run_async())  # Запускаем асинхронную задачу
        loop.close()

########################################################################################################################################################################

            #https://learn.microsoft.com/en-us/uwp/api/windows.media.control.globalsystemmediatransportcontrolssession?view=winrt-26100

            #player_time = 10 #секунд
            #media_session.try_change_playback_position_async(player_time*10000000) # в тиках
            #print("Позиция 10 сек.")

            #TryChangeAutoRepeatModeAsync(MediaPlaybackAutoRepeatMode)

            #GetPlaybackInfo() #Вроде получить позицию и статус проигрывания
            #TrySkipNextAsync()
            #TrySkipPreviousAsync()


def resource_path(relative_path): #Для создания .exe файла
    try: # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MyForm(tk.Tk):
    main_sessions = None #Сессиия медиа

    finished = Signal()
    data_ready = Signal()

    def __init__(self):
        super().__init__()
        # Установка размеров окна
        self.height = 40
        self.screen_width = GetSystemMetrics(0)  # Ширина экрана
        self.width = int(self.screen_width * 0.35)
        self.x = int(self.screen_width * 0.65 - self.width / 2)  # Позиция по X
        self.y = GetSystemMetrics(1) - self.height  # Позиция по Y

        self.overrideredirect(True)  # Убираем рамку окна
        self.geometry(f"{self.width}x{self.height}+{self.x}+{self.y}")
        #self.withdraw()  # Скрываем окно при запуске

        # Убираем рамку окна и делаем его прозрачным
        self.overrideredirect(True)
        self.attributes("-topmost", True)  # Закрепляем окно на переднем плане
        self.attributes("-transparentcolor", "black")  # Делаем фон белым и прозрачным

        # Создание фрейма для кнопок
        self.button_frame = tk.Frame(self, bg="black", bd=0)  # фон для кнопок, прозрачный
        self.button_frame.pack(fill=tk.BOTH, expand=True)

        # Кнопки в один ряд
        self.icon_image = tk.PhotoImage(file=resource_path("icon\\back-wh.png"))  # путь к изображению
        self.icon_image_ds = tk.PhotoImage(file=resource_path("icon\\back-ds.png"))  # путь к изображению
        self.button1 = tk.Button(self.button_frame, command=self.on_button_previous_click, image=self.icon_image, bg="black", bd=0) #Назад

        # Изменение цвета кнопки при наведении
        self.button1.bind("<Enter>", lambda e: self.button1.config(bg="gray", fg="white") if self.button1.cget("state") != "disabled" else self.button1.config(bg="black", fg="white"))  # При наведении - серый
        self.button1.bind("<Leave>", lambda e: self.button1.config(bg="black", fg="white") if self.button1.cget("state") != "disabled" else self.button1.config(bg="black", fg="white"))# При уходе - черный
        self.button1.pack(side=tk.LEFT)

        self.icon_image2 = tk.PhotoImage(file=resource_path("icon\\pause-wh.png"))  # путь к изображению
        self.icon_image2_play = tk.PhotoImage(file=resource_path("icon\\play-wh.png"))  # путь к изображению

        self.button2 = tk.Button(self.button_frame, command=self.on_button_play_click, image=self.icon_image2, bg="black", bd=0) #Играть/Пауза
        self.button2.pack(side=tk.LEFT)
        self.button2.bind("<Enter>", lambda e: self.button2.config(bg="gray", fg="white") if self.button2.cget("state") != "disabled" else self.button2.config(bg="black", fg="white"))  # При наведении - серый
        self.button2.bind("<Leave>", lambda e: self.button2.config(bg="black", fg="white") if self.button2.cget("state") != "disabled" else self.button2.config(bg="black", fg="white"))  # При уходе - черный

        self.icon_image3 = tk.PhotoImage(file=resource_path("icon\\next-wh.png"))  # путь кизображению
        self.icon_image3_ds = tk.PhotoImage(file=resource_path("icon\\next-ds.png"))  # путь кизображению
        self.button3 = tk.Button(self.button_frame, command=self.on_button_next_click, image=self.icon_image3, bg="black", bd=0) #Далее
        self.button3.pack(side=tk.LEFT)
        self.button3.bind("<Enter>", lambda e: self.button3.config(bg="gray", fg="white") if self.button3.cget("state") != "disabled" else self.button3.config(bg="black", fg="white"))  # При наведении - серый
        self.button3.bind("<Leave>", lambda e: self.button3.config(bg="black", fg="white") if self.button3.cget("state") != "disabled" else self.button3.config(bg="black", fg="white"))  # При уходе - черный

        # Кнопка Hide, расположенная справа
        self.icon_image4 = tk.PhotoImage(file=resource_path("icon\\hide-wh.png"))  # путь кизображению
        self.button_hide = tk.Button(self.button_frame, command=self.hide_window, image=self.icon_image4, bg="black", bd=0) #Скрыть
        self.button_hide.pack(side=tk.LEFT, padx=10)
        self.button_hide.bind("<Enter>", lambda e: self.button_hide.config(bg="gray", fg="white"))  # При наведении - серый
        self.button_hide.bind("<Leave>", lambda e: self.button_hide.config(bg="black", fg="white"))  # При уходе - черный

        # Создаем Canvas, который ограничивает область видимости
        self.canvas = tk.Canvas(self, width=730, height=50, bg="black", bd=0, highlightthickness=0)
        self.canvas.place(x=160, y=10)  # Устанавливаем начальную позицию метки

        self.label = tk.Label(self.canvas, font=("Arial", 14), bg="black", fg="white", bd=0, relief="flat")
        self.label.place(x=0, y=0)  # Устанавливаем начальную позицию метки

        self.protocol("WM_DELETE_WINDOW", self.hide_window)

        #Запуск фонового потока для отслеживания медиа других приложений
        self.worker = Worker()
        self.worker.global_var_Changed.connect(self.update_global_var)
        self.worker.start()

        # Запуск потока для постоянной проверки положения окна
        self.check_topmost_thread = Thread(target=self.keep_on_top)
        self.check_topmost_thread.daemon = True
        self.check_topmost_thread.start()

        self.animation_thread =  None
        self.is_paused = False  # Флаг для приостановки анимации
        self.text_x = 0  # Начальная позиция текста, передаваемая из основного класса
        self.wait = 0.02 #Скорость анимации по умолчанию
        self.width_text_max = int(self.screen_width/4)+33 #Максимально допустимая ширина текста


    def update_global_var(self, value):
        #Запуск анимации в отдельном потоке, проверка и завершение старого потока, если он был запущен.
        self.is_paused = True
        global main_sessions
        self.main_sessions = value

        self.text = value[1]
        self.label.config(text=self.text)
        self.text_width = self.get_text_width()

        # Если текст не помещается в Label, то запускаем анимацию текста
        if self.text_width > self.width_text_max: #Сравниваем ширину текста с размером окна Canvas для вывода Label
            if self.text_width < 1000: self.wait = 0.03
            if self.text_width < 800: self.wait = 0.05
            if self.text_width < 600: self.wait = 0.07
            # Запуск анимации в отдельном потоке
            if self.animation_thread is None:
                self.animation_thread = threading.Thread(target=self.animate_text)
                self.animation_thread.daemon = True  # Поток завершится с завершением главного потока
                self.animation_thread.start()
                self.is_paused = False
            else:
                self.is_paused = False

        try:
            controls = value[0].get_playback_info().controls
            # Проверяем доступность каждой кнопки и устанавливаем кнопки по состоянию медиа
            if controls.is_previous_enabled:  # Проверка доступности кнопки предыдущего трека
                self.button1.config(state="normal", image=self.icon_image)
            else:
                self.button1.config(state="disabled", image=self.icon_image_ds, relief="flat", bd=0, highlightthickness=0, takefocus=0)  # Убираем обводку

            if controls.is_next_enabled:  # Проверка доступности кнопки следующего трека
                self.button3.config(state="normal", image=self.icon_image3)
            else: self.button3.config(state="disabled", image=self.icon_image3_ds, relief="flat", bd=0, highlightthickness=0, takefocus=0)  # Убираем обводку

            if value[0].get_playback_info().playback_status == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING:
                self.button2.config(image=self.icon_image2)
            else:
                self.button2.config(image=self.icon_image2_play)

        except Exception as e: # Обработка ошибки при получении свойств медиа кнопок
            #print(f"Ошибка при получении свойств медиа кнопок: {e}")
            return None

    #Фоновый поток для анимации текста
    def animate_text(self):
        while True:
            if not self.is_paused:
                # Сдвигаем текст по оси X
                self.text_x -= 1
                if self.text_x + self.text_width < self.width_text_max-50:  # Если текст выходит за пределы экрана
                    self.text_x = 0  # Возвращаем текст в начало

                # Обновляем метку в основном потоке с помощью after()
                self.after(0, self.label.place, {"x": self.text_x})
            else:
                self.text_x = 0
                self.after(0, self.label.place, {"x": 0})
                self.is_paused_now = True
            time.sleep(self.wait)  # Небольшая задержка для плавности анимации

    def get_text_width(self): #Получаем ширину текста в пикселях
        font = self.label.cget("font")
        return self.label.tk.call("font", "measure", font, self.text)


    def hide_window(self):
        self.withdraw()  # Скрыть окно

    def show_window(self):
        self.deiconify()  # Показать окно, когда это необходимо

    def on_button_previous_click(self):
        if self.main_sessions[0]:
            self.main_sessions[0].try_skip_previous_async()

    def on_button_play_click(self):
        if self.main_sessions[0]:
            self.main_sessions[0].try_toggle_play_pause_async()

    def on_button_next_click(self):
        if self.main_sessions[0]:
            self.main_sessions[0].try_skip_next_async()

    def keep_on_top(self):
        while True:
            self.lift()  # Попытка поднять окно на передний план
            time.sleep(0.1)  # Пауза, чтобы избежать излишней нагрузки на процессор


def on_clicked(icon, item):
    if item == "Show":
        window.show_window()  # Показать окно
    elif item == "Exit":
        icon.stop()  # Остановить иконку в трее
        window.quit()  # Завершить приложение

def setup(icon):
    icon.visible = True  # Настройка видимости иконки

# Создание меню иконки в трее
menu = (
    MenuItem("Show", lambda item: on_clicked(icon, "Show")),
    MenuItem("Exit", lambda item: on_clicked(icon, "Exit"))
)

# Создание иконки в трее
icon = Icon("media_control")

icon.icon = Image.open(resource_path("icon\\tray-icon-wh.png"))
icon.title = "Media control"
icon.menu = menu

def run_tray():
    icon.run(setup)  # Запустите иконку в трее

# Запуск иконки в отдельном потоке
tray_thread = Thread(target=run_tray)
tray_thread.start()


if __name__ == "__main__":
    # Создание приложения
    app = QApplication(sys.argv)

    window = MyForm() # Создание нового экземпляра формы
    window.mainloop()
    #sys.exit(app.exec_())
    sys.exit()
