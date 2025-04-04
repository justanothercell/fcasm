# adapted from
# https://gist.github.com/michelbl/efda48b19d3e587685e3441a74457024

import os

if os.name == 'nt':
    import msvcrt
else:
    import sys
    import termios
    import atexit
    from select import select

class Term:
    def __init__(self):
        '''
        Creates a Term object that you can call to do various keyboard things.
        '''
        if os.name != 'nt':
            self._setup_posix()

    def _setup_posix(self):
        '''
        Sets up the terminal to read non-blocking input.
        '''
        # Save the terminal settings
        self.fd = sys.stdin.fileno()
        self.new_term = termios.tcgetattr(self.fd)
        self.old_term = termios.tcgetattr(self.fd)
        # New terminal setting unbuffered
        self.new_term[3] = (self.new_term[3] & ~termios.ICANON & ~termios.ECHO)
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.new_term)
        # Support normal-terminal reset at exit
        atexit.register(self._reset_posix_term)

    def _reset_posix_term(self):
        # Resets to normal terminal. On Windows, this is a no-op.
        if os.name != 'nt':
            termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old_term)

    def getch(self):
        '''
        Returns a keyboard character after kbhit() has been called.
        '''
        if os.name == 'nt':
            return msvcrt.getch().decode('utf-8')
        else:
            return sys.stdin.read(1)

    def get_arrow(self):
        '''
        Returns an arrow-key code after kbhit() has been called. Codes are:
        0: up, 1: right, 2: down, 3: left
        '''
        if os.name == 'nt':
            msvcrt.getch()  # skip 0xE0
            c = msvcrt.getch()
            vals = [72, 77, 80, 75]
        else:
            c = sys.stdin.read(3)[2]
            vals = [65, 67, 66, 68]

        return vals.index(ord(c.decode('utf-8')))

    def kbhit(self):
        '''
        Returns True if a keyboard character was hit, False otherwise.
        '''
        if os.name == 'nt':
            return msvcrt.kbhit()
        else:
            dr, dw, de = select([sys.stdin], [], [], 0)
            return dr != []

    def __enter__(self):
        print('\x1b[?1049h', end='') # enter alt. screen
        print('\x1b[H', end='') # move to top
        print('\x1b[?25l', end='') # cursor invisible
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print('\x1b[?25h', end='') # cursor visible
        print('\x1b[?1049l', end='') # leave alt, screen
        if os.name != 'nt':
            self._reset_posix_term()
