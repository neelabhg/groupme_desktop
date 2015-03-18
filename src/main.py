import urllib.request
import urllib.parse
from io import BytesIO

import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin
import wx.lib.agw.ultimatelistctrl as ulc
import wx.html2
from wx.lib.wordwrap import wordwrap
import groupy
import groupy.config

from src import config


class GroupList(wx.ListBox):
    def __init__(self, parent):
        self.parent = parent
        super(GroupList, self).__init__(self.parent)
        self.setup_ui()

    def setup_ui(self):
        pass

    def refresh_data(self):
        self.populate_groups()

    def set_on_select_handler(self, handler):
        def on_select(event):
            selected_group_obj = self.GetClientData(self.GetSelection())
            handler(selected_group_obj)
        self.Bind(wx.EVT_LISTBOX, on_select)

    def populate_groups(self):
        # http://www.blog.pythonlibrary.org/2010/12/16/wxpython-storing-object-in-combobox-or-listbox-widgets/
        groups = groupy.Group.list()
        for group in groups:
            self.Append(group.name, group)


class GroupImage(wx.StaticBitmap):
    def __init__(self, parent):
        self.parent = parent
        self.image = None
        super(GroupImage, self).__init__(self.parent)
        self.setup_ui()

    def setup_ui(self):
        self.setup_handlers()

    def setup_handlers(self):
        self.Bind(wx.EVT_SIZE, self.on_resize)

    def on_resize(self, event):
        self.Refresh()
        if self.image is not None:
            #width = self.GetSize()[0]
            #self.image = self.image.Scale(width, width)
            #self.SetBitmap(self.image.ConvertToBitmap())
            pass
        event.Skip(True)

    def load_image_url(self, url):
        # http://stackoverflow.com/a/20764507/2193410 (wx.Image from image URL)
        self.SetBitmap(wx.Bitmap())
        if url is not None:
            with urllib.request.urlopen(url) as resp:
                stream = BytesIO(resp.read())
                self.image = wx.Image(stream).Scale(200, 200)
                self.SetBitmap(self.image.ConvertToBitmap())
        self.parent.Fit()


class GroupInfo(wx.Panel):
    def __init__(self, parent):
        self.parent = parent
        self.group = None
        self.group_img_box = None
        self.group_members_list_box = None
        super(GroupInfo, self).__init__(self.parent)
        self.setup_ui()

    def setup_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        self.group_img_box = GroupImage(self)
        self.group_members_list_box = wx.ListBox(self)
        sizer.AddMany([
            (self.group_img_box, 0, wx.CENTER),
            (self.group_members_list_box, 1, wx.EXPAND)
        ])

    def refresh_data(self):
        self.load_group_info(self.group)

    def load_group_info(self, group):
        if group is not None:
            self.group = group
            self.group_img_box.load_image_url(self.group.image_url)
            self.group_members_list_box.Clear()
            self.group_members_list_box.InsertItems(
                list(map(lambda m: m.nickname, group.members())), 0)


