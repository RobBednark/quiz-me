class FuzzyInt(int):
    '''
    Django has 'assertNumQueries'. Here is how to do fuzzy testing
    with this function, using a subclass of int.  To use it, e.g.,
        with self.assertNumQueries(FuzzyInt(5,8)):
    '''
    def __new__(cls, lowest, highest):
        obj = super(FuzzyInt, cls).__new__(cls, highest)
        obj.lowest = lowest
        obj.highest = highest
        return obj

    def __eq__(self, other):
        return other >= self.lowest and other <= self.highest
