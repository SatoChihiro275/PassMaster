import secrets
import pyperclip
import PySimpleGUI as sg
import datetime
import json
import os
import re
from cryptography.fernet import Fernet

# 暗号化キーを生成または読み込む
KEY_FILE = "secret.key"
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, "rb") as key_file:
        key = key_file.read()
else:
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as key_file:
        key_file.write(key)
cipher = Fernet(key)

# 保存するファイル名
FILE_NAME = "passwords.json"

# テーマのリスト
themes = sg.theme_list()

# 外部ファイルからパスワードリストを読み込む
if os.path.exists(FILE_NAME):
    with open(FILE_NAME, "rb") as file:
        encrypted_data = file.read()
        if encrypted_data:
            decrypted_data = cipher.decrypt(encrypted_data).decode()
            password_list = json.loads(decrypted_data)
        else:
            password_list = []
else:
    password_list = []

# パスワードリストを表示するための関数
def update_password_list(filter_text=""):
    display_list = []
    for entry in password_list:
        if filter_text.lower() in entry["識別名"].lower() or filter_text.lower() in entry["メモ"].lower():
            display_list.append(f"{entry['作成日時']} - {entry['識別名']} - {entry['メモ']}")
    window["PASSWORD_LIST"].update(display_list)

# パスワード強度を評価する関数
def evaluate_password_strength(password):
    length_score = len(password) / 8  
    variety_score = (len(set(re.findall(r'[A-Z]', password))) > 0) +\
                    (len(set(re.findall(r'[a-z]', password))) > 0) +\
                    (len(set(re.findall(r'[0-9]', password))) > 0) +\
                    (len(set(re.findall(r'[!@#\$%\^&\*\(\)_\+\-=\[\]{};:\'",<>\./?]', password))) > 0)
    variety_score /= 4

    score = length_score + variety_score

    if score > 1.5:
        return "強い", "green"
    elif score > 1.0:
        return "普通", "orange"
    else:
        return "弱い", "red"

# レイアウトを作成する関数
def create_layout():
    layout = [
        [sg.Text("PassMaster", font=("Helvetica", 16))],
        [sg.Text("使用する文字種", size=(15, 1))],
        [sg.Checkbox("大文字", default=True, key="USE_UPPER"),
         sg.Checkbox("小文字", default=True, key="USE_LOWER"),
         sg.Checkbox("数字", default=True, key="USE_NUMBERS"),
         sg.Checkbox("記号", default=True, key="USE_SYMBOLS")],
        [sg.Text("パスワードの文字数", size=(15, 1)), sg.InputText("16", key="LENGTH", size=(5, 1))],
        [sg.Button("パスワード生成", key="GENERATE")],
        [sg.Text("パスワード:", size=(25, 1))],
        [sg.InputText("", key="PASSWORD", font=("Helvetica", 12), background_color="#f0f0f0", enable_events=True)],
        [sg.Text("強度:", size=(10, 1)), sg.Text("", key="STRENGTH", font=("Helvetica", 12))],
        [sg.Text("識別名 *", size=(15, 1)), sg.InputText(key="IDENTIFIER")],
        [sg.Text("メモ", size=(15, 1)), sg.InputText(key="MEMO")],
        [sg.Text("テーマ選択", size=(15, 1)), sg.Combo(themes, key="THEME_SELECTION", readonly=True), sg.Button("適用", key="APPLY_THEME")],
        [sg.Button("保存する", key="SAVE")],
        [sg.Text("ステータス", size=(15, 1)), sg.Text("", key="STATUS", font=("Helvetica", 10), background_color="yellow")],
        [sg.Text("検索フィルタ", size=(15, 1)), sg.InputText("", key="FILTER"), sg.Button("検索", key="SEARCH")],
        [sg.Listbox(values=[], size=(60, 10), key="PASSWORD_LIST", enable_events=True)],
        [sg.Button("削除", key="DELETE")],
    ]
    return layout

# 初期ウィンドウの作成
window = sg.Window("PassMaster", create_layout(), finalize=True)