class ChatInputPanel(wx.Panel):
    def __init__(self, parent):
        self.parent = parent
        self.input_box = None
        self.send_button = None
        super(ChatInputPanel, self).__init__(self.parent)
        self.setup_ui()

    def setup_ui(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(sizer)
        self.input_box = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        #smiley_button = wx.Button(self, label='S')
        #attach_button = wx.Button(self, label='A')
        self.send_button = wx.Button(self, label='Send')
        sizer.AddMany([
            (self.input_box, 1, wx.LEFT | wx.EXPAND),
            #smiley_button,
            #attach_button,
            (self.send_button, 0, wx.RIGHT | wx.EXPAND)
        ])

    def setup_handlers(self, group):
        def send_message(event):
            text = self.input_box.GetValue()
            if text:
                if group.post(text):
                    self.input_box.Clear()

        self.send_button.Bind(wx.EVT_BUTTON, send_message)
        self.input_box.Bind(wx.EVT_TEXT_ENTER, send_message)


class ChatMessageList(ulc.UltimateListCtrl, ListCtrlAutoWidthMixin):
    def __init__(self, parent):
        self.parent = parent
        self.group = None
        super(ChatMessageList, self).__init__(self.parent, agwStyle=ulc.ULC_REPORT | ulc.ULC_HAS_VARIABLE_ROW_HEIGHT)
        ListCtrlAutoWidthMixin.__init__(self)
        self.setResizeColumn(2)
        self.setup_ui()

    def setup_ui(self):
        self.InsertColumn(0, 'name')
        self.InsertColumn(1, 'message')
        self.InsertColumn(2, 'likes')

    def refresh_data(self):
        self.load_messages(self.group)

    def load_messages(self, group):
        if group is not None:
            self.group = group
            self.DeleteAllItems()
            message_text_width = self.GetColumnWidth(1) - 10
            for message in group.messages():
                index = self.InsertStringItem(0, message.name)
                text = message.text
                if text is None:
                    text = 'Attachment'
                try:
                    text.encode('charmap')
                except UnicodeEncodeError:
                    text = '<Message contains unknown characters>'
                text = wordwrap(text, message_text_width, wx.ClientDC(self))
                self.SetStringItem(index, 1, text)
                likes = str(len(message.favorited_by))
                if likes == '0':
                    likes = ''
                self.SetStringItem(index, 2, likes)
            self.EnsureVisible(self.GetItemCount() - 1)
            #self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
            self.Update()


class MainWindow(wx.Panel):
    def __init__(self, parent):
        super(MainWindow, self).__init__(parent)
        self.parent = parent
        self.group_list_box = None
        self.group_info_panel = None
        self.message_list = None
        self.chat_input_box = None
        self.setup_ui()

    def setup_ui(self):
        column_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(column_sizer)
        left_panel = wx.Panel(self)
        center_panel = wx.Panel(self)
        right_panel = wx.Panel(self)
        column_sizer.AddMany([
            (left_panel, 1, wx.EXPAND),
            (center_panel, 3, wx.EXPAND),
            (right_panel, 1, wx.EXPAND)
        ])

        self.setup_left_panel(left_panel)
        self.setup_right_panel(right_panel)
        self.setup_center_panel(center_panel)
        self.setup_handlers()

    def setup_left_panel(self, panel):
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)
        self.group_list_box = GroupList(panel)
        sizer.Add(self.group_list_box, 1, wx.EXPAND)

    def setup_right_panel(self, panel):
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)
        self.group_info_panel = GroupInfo(panel)
        sizer.Add(self.group_info_panel, 1, wx.EXPAND)

    def setup_center_panel(self, panel):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel.SetSizer(sizer)
        chat_splitter_window = wx.SplitterWindow(panel)
        self.message_list = ChatMessageList(chat_splitter_window)
        self.chat_input_box = ChatInputPanel(chat_splitter_window)
        sizer.Add(chat_splitter_window, 1, wx.EXPAND)
        chat_splitter_window.SplitHorizontally(self.message_list, self.chat_input_box, -70)
        chat_splitter_window.SetMinimumPaneSize(70)
        chat_splitter_window.SetSashGravity(1.0)  # Input pane should not grow on resize

    def setup_handlers(self):
        self.group_list_box.set_on_select_handler(self.group_selected)

    def group_selected(self, group):
        self.group_info_panel.load_group_info(group)
        self.message_list.load_messages(group)
        self.chat_input_box.setup_handlers(group)

    def refresh_data(self):
        self.group_list_box.refresh_data()
        self.group_info_panel.refresh_data()
        self.message_list.refresh_data()


class LoginDialog(wx.Dialog):
    # Dialog code adapted from http://www.blog.pythonlibrary.org/2014/07/11/wxpython-how-to-create-a-login-dialog/
    # WebView code adapted from https://github.com/wxWidgets/Phoenix/blob/master/samples/html2/HTML2_WebView.py
    def __init__(self):
        super(LoginDialog, self).__init__(None, title='GroupMe Desktop - Login to GroupMe', size=(500, 400))
        self.wv = None
        self.access_token = None
        self.setup_ui()
        self.Center()

    def setup_ui(self):
        self.wv = wx.html2.WebView.New(self)
        self.Bind(wx.html2.EVT_WEBVIEW_NAVIGATED, self.on_web_view_navigated, self.wv)
        self.wv.LoadURL(config.redirect_url)

    def on_web_view_navigated(self, event):
        url = event.GetURL()
        if config.callback_url in url:
            if self.extract_token(url):
                self.Close()
            else:
                self.wv.LoadURL(config.redirect_url)

    def extract_token(self, url):
        params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        try:
            self.access_token = params['access_token'][0]
            return True
        except (KeyError, IndexError):
            return False


class Application(wx.Frame):
    def __init__(self):
        super(Application, self).__init__(None, title='GroupMe Desktop', size=(1000, 600))
        self.wx_config = wx.Config('GroupMeDesktop')
        if not self.login():
            self.Close()
            return

        MainWindow(self).refresh_data()
        self.Center()
        self.Show()

    def login(self):
        access_token = self.wx_config.Read('groupme_access_token')
        self.set_groupy_access_token(access_token)
        if self.is_logged_in():
            return True
        login_dialog = LoginDialog()
        login_dialog.ShowModal()
        login_dialog.Destroy()
        access_token = login_dialog.access_token
        if access_token:
            self.set_groupy_access_token(access_token)
            self.wx_config.Write('groupme_access_token', access_token)
            return True
        return False

    @staticmethod
    def set_groupy_access_token(token):
        groupy.config.API_KEY = token

    @staticmethod
    def is_logged_in():
        try:
            groupy.User.get()
            return True
        except groupy.api.errors.ApiError:
            return False

if __name__ == '__main__':
    app = wx.App()
    Application()
    app.MainLoop()
