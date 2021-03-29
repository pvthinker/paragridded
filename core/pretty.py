from colored import fore, style

# https://github.com/dslackw/colored
highlight = fore.DARK_BLUE+style.BOLD
reset = style.RESET

ma = fore.DARK_GREEN+style.BOLD
gr = fore.PURPLE_4B+style.BOLD
md = fore.DARK_RED_2+style.BOLD
va = fore.DARK_CYAN+style.BOLD

def BB(string):
    """ Highlight `string` by making it Blue and Bold"""
    return highlight+string+reset

def MA(string):
    """ Color `string` for Marray"""
    return ma+string+reset

def GR(string):
    """ Color `string` for Grid"""
    return gr+string+reset

def MD(string):
    """ Color `string` for MDataset"""
    return md+string+reset

def VA(string):
    """ Color `string` for Variable"""
    return va+string+reset

