import ipywidgets as widgets
import numpy as np


class EditableMatrix:
    '''
    A class to create a matrix of editable cells.

    ...

    Attributes
    ----------
    rows : int
        number of rows in the matrix
    cols : int
        number of columns in the matrix
    data : list
        initial data to be displayed in the matrix
    output : ipywidgets.Output
        output widget to display the matrix data
    onValueChange : callable
        function to be called when a cell value changes. It takes self and the change as arguments
    cellWidth : int
        width of the cell in pixels
    padding : int
        padding of the cell in pixels
    '''

    def __init__(self, rows: int, cols: int, valuesPerCell: int = 1, data=[[]], output: widgets.Output = None, onValueChange: callable = None, editableShape: bool = True, cellWidth=50, padding=10) -> None:
        self.rows = rows
        self.cols = cols
        self.valuesPerCell = valuesPerCell
        self.data = data
        self.cellWidth = cellWidth
        self.padding = padding
        self.editableShape = editableShape

        self.__create_grid()

        self.output = output
        self.onValueChange = onValueChange
        self.ValCellLabel = widgets.Label('Vals/Cell:')

    def __repr__(self) -> str:
        '''
        Returns a string representation of the object
        '''
        return f'EditableMatrix(rows={self.rows}, cols={self.cols}, valuesPerCell={self.valuesPerCell}, data={self.get_data()})'

    def __str__(self) -> str:
        '''
        Returns a string representation of the object
        '''
        return f'EditableMatrix(rows={self.rows}, cols={self.cols}, valuesPerCell={self.valuesPerCell}, data={self.get_data()})'

    def __len__(self) -> int:
        '''
        Returns the number of cells in the matrix
        '''
        return self.rows * self.cols * self.valuesPerCell

    def __getitem__(self, key):
        '''
        Returns the value of the cell at the given key

        Parameters
        ----------
        key : int or tuple
            the key to access the cell value. If it is an int, it will return the value of the row at the given index. If it is a tuple, it will return the value of the cell at the given row and column indexes
        '''
        if isinstance(key, int) and key < self.rows:
            return [self.grid.children[key].children[j].children[k].value for k in range(self.valuesPerCell) for j in range(self.cols)]
        elif isinstance(key, tuple) and len(key) <= 3:
            if len(key) == 2 and key[0] < self.rows and key[1] < self.cols:
                return [self.grid.children[key[0]].children[key[1]].children[k].value for k in range(self.valuesPerCell)]
            if len(key) == 3 and key[0] < self.rows and key[1] < self.cols and key[2] < self.valuesPerCell:
                return self.grid.children[key[0]].children[key[1]].children[key[2]].value
            raise IndexError('Invalid key')
        else:
            raise TypeError('Invalid key type')

    def __setitem__(self, key, value):
        '''
        Sets the value of the cell at the given key

        Parameters
        ----------
        key : int or tuple
            the key to access the cell value. If it is an int, it will set the value of the row at the given index. If it is a tuple, it will set the value of the cell at the given row and column indexes
        value : int or float or list
            the value to set the cell. If it is a list, it will set the values of the row at the given index
        '''
        if isinstance(key, int) and isinstance(value, list) and len(value) == self.cols and len(value[0]) == self.valuesPerCell:
            for j in range(self.cols):
                for k in range(self.valuesPerCell):
                    self.grid.children[key].children[j].children[k].value = value[j][k]

        elif isinstance(key, tuple) and isinstance(value, list):
            if len(key) == 2 and len(value) == self.valuesPerCell and key[0] < self.rows and key[1] < self.cols:
                for k in range(self.valuesPerCell):
                    self.grid.children[key[0]].children[key[1]
                                                        ].children[k].value = value[k]
            elif len(key) == 3 and key[0] < self.rows and key[1] < self.cols and key[2] < self.valuesPerCell:
                self.grid.children[key[0]].children[key[1]
                                                    ].children[key[2]].value = value
            else:
                raise IndexError('Invalid key')
        else:
            raise TypeError('Invalid key type')

    def __iter__(self):
        '''
        Returns an iterator to the cell values in the matrix
        '''
        for i in range(self.rows):
            for j in range(self.cols):
                for k in range(self.valuesPerCell):
                    yield self[i, j, k]

    def get_data(self):
        '''
        Returns the data in the matrix
        '''
        if self.valuesPerCell == 1:
            return [[self[i, j] for j in range(self.cols)] for i in range(self.rows)]

        return [[[self[i, j, k] for k in range(self.valuesPerCell)] for j in range(self.cols)] for i in range(self.rows)]

    def get_data_np(self):
        '''
        Returns the data in the matrix as a numpy array
        '''
        return np.array(self.get_data())

    def __valueInput(self, value=0):
        '''
        Creates a value input widget

        Parameters
        ----------
        value : int or float
            the initial value of the value input
        '''
        value = widgets.FloatText(
            value=value,
            placeholder='Type something',
            disabled=False,
            layout=widgets.Layout(
                width=f'{self.cellWidth}px', justify_content='center', align_items='center', text_align='center')
        )
        value.observe(self.__on_value_change, names='value')
        return value

    def __cellInput(self, value=0):
        '''
        Creates a cell input widget

        Parameters
        ----------
        value : int or float
            the initial value of the cell input
        '''
        cellInput = widgets.HBox([
            self.__valueInput(value) for i in range(self.valuesPerCell)
        ], layout=widgets.Layout(margin=f'{self.padding}px'))

        return cellInput

    def __on_value_change(self, change):
        '''
        Function to be called when a cell value changes

        Parameters
        ----------
        change : dict
            the change dictionary
        '''
        self.ValCellLabel.value = f'Vals/Cell: {self.valuesPerCell}'
        if self.onValueChange is not None:
            self.onValueChange(self, change)
            return

        if self.output is not None:
            with self.output:
                print(self.get_data())

    def __create_grid(self):
        '''
        Creates the grid of cell inputs
        '''
        if self.data == [[]]:
            self.grid = widgets.VBox([widgets.HBox(
                [self.__cellInput() for j in range(self.cols)]) for i in range(self.rows)])
        else:
            self.grid = widgets.VBox(
                [widgets.HBox([self.__cellInput(value) for value in row]) for row in self.data])

    def getActionButtons(self):
        '''
        Returns the action buttons to add and remove rows and columns
        '''
        buttonLayout = widgets.Layout(
            width='40px', height='40px', margin='5px')

        add_row_button = widgets.Button(
            icon='fa-plus-square', layout=buttonLayout)
        remove_row_button = widgets.Button(
            icon='fa-minus-square', layout=buttonLayout)
        add_column_button = widgets.Button(
            icon='fa-plus-square', layout=buttonLayout)
        remove_column_button = widgets.Button(
            icon='fa-minus-square', layout=buttonLayout)
        add_valuesPerCell_button = widgets.Button(
            icon='fa-plus-square', layout=buttonLayout)
        remove_valuesPerCell_button = widgets.Button(
            icon='fa-minus-square', layout=buttonLayout)

        add_row_button.on_click(lambda _: self.add_row())
        remove_row_button.on_click(lambda _: self.remove_row())
        add_column_button.on_click(lambda _: self.add_column())
        remove_column_button.on_click(lambda _: self.remove_column())
        add_valuesPerCell_button.on_click(
            lambda _: self.increase_values_per_cell())
        remove_valuesPerCell_button.on_click(
            lambda _: self.decrease_values_per_cell())

        row_buttons = widgets.VBox(
            [remove_row_button, add_row_button], layout=widgets.Layout(justify_content='flex-start', align_items='flex-start'))

        column_buttons = widgets.HBox(
            [remove_column_button, add_column_button], layout=widgets.Layout(justify_content='flex-start'))

        valuesPerCell_buttons = widgets.HBox(
            [remove_valuesPerCell_button, add_valuesPerCell_button], layout=widgets.Layout(justify_content='flex-start'))

        return row_buttons, column_buttons, valuesPerCell_buttons

    def get_widget(self):
        '''
        Returns the widget to display the matrix
        '''
        row_buttons, column_buttons, valuesPerCell_buttons = self.getActionButtons(
        ) if self.editableShape else (widgets.Label(""), )*3

        return widgets.GridBox(
            children=[
                widgets.Label(''),
                column_buttons,
                row_buttons,
                self.grid,
                self.ValCellLabel,
                valuesPerCell_buttons
            ],
            layout=widgets.Layout(
                grid_template_rows='auto auto auto',
                grid_template_columns='auto auto',
                justify_content='flex-start',
                align_items='flex-start',
            )
        )

    def set_disabled(self, disabled):
        '''
        Sets the disabled property of the cell inputs

        Parameters
        ----------
        disabled : bool
            the value to set the disabled property
        '''
        for i in range(self.rows):
            for j in range(self.cols):
                for value in self.grid.children[i].children[j].children:
                    value.disabled = disabled

    def add_column(self):
        '''
        Adds a column to the matrix
        '''
        for i in range(self.rows):
            cellInput = self.__cellInput()
            cellInput.observe(self.__on_value_change, names='value')
            self.grid.children[i].children += (cellInput,)

        self.cols += 1
        self.__on_value_change({'value': None})

    def remove_column(self):
        '''
        Removes a column from the matrix
        '''
        if self.cols == 1:
            return

        for i in range(self.rows):
            self.grid.children[i].children = self.grid.children[i].children[:-1]

        self.cols -= 1
        self.__on_value_change({'value': None})

    def add_row(self):
        '''
        Adds a row to the matrix
        '''
        row = []
        for j in range(self.cols):
            cellInput = self.__cellInput()
            cellInput.observe(self.__on_value_change, names='value')
            row.append(cellInput)
        self.grid.children += (widgets.HBox(row,),)
        self.rows += 1
        self.__on_value_change({'value': None})

    def remove_row(self):
        '''
        Removes a row from the matrix
        '''
        if self.rows == 1:
            return
        self.grid.children = self.grid.children[:-1]
        self.rows -= 1
        self.__on_value_change({'value': None})

    def increase_values_per_cell(self):
        '''
        Increases the number of values per cell
        '''
        for i in range(self.rows):
            for j in range(self.cols):
                valueInput = self.__valueInput()
                self.grid.children[i].children[j].children += (valueInput,)
        self.valuesPerCell += 1
        self.__on_value_change({'value': None})

    def decrease_values_per_cell(self):
        '''
        Decreases the number of values per cell
        '''
        if self.valuesPerCell == 1:
            return
        for i in range(self.rows):
            for j in range(self.cols):
                self.grid.children[i].children[j].children = self.grid.children[i].children[j].children[:-1]
        self.valuesPerCell -= 1
        self.__on_value_change({'value': None})
