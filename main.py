"""Leelansh Nikumbh"""

from test_mail import get_data,main_mail
from test_docs_api import write_to_docs
from gmail_sheet import write_in_sheet
from drive import main_drive


if __name__=="__main__":
    main_mail()
    data = get_data()      # returns the list of dictionaries (prints nothing)
    # print_data(data)       # prints it in the formatted way
    write_to_docs(data)
    write_in_sheet(data)
    main_drive()





