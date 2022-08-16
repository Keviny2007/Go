import pygame as pg
import pygame_widgets
import tkinter
import tkinter.filedialog
from tkinter.filedialog import asksaveasfile

from pygame_widgets.button import Button
import math
import pickle

GRID_NUM = 19
WINDOW_SIZE = (1080, 720)
BOARD_LEN = min(WINDOW_SIZE) * 0.8
OFFSET = ((WINDOW_SIZE[0]-BOARD_LEN)/2, (WINDOW_SIZE[1]-BOARD_LEN)/2)
GRID_LEN = BOARD_LEN / (GRID_NUM-1)
CHESS_RADIUS = GRID_LEN * 0.5


class GoGame:
    def __init__(self):
        pg.init()
        self.cur_chess_color = [0, 0, 0]
        self.blackgroups: list[list[float]] = []
        self.whitegroups: list[list[float]] = []
        self.chess_girds = []
        self.window = pg.display.set_mode(WINDOW_SIZE)
        self.borad = None
        self.just_eaten = []
        self.pos_order = []
        self.draw_bg()
        self.save_button = Button(
            self.window, 50, 50, 100, 100, text='Save',
            fontSize=50, margin=20,
            inactiveColour=(255, 0, 0),
            pressedColour=(0, 255, 0), radius=20,
            onClick=self.SaveFile
        )
        self.load_button = Button(
            self.window, 50, 250, 100, 100, text='Load',
            fontSize=50, margin=20,
            inactiveColour=(255, 0, 0),
            pressedColour=(0, 255, 0), radius=20,
            onClick=self.load
        )
        self.replay_button = Button(
            self.window, 50, 450, 100, 100, text='Replay',
            fontSize=50, margin=20,
            inactiveColour=(255, 0, 0),
            pressedColour=(0, 255, 0), radius=20,
            onClick=self.load_to_replay
        )

    def save(self):
        f = open('1.pkl', 'wb')
        tmp = self.__dict__.copy()
        tmp.pop('window')
        tmp.pop('borad')
        tmp.pop('save_button')
        tmp.pop('load_button')
        pickle.dump(tmp, f, 2)
        f.close()

    def load(self):
        """Create a Tk file dialog and cleanup when finished"""
        top = tkinter.Tk()
        top.withdraw()  # hide window
        file_name = tkinter.filedialog.askopenfilename(parent=top)
        top.destroy()
        with open(file_name, 'r') as f: # read write append
            tmp = f.read()
        tmp = tmp.split('-')
        for i in range(len(tmp)):
            ls = tmp[i].split(',') # ['3','4']
            tmp[i] = (int(ls[0]), int(ls[1])) # (3, 4)

        self.__init__()
        for pos in tmp:
            self.add_chess(pos, is_mouse_pos=False)
        self.draw_bg()
        
    def SaveFile(self):
        data = [("text file(*.txt)","*.txt")]
        file = asksaveasfile(filetypes = data, defaultextension = data).name
        # file will have file name provided by user.
        # Now we can use this file name to save file.
        
        tmp = ''
        # 1,2-3,4  s.split(',')
        for pos in self.chess_girds:
            tmp += f'{pos[0]},{pos[1]}-'
        tmp = tmp[:-1]

        with open(file,"w") as f:
            f.write(tmp)

    def load_to_replay(self):
        """Create a Tk file dialog and cleanup when finished"""
        top = tkinter.Tk()
        top.withdraw()  # hide window
        file_name = tkinter.filedialog.askopenfilename(parent=top)
        top.destroy()
        with open(file_name, 'r') as f: # read write append
            tmp = f.read()
        tmp = tmp.split('-')
        for i in range(len(tmp)):
            ls = tmp[i].split(',') # ['3','4']
            tmp[i] = (int(ls[0]), int(ls[1])) # (3, 4)

        self.__init__()
        self.pos_order = tmp 
        self.idx = 0       

    def draw_bg(self):
        '''draw a background'''
        board = pg.Surface(WINDOW_SIZE)
        board.fill((242, 194, 111))

        '''draw lines to form grids'''
        for grid_x_idx in range(GRID_NUM):
            pg.draw.line(
                board,
                color=(0, 0, 0),
                start_pos=(grid_x_idx * GRID_LEN+OFFSET[0], OFFSET[1]),
                end_pos=(grid_x_idx * GRID_LEN+OFFSET[0], BOARD_LEN+OFFSET[1])
            )
        for grid_x_idx in range(GRID_NUM):
            pg.draw.line(
                board,
                color=(0, 0, 0),
                start_pos=(OFFSET[0], grid_x_idx * GRID_LEN+OFFSET[1]),
                end_pos=(BOARD_LEN+OFFSET[0], grid_x_idx * GRID_LEN+OFFSET[1])
            )

        '''draw 星位'''
        y = OFFSET[1] + GRID_LEN * 3
        x = OFFSET[0] + GRID_LEN * 3
        for i in range(3):
            for j in range(3):
                pg.draw.circle(board, (0, 0, 0), (x+i*6*GRID_LEN, y+j*6*GRID_LEN), 4)
                

        


        # draw blackgroups whitegroups
        for group in self.blackgroups:
            for grid_pos in group:
                pos = (
                    OFFSET[0] + GRID_LEN*grid_pos[0],
                    OFFSET[1] + GRID_LEN*grid_pos[1]
                )
                pg.draw.circle(board, (0, 0, 0), pos, CHESS_RADIUS)
        for group in self.whitegroups:
            for grid_pos in group:
                pos = (
                    OFFSET[0]+grid_pos[0]*GRID_LEN,
                    OFFSET[1]+grid_pos[1]*GRID_LEN
                )
                pg.draw.circle(board, (255, 255, 255), pos, CHESS_RADIUS)

        '''draw background to the screen'''
        self.window.blit(board, (0, 0))
        self.borad = board

    def add_chess(self, pos_: list[float], is_mouse_pos: bool=True):
        '''draw a chess based on player's mouse position'''
        # update
        # self.blackgroups
        # self.whitegroups
        # self.chess_girds
        if is_mouse_pos:
            grid_pos = (
                round((pos_[0]-OFFSET[0]) / GRID_LEN),
                round((pos_[1]-OFFSET[1]) / GRID_LEN)
            )
        else:
            grid_pos = pos_

        # check in board
        if grid_pos[0] not in range(19) or grid_pos[1] not in range(19):
            return
        
        # check if there's already a chess (occupied)
        if self.occupied(grid_pos):
            return

        # check if just eaten
        if len(self.just_eaten)==1 and grid_pos in self.just_eaten:
            return
        
        # check if replaying
        if self.pos_order != []: # replaying
            if self.idx >= len(self.pos_order) or grid_pos != self.pos_order[self.idx]:
                return       
            else:
                self.idx+=1

        self.chess_girds.append(grid_pos)

        # append into chess groups
        if self.cur_chess_color[0] == 0:
            # black
            tmp = [x.copy() for x in self.blackgroups]
            # if current postion is neighborhood of some existing group
            merged_group = [grid_pos]
            for group in self.blackgroups[::-1]:

                for pos in group:
                    candidates = [
                        (pos[0], pos[1]+1),
                        (pos[0], pos[1]-1),
                        (pos[0]+1, pos[1]),
                        (pos[0]-1, pos[1]),
                    ]
                    if grid_pos in candidates:
                        # new pos is neighborhood of current group
                        self.blackgroups.remove(group)
                        merged_group += group
                        break

            self.blackgroups.append(merged_group) # lay the black chess
            if self.eat_whitegroups():
                pass
            elif self.can_eat_blackgroups():
                self.chess_girds.pop(-1)
                self.blackgroups=tmp
                return

        else:
            # white
            # if current postion is neighborhood of some existing group
            merged_group = [grid_pos]
            tmp = [x.copy() for x in self.whitegroups]
            for group in self.whitegroups[::-1]:

                for pos in group:
                    candidates = [
                        (pos[0], pos[1]+1),
                        (pos[0], pos[1]-1),
                        (pos[0]+1, pos[1]),
                        (pos[0]-1, pos[1]),
                    ]
                    if grid_pos in candidates:
                        # new pos is neighborhood of current group
                        self.whitegroups.remove(group)
                        merged_group += group
                        break

            self.whitegroups.append(merged_group)
            if self.eat_blackgroups():
                pass
            elif self.can_eat_whitegroups():
                self.chess_girds.pop(-1)
                self.whitegroups=tmp
                return

        self.cur_chess_color = [255-x for x in self.cur_chess_color]
        

    def eat_whitegroups(self) -> bool:
        self.just_eaten = []
        length = len(self.whitegroups)
        have_eaten = False
        for idx, group in enumerate(self.whitegroups[::-1]):
            idx = length-1-idx
            # 白棋的group
            can_eat_cur_group = True
            for pos in group:
                if not can_eat_cur_group:
                    break
                candidates = [
                    (pos[0], pos[1]+1),
                    (pos[0], pos[1]-1),
                    (pos[0]+1, pos[1]),
                    (pos[0]-1, pos[1]),
                ]

                for candidate in candidates[::-1]:
                    for cord in candidate:
                        if cord not in range(19):
                            candidates.remove(candidate)

                # candidates是不是都有棋子
                for candidate in candidates:
                    if not self.occupied(candidate):  # 如果有一个邻居没有棋子，则group不可能被吃
                        can_eat_cur_group = False
                        break
            if can_eat_cur_group:
                self.just_eaten += self.whitegroups.pop(idx)  # list addtion
                have_eaten = True
        
        return have_eaten

    def eat_blackgroups(self) -> bool:
        self.just_eaten = []
        length = len(self.blackgroups)
        have_eaten = False
        for idx, group in enumerate(self.blackgroups[::-1]):
            idx = length-1-idx
            # 白棋的group
            can_eat_cur_group = True
            for pos in group:
                if not can_eat_cur_group:
                    break
                candidates = [
                    (pos[0], pos[1]+1),
                    (pos[0], pos[1]-1),
                    (pos[0]+1, pos[1]),
                    (pos[0]-1, pos[1]),
                ]

                for candidate in candidates[::-1]:
                    for cord in candidate:
                        if cord not in range(19):
                            candidates.remove(candidate)

                # candidates是不是都有棋子
                for candidate in candidates:
                    if not self.occupied(candidate):  # 如果有一个邻居没有棋子，则group不可能被吃
                        can_eat_cur_group = False
                        break
            if can_eat_cur_group:
                self.just_eaten += self.blackgroups.pop(idx)
                have_eaten = True
        
        return have_eaten

    def can_eat_blackgroups(self) -> bool:
        length = len(self.blackgroups)
        have_eaten = False
        for idx, group in enumerate(self.blackgroups[::-1]):
            idx = length-1-idx
            # 白棋的group
            can_eat_cur_group = True
            for pos in group:
                if not can_eat_cur_group:
                    break
                candidates = [
                    (pos[0], pos[1]+1),
                    (pos[0], pos[1]-1),
                    (pos[0]+1, pos[1]),
                    (pos[0]-1, pos[1]),
                ]

                # candidates是不是都有棋子
                for candidate in candidates:
                    if not self.occupied(candidate):  # 如果有一个邻居没有棋子，则group不可能被吃
                        can_eat_cur_group = False
                        break
            if can_eat_cur_group:
                return True

        return have_eaten

    def can_eat_whitegroups(self) -> bool:
        length = len(self.whitegroups)
        have_eaten = False
        for idx, group in enumerate(self.whitegroups[::-1]):
            idx = length-1-idx
            # 白棋的group
            can_eat_cur_group = True
            for pos in group:
                if not can_eat_cur_group:
                    break
                candidates = [
                    (pos[0], pos[1]+1),
                    (pos[0], pos[1]-1),
                    (pos[0]+1, pos[1]),
                    (pos[0]-1, pos[1]),
                ]

                # candidates是不是都有棋子
                for candidate in candidates:
                    if not self.occupied(candidate):  # 如果有一个邻居没有棋子，则group不可能被吃
                        can_eat_cur_group = False
                        break
            if can_eat_cur_group:
                return True
        
        return have_eaten

    def occupied(self, pos):
        for group in self.whitegroups:
            for pos_ in group:
                if pos_ == pos:
                    return True
        for group in self.blackgroups:
            for pos_ in group:
                if pos_ == pos:
                    return True
        return False

    def run(self):

        while 1:
            events = pg.event.get()
            for event in events:

                if event.type == pg.QUIT:
                    # player quit game
                    return

                if event.type == pg.MOUSEBUTTONDOWN:
                    # lay a chess
                    self.add_chess(pg.mouse.get_pos())
                    self.draw_bg()

            font = pg.font.SysFont(None, 24)
            img = font.render('hello', True, "BLUE")
            self.window.blit(img, (500, 500))

            self.window.blit(self.borad, (0, 0))
            pg.draw.circle(self.window, self.cur_chess_color,
                           pg.mouse.get_pos(), CHESS_RADIUS)
            pygame_widgets.update(events)
            pg.display.update()


if __name__ == "__main__":
    # create an instance
    gogame = GoGame()
    gogame.run()
