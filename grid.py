import numpy as np
from unit import Unit
"""
Grid class is created to keep track of the main grid,
it has rows cols and 2D grid array which obtains Units
the str methods for all of the code is written to debug the code since it is hard to debug in parallel programming

"""
class Grid:
    def __init__(self,rows,cols):
        self.rows=rows
        self.cols=cols
        self.grid = np.array([[Unit() for _ in range(cols)] for _ in range(rows)], dtype=object)

    def get(self, row, col):
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.grid[row][col]
        else:
            raise IndexError("Index out of bounds")

    def set(self, row, col,  unit):
        if 0 <= row < self.rows and 0 <= col < self.cols and self.grid[row][col].unit_type=="neutral":
            self.grid[row][col] =  unit
        else:
            raise IndexError("Index out of bounds")

    def __str__(self):
        return '\n'.join([' '.join([str(cell) for cell in row]) for row in self.grid])
