from readGSheet import get_sheets
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QLabel, QTableWidgetItem, QHeaderView, QDialog, QButtonGroup, QDialogButtonBox, QApplication, QMainWindow, QPushButton, QTableWidget, QLabel, QVBoxLayout, QWidget
import os
import webbrowser
from time import sleep
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib import cm
import numpy as np
import pandas as pd
import sys
from datetime import datetime


class DisplayWinner(QDialog):
    def __init__(self, image, parent=None):
        super().__init__(parent)
        self.setFixedWidth(500)
        self.setFixedHeight(500)
        lb = QLabel(self)
        img_path = os.path.join('ImageFiles', image + '.jpg')
        pixmap = QtGui.QPixmap(img_path, '1')
        height_label = 500
        lb.resize(self.width(), height_label)
        lb.setPixmap(pixmap.scaled(lb.size(), QtCore.Qt.IgnoreAspectRatio))


class GetResponse(QDialog):
    def __init__(self, names, song_title, parent=None):
        super().__init__(parent)
        self.names = names
        self.setWindowTitle(song_title)
        self.setFixedWidth(850)
        self.setFixedHeight(700)
        self.table = QTableWidget(len(names), len(names)+1)
        col_width = self.table.horizontalHeader()
        row_height = self.table.verticalHeader()

        self.lay = QVBoxLayout()
        self.lay.addWidget(self.table)
        self.setLayout(self.lay)

        self.ans_dict = {}
        row_ix = 0
        for name in names:
            row_height.setSectionResizeMode(row_ix, QHeaderView.ResizeToContents)

            self.btn_grp = QButtonGroup(self)
            self.btn_grp.setExclusive(True)
            self.table.setItem(row_ix, 0, QTableWidgetItem(name.split(' ')[0]))

            col_ix = 1
            for name in names:
                col_width.setSectionResizeMode(col_ix, QHeaderView.ResizeToContents)

                self.btn = QPushButton(name[:3], self)
                self.btn.clicked.connect(self.buttonClicked)

                self.btn.setCheckable(True)

                self.btn.setFixedWidth(35)
                self.btn.setFixedHeight(35)
                self.lay.addWidget(self.btn)
                self.btn_grp.addButton(self.btn)
                self.table.setCellWidget(row_ix, col_ix, self.btn)
                col_ix+=1
            row_ix+=1

        self.dialogbutton = QDialogButtonBox()
        self.dialogbutton.setOrientation(QtCore.Qt.Horizontal)
        self.dialogbutton.setStandardButtons(QDialogButtonBox.Ok)
        self.lay.addWidget(self.dialogbutton)

        self.dialogbutton.accepted.connect(self.accept)


    def buttonClicked(self):
        button = self.sender()
        r_id = self.table.indexAt(button.pos()).row()
        self.ans_dict[self.table.item(r_id, 0).text()[:3]] = [button.text()]
        self.table.item(r_id, 0).setBackground(QtGui.QColor(150,250,50))

    def accept(self):
        self.return_val = self.ans_dict
        super().accept()
        # if len(self.return_val) == len(self.names):
        #     super().accept()


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        # self.axes.set_xticklabels('Test', Fontsize=10)
        self.canvas = FigureCanvasQTAgg(self.fig)
        super(MplCanvas, self).__init__(self.fig)

    def update_figure(self, data):
        self.axes.cla()
        self.axes.bar(list(data), list(data.sum()))
        self.fig.canvas.draw()


class FirstWidget(QWidget):
    def __init__(self, sheet, vid_time, parent=None):
        super().__init__(parent)
        self.sheet = sheet
        self.scoreboard=pd.DataFrame()
        self.vid_timer = vid_time
        self.max_points = 10
        self.share_points = 5
        self.resp_df = pd.DataFrame()
        self.resp_oppath = os.path.join('DataDump', 'resp_' + datetime.now().strftime('%H%M') + '.csv')
        self.idx = 0
        self.names = np.sort(self.sheet['_Name'].unique())
        self.lay = QVBoxLayout(self)


        self.sc = MplCanvas(self, width=5, height=4, dpi=100)
        self.sc.axes.bar(['Get', 'Ready'], [1, 1])
        self.lay.addWidget(self.sc)

        playvid_btn = QPushButton("Play Video")
        playvid_btn.clicked.connect(self.on_clicked_vid)
        self.lay.addWidget(playvid_btn)

    def get_entry(self):
        entry = self.sheet.iloc[self.idx, :]
        self.idx += 1
        return entry

    def on_clicked_vid(self):
        song_entry = self.get_entry()
        resp_row = self.run_entry(song_entry)
        resp_row.rename(self.idx, inplace=True)
        self.resp_df = self.resp_df.append(resp_row)
        self.scoreboard = self.resp_df.filter(regex='^(?!_)', axis=1)
        print(self.scoreboard.sum())
        self.sc.update_figure(self.scoreboard)
        self.resp_df.to_csv(self.resp_oppath)

    def run_entry(self, song_entry):
        webbrowser.get('safari').open(song_entry['_Link'])
        sleep(self.vid_timer)
        os.system("killall -9 'Safari'")
        ans_row = self.compile_answers(ans=song_entry['_Name'], song_title=song_entry['_Song'])
        comp_row = song_entry.append(ans_row)
        return comp_row

    def compile_answers(self, ans, song_title):
        w = GetResponse(self.names, song_title)
        if w.exec_() == QDialog.Accepted:
            pass
        dw = DisplayWinner(ans.split(' ')[0])
        dw.exec_()
        ans_df = pd.DataFrame(data=w.return_val)
        resp_bool = (ans_df == ans[:3])
        resp_bool[ans[:3]] = False
        pt_df = pd.DataFrame(columns=list(ans_df))
        if True not in resp_bool.loc[0, :].value_counts():
            pt_df[ans[:3]] = [self.max_points]
            pt_df = pt_df.fillna(0)
        elif resp_bool.loc[0, :].value_counts()[True] == 1:
            pt_df = resp_bool.copy()
            pt_df[pt_df == True] = self.max_points
            pt_df[pt_df == False] = 0
        else:
            pt_df = resp_bool.copy()
            pt_df[pt_df == True] = self.share_points
            pt_df[pt_df == False] = 0
        pt_df['_Responses'] = str(w.return_val)

        return pt_df.loc[0, :]


if __name__ == '__main__':
    full, sa, sb, sc = get_sheets()
    app = QApplication(sys.argv)
    vid_time = 60
    w = FirstWidget(full, vid_time)
    w.show()
    sys.exit(app.exec_())