# PDFツール
from kivy import Config
Config.set("graphics","multisamples","0")
# ==================================================================================================================
# kivy 基本Widget
# ==================================================================================================================
# from typing import List
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.properties import StringProperty, ObjectProperty, ListProperty, NumericProperty
from kivy.uix.popup import Popup
# ==================================================================================================================
# デフォルトに使用するフォントを変更する(日本語対応フォントに変更)
# ==================================================================================================================
from kivy.resources import resource_add_path
from kivy.core.text import LabelBase, DEFAULT_FONT
# resource_add_path('/Users/maruki/scripts/kivy/Japanese_font')
# resource_add_path('./')
# LabelBase.register(DEFAULT_FONT, 'mplus-2c-regular.ttf') #日本語が使用できるように日本語フォントを指定する

# ==================================================================================================================
# アプリ解像度設定
# ==================================================================================================================
from kivy.core.window import Window
# Window.fullscreen = 'auto'
# Window.size = (640, 480)
Window.size = (960, 720)

from PyPDF2 import PdfFileWriter, PdfFileReader,PdfFileMerger
import os, time, sys
# 機能選択画面
class MyLayout(Screen):
    def __init__(self, **kwargs):
        super(MyLayout,self).__init__(**kwargs)

# 処理中ダイアログ
class Dialog(Widget):
    concat = ObjectProperty()
    delete_dialog = ObjectProperty()
    dialog_label = StringProperty()
    max_value = NumericProperty()
    def __init__(self, **kwargs):
        super(Dialog,self).__init__(**kwargs)
        # ジェネレータ作成
        self.gen = self.concat()
        # プログレスバー設定
        print("num:",self.max_value)
        self.ids.id_pb.max = self.max_value
        # クロックを使っているのは、PDF結合処理中にポップアップを表示できないため
        Clock.schedule_once(self.update, 0.1)
    def update(self,dt):
        try:
            index = next(self.gen)
            self.dialog_label = "{}/{}処理中…しばらくお待ち下さい".format(index,self.max_value)
            self.ids.id_pb.value = index
            Clock.schedule_once(self.update, 0.1)
        except StopIteration:
            # 完了ボタンをトーンアップ
            self.ids.id_complete_button.disabled = False
            self.dialog_label = "処理完了!"
        except:
            self.ids.id_complete_button.disabled = False
            self.dialog_label = "エラー発生。エラーコメントを確認してください。"

# PDFページ削除
class DeletePDF(Screen):
    file_path = StringProperty()
    save_name = StringProperty()
    def __init__(self, **kwargs):
        super(DeletePDF,self).__init__(**kwargs)
        self.finish_flag = 0
    
    # 処理中ダイアログ
    def show_dialog(self):
        content = Dialog(concat=self.delete,delete_dialog=self.delete_dialog,max_value=1)
        self._popup = Popup(title="処理中",content=content,size_hint=(0.8, 0.8))
        self._popup.open()

    def delete_dialog(self):
        self._popup.dismiss()

    # ページ削除
    def delete(self):
        yield 0
        infile = PdfFileReader(self.file_path, 'rb')
        output = PdfFileWriter() 

        # 暗号化確認
        check_encrypt(infile)

        # 削除ページ番号計算
        page = self.calc_page_num(self.ids.id_delete_num.text)

        # PDF作成
        for i in range(infile.getNumPages()):
            if str(i+1) in page:
                continue
            p = infile.getPage(i)
            output.addPage(p)

        # 保存ファイル名
        save_file_name = self.ids.id_save_file_name.text
        # if self.finish_flag == 0:
        try:
            with open(os.path.join(os.path.dirname(self.file_path),save_file_name), 'xb') as f: 
                output.write(f)
                # self.finish_flag = 1
        except:
            print("同名ファイルが存在します。データ上書きの可能性があるため、中止します。")
            raise Exception("[error] same name file is exist. ")
        yield 1

    def calc_page_num(self,page_num):
        # ページ番号例 2-6,8,9
        # 削除ページ番号計算
        page_temp = page_num.split(",")
        page = []
        for i in page_temp:
            temp = i.split("-")
            if len(temp)>=2:
                for i in range(int(temp[0]),int(temp[1])+1):
                    page.append(str(i))
            else:
                page += i
        print("delete page:{}".format(page_num))
        print(page_temp)
        print(page)

        return page

# PDF結合画面
class MergePDF(Screen):
    file_path = StringProperty()
    file_list = ListProperty()
    def __init__(self, **kw):
        super(MergePDF,self).__init__(**kw)

    # 処理中ダイアログ
    def show_dialog(self):
        content = Dialog(concat=self.concat,delete_dialog=self.delete_dialog,max_value=len(self.ids.id_target_file_list.text.split(",")))
        self._popup = Popup(title="処理中",content=content,size_hint=(0.8, 0.8))
        self._popup.open()

    def delete_dialog(self):
        self._popup.dismiss()

    # PDF連結
    def concat(self):
        merger = PdfFileMerger()
        print("processing...")

        # 入力されたファイルを処理対象にする
        # String型をリストに変換
        target_file_list = self.ids.id_target_file_list.text.split(",")
        print(target_file_list)
        for index,file in enumerate(target_file_list):
            yield index+1
            file_abs = os.path.join(self.file_path,file)
            # 暗号化確認
            check_encrypt(merger,file_abs)
            # マージ
            merger.append(file_abs)
        
        # 保存ファイル名
        save_file_name = self.ids.id_save_file_name.text
        save_path = os.path.join(self.file_path,save_file_name)

        try:
            with open(save_path, 'xb') as f:
                merger.write(f)
        except:
            print("同名ファイルが存在します。データ上書きの可能性があるため、中止します。")
            raise Exception("[error] same name file is exist. ")

        # merger.write(save_path)
        merger.close()
        yield 100
    