# 初期表示のためにリストを更新
update_password_list()

# イベントループ
while True:
    event, values = window.read()

    if event == sg.WINDOW_CLOSED:
        break

    if event == "GENERATE":
        # パスワードを生成する処理
        password_chars = ""
        if values["USE_UPPER"]:
            password_chars += "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if values["USE_LOWER"]:
            password_chars += "abcdefghijklmnopqrstuvwxyz"
        if values["USE_NUMBERS"]:
            password_chars += "0123456789"
        if values["USE_SYMBOLS"]:
            password_chars += "#!@_-"

        if password_chars == "":
            window["STATUS"].update("エラー: 少なくとも一つの文字種を選択してください。", text_color="red")
            continue

        try:
            password_length = int(values["LENGTH"])
            if password_length <= 0:
                raise ValueError
        except ValueError:
            window["STATUS"].update("エラー: パスワードの長さは正の整数で入力してください。", text_color="red")
            continue

        password = "".join(secrets.choice(password_chars) for _ in range(password_length))
        window["PASSWORD"].update(password)
        pyperclip.copy(password)
        window["STATUS"].update("パスワードがクリップボードにコピーされました。", text_color="green")

        strength, color = evaluate_password_strength(password)
        window["STRENGTH"].update(strength, text_color=color)

    if event == "SAVE":
        # パスワード保存処理
        password = values["PASSWORD"]
        identifier = values["IDENTIFIER"]
        memo = values["MEMO"]
        if not identifier:
            window["STATUS"].update("エラー: 識別名は必須項目です。", text_color="red")
            continue

        if not password:
            window["STATUS"].update("エラー: パスワードを入力するか生成してください。", text_color="red")
            continue

        save_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        password_entry = {
            "識別名": identifier,
            "パスワード": password,
            "メモ": memo,
            "作成日時": save_time
        }
        password_list.append(password_entry)
        
        # 外部ファイルに暗号化して保存
        data_to_save = json.dumps(password_list).encode()
        encrypted_data = cipher.encrypt(data_to_save)
        with open(FILE_NAME, "wb") as file:
            file.write(encrypted_data)
        
        update_password_list(values["FILTER"])
        window["STATUS"].update("パスワードが保存されました。", text_color="green")

    if event == "DELETE":
        selected_item = values["PASSWORD_LIST"]
        if selected_item:
            confirm = sg.popup_yes_no("選択したパスワードを削除しますか？")
            if confirm == "Yes":
                selected_text = selected_item[0]
                for entry in password_list:
                    if f"{entry['作成日時']} - {entry['識別名']} - {entry['メモ']}" == selected_text:
                        password_list.remove(entry)
                        break

                data_to_save = json.dumps(password_list).encode()
                encrypted_data = cipher.encrypt(data_to_save)
                with open(FILE_NAME, "wb") as file:
                    file.write(encrypted_data)
                
                update_password_list(values["FILTER"])
                window["STATUS"].update("パスワードが削除されました。", text_color="green")
        else:
            window["STATUS"].update("エラー: 削除するパスワードを選択してください。", text_color="red")

    if event == "PASSWORD_LIST" and values["PASSWORD_LIST"]:
        selected_text = values["PASSWORD_LIST"][0]
        for entry in password_list:
            if f"{entry['作成日時']} - {entry['識別名']} - {entry['メモ']}" == selected_text:
                window["PASSWORD"].update(entry["パスワード"])
                break

    if event == "SEARCH":
        update_password_list(values["FILTER"])

    if event == "APPLY_THEME":
        selected_theme = values["THEME_SELECTION"]
        if selected_theme:
            sg.theme(selected_theme)
            window.close()
            window = sg.Window("PassMaster", create_layout(), finalize=True)
            update_password_list(values["FILTER"])

    if event == "PASSWORD":
        password = values["PASSWORD"]
        strength, color = evaluate_password_strength(password)
        window["STRENGTH"].update(strength, text_color=color)

window.close()