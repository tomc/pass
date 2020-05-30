import os
import wx
import hashlib
import requests

# Global Constants



""" Sample MD5
md5_hash = hashlib.md5()

a_file = open("test.txt", "rb")
content = a_file.read()
md5_hash.update(content)

digest = md5_hash.hexdigest()
print(digest)
"""
def verifyFiles():
    dbsite = 'http://dev.forcing.club/pass/' # store items here
    files = ['D00MP','NABCseed.db']
    
    
    for i in files:
        content = ''
        md5_hash = hashlib.new('md5')
        print('Verifying',i)
        with open(i,'rb') as a_file:
            content = a_file.read()
        
        md5_hash.update(content)
    
        digest = md5_hash.hexdigest()
        web_file = requests.get(dbsite+i+'.md5')
        ook = web_file.text
        
        if ook[:32] == digest[:32]:  # trimming \n
            print("Verified ",i)
        else:
            print("Updating",i)
            r = requests.get(dbsite+i, stream = True)
            
            with open(i,"wb") as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
        

class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(800,600))
        self.Centre()
        
        self.control = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        self.CreateStatusBar() # A StatusBar in the bottom of the window

        # FavIcon
        icon = wx.Icon('./clubonly-logo.png', type=wx.BITMAP_TYPE_PNG)
        self.SetIcon(icon)

        # Setting up the menu.
        filemenu = wx.Menu()
        importmenu = wx.Menu()
        helpmenu = wx.Menu()

        # wx.ID_ABOUT and wx.ID_EXIT are standard ids provided by wxWidgets.
        menuNew = filemenu.Append(wx.ID_NEW, "&New", "New Event")
        menuOpen = filemenu.Append(wx.ID_OPEN, "&Open", "Open Event")
        menuExit = filemenu.Append(wx.ID_EXIT,"E&xit"," Terminate the program")

        menuEvent = importmenu.Append(wx.ID_ANY,"&Event List (ACBL Score)"," ACBLScore F6, Text File")
        menuLive = importmenu.Append(wx.ID_ANY,"&Live", "Import from live.acbl.org")
        
        menuFAQ = helpmenu.Append(wx.ID_ANY, "&FAQ", " Frequently Asked Questions")
        menuAbout = helpmenu.Append(wx.ID_ABOUT, "&About"," Information about this program")
        
        # Creating the menubar.
        menuBar = wx.MenuBar()
        menuBar.Append(filemenu,"&File") # Adding the "filemenu" to the MenuBar
        menuBar.Append(importmenu,"&Import")
        menuBar.Append(helpmenu,"&Help")
        self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.

        # Set events.
                
        self.Bind(wx.EVT_MENU, self.OnNew, menuNew)
        self.Bind(wx.EVT_MENU, self.OnOpen, menuOpen)
        self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)
        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)
        self.Bind(wx.EVT_MENU, self.OnEvent, menuEvent)
        self.Bind(wx.EVT_MENU, self.OnLive, menuLive)
        self.Bind(wx.EVT_MENU, self.OnFAQ, menuFAQ)

        self.Show(True)

    def OnAbout(self,e):
        # A message dialog box with an OK button. wx.OK is a standard ID in wxWidgets.
        message = """Pairs Automated Seeding Server ver 0.1.0
        
        Developed by Tom Carmichael
        See http://forcing.club/PASS for more information."""
        dlg = wx.MessageDialog( self, message, "About PASS", wx.OK)
        dlg.ShowModal() # Show it
        dlg.Destroy() # finally destroy it when finished.

    def OnExit(self,e):
        self.Close(True)  # Close the frame.
        
    def OnNew(self,e):
        pass
    
    def OnOpen(self,e):
        """ Open a file"""
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.*", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            f = open(os.path.join(self.dirname, self.filename), 'r')
            self.control.SetValue(f.read())
            f.close()
        dlg.Destroy()
        
    def OnEvent(self,e):
        pass
    
    def OnLive(self,e):
        pass
    
    def OnFAQ(self,e):
        dlg = wx.MessageDialog(self, "To Do", "Frequently Asked Questions", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

app = wx.App(False)
frame = MainWindow(None, "Pairs Automated Seeding Server (PASS)")
verifyFiles()
app.MainLoop()