# PDF一括パスワード付与
class PasswordPDF(Screen):
    file_path = StringProperty()
    file_list = ListProperty()
    password = StringProperty()
    def __init__(self, **kwargs) -> None:
        super(PasswordPDF,self).__init__(**kwargs)

    # パスワード設定後、実行ボタンクリック
    def click_pass(self,password):
        self.password = password
        self.show_dialog()

    # 処理中ダイアログ
    def show_dialog(self):
        content = Dialog(concat=self.set_pass,delete_dialog=self.delete_dialog,max_value = len(self.file_list))
        self._popup = Popup(title="処理中",content=content,size_hint=(0.8, 0.8))
        self._popup.open()

    def delete_dialog(self):
        self._popup.dismiss()

    # パスワードを設定する
    def set_pass(self):
        print("processing...")
        yield 0
        if self.password == "":
            print("パスワードを入力してください")
            raise Exception("[error]password is not input.")

        # ファイルリスト取得
        target_file_list = self.ids.id_target_file_list.text.split(",")
        
        for index,pdf in enumerate(target_file_list):
            yield index+1
            # 絶対パス
            pdf_abs = os.path.join(self.file_path,pdf)
            
            # コピー先ファイル
            dst_pdf = PdfFileWriter()
            
            # コピー元ファイル
            src_pdf = PdfFileReader(pdf_abs)

            # 暗号化確認
            check_encrypt(src_pdf)

            # PDFをコピー
            dst_pdf.cloneReaderDocumentRoot(src_pdf)
            
            # # 作成者やタイトルといったメタデータもコピーする
            # d = {key: src_pdf.documentInfo[key] for key in src_pdf.documentInfo.keys()}
            # print("d is {}".format(d))
            # dst_pdf.addMetadata(d)

            # パスワード付与
            dst_pdf.encrypt(self.password)

            # 保存
            try:
                with open(os.path.join(self.file_path,os.path.splitext(pdf)[0]+"_password.pdf"), 'xb') as f:
                    dst_pdf.write(f)
            except:
                print("同名ファイルが存在します。データ上書きの可能性があるため、中止します。")
                raise Exception("[error] same name file is exist. ")
        yield 1000
            
# リセット
class Reset(Widget):
    def __init__(self, **kwargs):
        super(Reset,self).__init__(**kwargs)
    def reset(self):
        EditPDFApp.deletepdf.file_path   = ""
        EditPDFApp.mergepdf.file_path    = ""
        EditPDFApp.passwordpdf.file_path = ""
        EditPDFApp.mergepdf.file_list    = ""
        EditPDFApp.passwordpdf.file_list = ""
        EditPDFApp.deletepdf.save_name = ""

# 暗号化確認
def check_encrypt(pdf,file_path=""):
    if file_path != "":
        pdf = PdfFileReader(file_path)
    if pdf.isEncrypted == True:
        print("選択PDFにはパスワードがかかっている/保護されているため編集できません。パスワード/保護を解除してください。")
        raise Exception("error")

def resourcePath():
    '''Returns path containing content - either locally or in pyinstaller tmp file'''
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS)

    return os.path.join(os.path.abspath("."))

# App
class EditPDFApp(App):
    def __init__(self, **kwargs):
        super(EditPDFApp,self).__init__(**kwargs)
        # ドラッグ&ドロップ
        Window.bind(on_dropfile=self._on_dropfile)
    # ドラッグ&ドロップ時の処理
    def _on_dropfile(self,window,path):
        path = path.decode("utf-8")
        if path.endswith(".pdf"):
            self.deletepdf.file_path = path
            self.deletepdf.save_name = "deletePDF_"+os.path.basename(path)
            self.mergepdf.file_path    = "フォルダを選択してください"
            self.passwordpdf.file_path = "フォルダを選択してください"
        else:
            self.deletepdf.file_path   = "PDFファイルを選択してください"
            
            try:
                files = os.listdir(path)
                files = [i for i in files if i.endswith(".pdf")]
            # フォルダではない場合
            except:
                self.mergepdf.file_path    = "フォルダを選択してください"
                self.passwordpdf.file_path = "フォルダを選択してください"
            # フォルダの場合
            else:
                self.mergepdf.file_path    = path
                self.passwordpdf.file_path = path
                # pdfファイルが入っている(空リストはFalseを返すことを利用)
                if files:
                    self.mergepdf.file_list    = files
                    self.passwordpdf.file_list = files
                else:
                    self.mergepdf.file_list    = ["pdfファイルが見つかりません。フォルダを変更して下さい。"]
                    self.passwordpdf.file_list = ["pdfファイルが見つかりません。フォルダを変更して下さい。"]

    def build(self):
        sm = ScreenManager()
        EditPDFApp.mylayout    = MyLayout(name="opening")
        EditPDFApp.deletepdf   = DeletePDF(name="delete")
        EditPDFApp.mergepdf    = MergePDF(name="merge")
        EditPDFApp.passwordpdf = PasswordPDF(name="pass")
        sm.add_widget(EditPDFApp.mylayout)
        sm.add_widget(EditPDFApp.deletepdf)
        sm.add_widget(EditPDFApp.mergepdf)
        sm.add_widget(EditPDFApp.passwordpdf)
        EditPDFApp.reset = Reset()
        
        return sm

if __name__ == "__main__":
    resource_add_path(resourcePath())
    LabelBase.register(DEFAULT_FONT, 'mplus-2c-regular.ttf') #日本語が使用できるように日本語フォントを指定する
    EditPDFApp().run()