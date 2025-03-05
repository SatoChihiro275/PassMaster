import secrets
import pyperclip
import PySimpleGUI as sg
import datetime
import json
import os

# 保存するファイル名
FILE_NAME = "passwords.json"

# テーマのリスト
themes = sg.theme_list()

# 外部ファイルからパスワードリストを読み込む
if os.path.exists(FILE_NAME):
    with open(FILE_NAME, "r") as file:
        password_list = json.load(file)
else:
    password_list = []

# パスワードリストを表示するための関数
def update_password_list(filter_text=""):
    display_list = []
    for entry in password_list:
        if filter_text.lower() in entry["識別名"].lower() or filter_text.lower() in entry["メモ"].lower():
            display_list.append(f"{entry['作成日時']} - {entry['識別名']} - {entry['メモ']}")
    window["PASSWORD_LIST"].update(display_list)

# レイアウトを作成する関数
def create_layout():
    layout = [
        [sg.Text("パスワード生成器", font=("Helvetica", 16))],
        [sg.Text("使用する文字種", size=(15, 1))],
        [sg.Checkbox("大文字", default=True, key="USE_UPPER"),
         sg.Checkbox("小文字", default=True, key="USE_LOWER"),
         sg.Checkbox("数字", default=True, key="USE_NUMBERS"),
         sg.Checkbox("記号", default=True, key="USE_SYMBOLS")],
        [sg.Text("パスワードの文字数", size=(15, 1)), sg.InputText("16", key="LENGTH", size=(5, 1))],
        [sg.Button("パスワード生成", key="GENERATE")],
        [sg.Text("生成されたパスワード:", size=(25, 1))],
        [sg.InputText("", key="PASSWORD", readonly=True, font=("Helvetica", 12), background_color="#f0f0f0")],
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
window = sg.Window("パスワード生成器", create_layout(), finalize=True)

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

        # エラーチェック
        if password_chars == "":
            window["STATUS"].update("エラー: 少なくとも一つの文字種を選択してください。", text_color="red")
            continue

        # パスワードの文字数を取得
        try:
            password_length = int(values["LENGTH"])
            if password_length <= 0:
                raise ValueError
        except ValueError:
            window["STATUS"].update("エラー: パスワードの長さは正の整数で入力してください。", text_color="red")
            continue

        # パスワード生成と表示
        password = "".join(secrets.choice(password_chars) for _ in range(password_length))
        window["PASSWORD"].update(password)
        pyperclip.copy(password)
        window["STATUS"].update("パスワードがクリップボードにコピーされました。", text_color="green")

    if event == "SAVE":
        # パスワード保存処理
        identifier = values["IDENTIFIER"]
        memo = values["MEMO"]
        if not identifier:
            window["STATUS"].update("エラー: 識別名は必須項目です。", text_color="red")
            continue

        # 保存時の時間取得
        save_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        password_entry = {
            "識別名": identifier,
            "パスワード": values['PASSWORD'],
            "メモ": memo,
            "作成日時": save_time
        }
        password_list.append(password_entry)
        
        # 外部ファイルに保存
        with open(FILE_NAME, "w") as file:
            json.dump(password_list, file, indent=4)
        
        update_password_list(values["FILTER"])
        window["STATUS"].update("パスワードが保存されました。", text_color="green")

    if event == "DELETE":
        # パスワード削除処理
        selected_item = values["PASSWORD_LIST"]
        if selected_item:
            confirm = sg.popup_yes_no("選択したパスワードを削除しますか？")
            if confirm == "Yes":
                selected_text = selected_item[0]
                for entry in password_list:
                    if f"{entry['作成日時']} - {entry['識別名']} - {entry['メモ']}" == selected_text:
                        password_list.remove(entry)
                        break

                # 外部ファイルの更新
                with open(FILE_NAME, "w") as file:
                    json.dump(password_list, file, indent=4)
                
                update_password_list(values["FILTER"])
                window["STATUS"].update("パスワードが削除されました。", text_color="green")
        else:
            window["STATUS"].update("エラー: 削除するパスワードを選択してください。", text_color="red")

    if event == "PASSWORD_LIST" and values["PASSWORD_LIST"]:
        # 選択されたパスワードの表示処理
        selected_text = values["PASSWORD_LIST"][0]
        for entry in password_list:
            if f"{entry['作成日時']} - {entry['識別名']} - {entry['メモ']}" == selected_text:
                window["PASSWORD"].update(entry["パスワード"])
                break

    if event == "SEARCH":
        # 検索ボタンが押されたときにフィルタを適用
        update_password_list(values["FILTER"])

    if event == "APPLY_THEME":
        # テーマ変更処理
        selected_theme = values["THEME_SELECTION"]
        if selected_theme:
            sg.theme(selected_theme)
            window.close()
            # 新しいテーマでウィンドウを再生成
            window = sg.Window("パスワード生成器", create_layout(), finalize=True)
            update_password_list(values["FILTER"])

window.close()