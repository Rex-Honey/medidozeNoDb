
def dictfetchall(cursor):
    '''
    Return all rows from a cursor as a dict
    Make sure that columns name should be different
    '''
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def setState(widget, state):
    widget.setProperty("ok", state == "ok")
    widget.setProperty("error", state == "err")
    widget.style().unpolish(widget)
    widget.style().polish(widget)